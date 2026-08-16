import math
import unittest

from PySide6.QtGui import QImage
from PySide6.QtWidgets import QApplication, QToolButton

from tests.qt_test_support import ensure_app
from qt_module import PIDParamCanvas, ParamDialog
from qt_module_schema import PID_SCHEMA


class PIDParamCanvasTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = ensure_app()

    def _calculate(self, parameters, frequencies_hz):
        calculator = getattr(PIDParamCanvas, "calculate_response", None)
        response = calculator(parameters, frequencies_hz) if callable(calculator) else None
        self.assertIsInstance(response, dict)
        return response

    def tearDown(self):
        for widget in QApplication.topLevelWidgets():
            if widget.objectName() == "pid_response_window":
                widget.close()
        self.app.processEvents()

    @staticmethod
    def _render(widget):
        widget.resize(620, 230)
        image = QImage(widget.size(), QImage.Format_ARGB32)
        image.fill(0)
        widget.render(image)
        return image

    def test_response_uses_pid_corner_and_integrator_leak_equations(self):
        response = self._calculate(
            {
                "overall_gain": 0.0,
                "pi_corner": 100.0,
                "pd_corner": 10_000.0,
                "saturation_turning_frequency": 10.0,
            },
            (10.0, 100.0, 10_000.0),
        )

        self.assertEqual(response["proportional_db"], (0.0, 0.0, 0.0))
        self.assertAlmostEqual(
            response["integral_db"][0],
            20.0 * math.log10(100.0 / math.sqrt(10.0**2 + 10.0**2)),
            places=6,
        )
        self.assertAlmostEqual(
            response["integral_db"][1],
            20.0 * math.log10(100.0 / math.sqrt(100.0**2 + 10.0**2)),
            places=6,
        )
        self.assertAlmostEqual(response["derivative_db"][2], 0.0, places=6)
        self.assertAlmostEqual(response["saturation_gain_db"], 20.0, places=6)

    def test_total_response_combines_i_and_d_as_complex_channels(self):
        response = self._calculate(
            {
                "overall_gain": 0.0,
                "pi_corner": 100.0,
                "pd_corner": 10_000.0,
                "saturation_turning_frequency": 0.0,
            },
            (1_000.0,),
        )

        # At sqrt(PI_corner * PD_corner), ideal I and D imaginary terms cancel.
        self.assertAlmostEqual(response["total_db"][0], 0.0, places=6)

    def test_direct_register_values_use_fpga_clock_and_fixed_point_scaling(self):
        expected_pi_corner = 125_000_000.0 / (2.0 * math.pi * (2.0**16))
        expected_pd_corner = 250_000_000.0 / (2.0 * math.pi)
        response = PIDParamCanvas.calculate_response(
            {
                "gain_p": 2**16,
                "gain_i": 2**16,
                "gain_d": 2**16,
                "leak_digit": 256,
            },
            (expected_pi_corner,),
            changed_key="gain_p",
        )

        self.assertEqual(response["source"], "direct")
        self.assertAlmostEqual(response["overall_gain_db"], 0.0, places=6)
        self.assertAlmostEqual(response["pi_corner_hz"], expected_pi_corner, places=6)
        self.assertAlmostEqual(response["pd_corner_hz"], expected_pd_corner, places=6)
        self.assertAlmostEqual(response["leak_frequency_hz"], expected_pi_corner, places=6)
        self.assertAlmostEqual(response["saturation_gain_db"], 0.0, places=6)

    def test_parameter_text_change_repaints_curve_immediately(self):
        schema = [field for field in PID_SCHEMA if field.get("mode") == "indirect"]
        dialog = ParamDialog(
            schema,
            {
                "overall_gain": 0.0,
                "pi_corner": 100.0,
                "pd_corner": 10_000.0,
                "saturation_gain": 20.0,
                "saturation_turning_frequency": 10.0,
            },
            companion_widget_factory=lambda parent: PIDParamCanvas(parent),
        )
        canvas = dialog._companion_widget
        before = self._render(canvas)

        gain_editor = dialog._editors["overall_gain"][1]
        gain_editor.setText("20dB")
        self.app.processEvents()
        after = self._render(canvas)

        self.assertNotEqual(before, after)
        dialog.close()

    def test_expand_button_opens_one_resizable_standalone_window(self):
        schema = [field for field in PID_SCHEMA if field.get("mode") == "indirect"]
        dialog = ParamDialog(
            schema,
            {
                "overall_gain": 0.0,
                "pi_corner": 100.0,
                "pd_corner": 10_000.0,
                "saturation_gain": 20.0,
                "saturation_turning_frequency": 10.0,
            },
            companion_widget_factory=lambda parent: PIDParamCanvas(parent),
        )
        dialog.show()
        self.app.processEvents()

        button = dialog.findChild(QToolButton, "pid_response_expand_button")
        self.assertIsNotNone(button)
        self.assertEqual(button.accessibleName(), "放大 PID 实时曲线")
        button.click()
        self.app.processEvents()

        windows = [
            widget
            for widget in QApplication.topLevelWidgets()
            if widget.objectName() == "pid_response_window"
        ]
        self.assertEqual(len(windows), 1)
        window = windows[0]
        self.assertTrue(window.isVisible())
        self.assertFalse(window.isModal())
        self.assertGreater(window.width(), dialog._companion_widget.width())
        self.assertGreater(window.height(), dialog._companion_widget.height())

        button.click()
        self.app.processEvents()
        windows = [
            widget
            for widget in QApplication.topLevelWidgets()
            if widget.objectName() == "pid_response_window"
        ]
        self.assertEqual(len(windows), 1)
        dialog.close()

    def test_expanded_curve_tracks_parameter_edits(self):
        schema = [field for field in PID_SCHEMA if field.get("mode") == "indirect"]
        dialog = ParamDialog(
            schema,
            {
                "overall_gain": 0.0,
                "pi_corner": 100.0,
                "pd_corner": 10_000.0,
                "saturation_gain": 20.0,
                "saturation_turning_frequency": 10.0,
            },
            companion_widget_factory=lambda parent: PIDParamCanvas(parent),
        )
        dialog.show()
        self.app.processEvents()

        button = dialog.findChild(QToolButton, "pid_response_expand_button")
        self.assertIsNotNone(button)
        button.click()
        self.app.processEvents()
        window = next(
            widget
            for widget in QApplication.topLevelWidgets()
            if widget.objectName() == "pid_response_window"
        )
        expanded_canvas = window.findChild(PIDParamCanvas, "pid_response_expanded_canvas")
        self.assertIsNotNone(expanded_canvas)

        gain_editor = dialog._editors["overall_gain"][1]
        gain_editor.setText("20dB")
        self.app.processEvents()

        self.assertAlmostEqual(expanded_canvas.response_data()["overall_gain_db"], 20.0)
        dialog.close()


if __name__ == "__main__":
    unittest.main()
