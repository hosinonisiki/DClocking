import math
import unittest

from PySide6.QtCore import QPoint, QPointF, Qt
from PySide6.QtGui import QImage
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QSlider, QToolButton

from tests.qt_test_support import ensure_app
import module as hw_module
from qt_module import ModulePID, PIDParamCanvas, ParamDialog
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

    def test_manual_tuning_sliders_update_editor_curve_and_apply_callback(self):
        schema = [field for field in PID_SCHEMA if field.get("mode") == "indirect"]
        applied = []
        dialog = ParamDialog(
            schema,
            {
                "overall_gain": 0.0,
                "pi_corner": 100.0,
                "pd_corner": 10_000.0,
                "saturation_gain": 20.0,
                "saturation_turning_frequency": 10.0,
            },
            apply_callback=applied.append,
            companion_widget_factory=lambda parent: PIDParamCanvas(parent),
        )
        dialog.show()
        self.app.processEvents()

        tuning_panel = getattr(dialog, "_pid_tuning_panel", None)
        self.assertIsNotNone(tuning_panel)
        sliders = {
            key: tuning_panel.findChild(QSlider, f"pid_tune_{key}")
            for key in (
                "overall_gain",
                "pi_corner",
                "pd_corner",
                "saturation_gain",
                "saturation_turning_frequency",
            )
        }
        self.assertTrue(all(sliders.values()))
        self.assertEqual(sliders["overall_gain"].accessibleName(), "滑动调节 P 整体增益")

        gain_slider = sliders["overall_gain"]
        gain_slider.setValue(gain_slider.value() + 80)
        self.app.processEvents()

        editor_value = dialog._editors["overall_gain"][1].preview_quantity_value()
        self.assertGreater(editor_value, 0.0)
        self.assertAlmostEqual(
            dialog._companion_widget.response_data()["overall_gain_db"],
            editor_value,
        )
        self.assertEqual(applied[-1], {"overall_gain": editor_value})
        dialog.close()

    def test_pid_special_values_follow_schema_write_whitelist(self):
        schema = [field for field in PID_SCHEMA if field.get("mode") == "indirect"]
        applied = []
        dialog = ParamDialog(
            schema,
            {
                "overall_gain": 0.0,
                "pi_corner": 100.0,
                "pd_corner": 10_000.0,
                "saturation_gain": 20.0,
                "saturation_turning_frequency": 10.0,
            },
            apply_callback=applied.append,
            companion_widget_factory=lambda parent: PIDParamCanvas(parent),
        )

        allowed = (
            ("overall_gain", "-infdB", float("-inf")),
            ("pd_corner", "+infHz", float("inf")),
            ("saturation_gain", "∞dB", float("inf")),
        )
        for key, text, expected in allowed:
            editor = dialog._editors[key][1]
            editor.setText(text)
            editor._sync_core_from_widget()
            QTest.keyClick(editor, Qt.Key_Return)
            self.app.processEvents()
            self.assertEqual(applied[-1][key], expected)

        rejected = (
            ("overall_gain", "infdB"),
            ("pi_corner", "infHz"),
            ("pi_corner", "-infHz"),
            ("pd_corner", "-infHz"),
            ("saturation_gain", "-infdB"),
            ("saturation_turning_frequency", "infHz"),
        )
        for key, text in rejected:
            editor = dialog._editors[key][1]
            editor.setText(text)
            editor._sync_core_from_widget()
            with self.assertRaises(ValueError):
                dialog._value_from_editor(key)
        dialog.close()

    def test_pid_tuning_slider_has_real_infinity_endpoints(self):
        schema = [field for field in PID_SCHEMA if field.get("mode") == "indirect"]
        applied = []
        dialog = ParamDialog(
            schema,
            {
                "overall_gain": 0.0,
                "pi_corner": 100.0,
                "pd_corner": 10_000.0,
                "saturation_gain": 20.0,
                "saturation_turning_frequency": 10.0,
            },
            apply_callback=applied.append,
            companion_widget_factory=lambda parent: PIDParamCanvas(parent),
        )
        panel = dialog._pid_tuning_panel

        panel._sliders["overall_gain"].setValue(0)
        self.app.processEvents()
        self.assertEqual(applied[-1], {"overall_gain": float("-inf")})
        self.assertEqual(
            dialog._editors["overall_gain"][1].preview_quantity_value(),
            float("-inf"),
        )

        panel._sliders["pd_corner"].setValue(panel._sliders["pd_corner"].maximum())
        self.app.processEvents()
        self.assertEqual(applied[-1], {"pd_corner": float("inf")})
        self.assertEqual(
            dialog._editors["pd_corner"][1].preview_quantity_value(),
            float("inf"),
        )

        saturation_slider = panel._sliders["saturation_gain"]
        saturation_slider.setValue(saturation_slider.maximum())
        self.app.processEvents()
        self.assertEqual(applied[-1], {"saturation_gain": float("inf")})
        self.assertEqual(
            dialog._editors["saturation_gain"][1].preview_quantity_value(),
            float("inf"),
        )
        dialog.close()

    def test_pid_tuning_slider_ranges_match_hardware_limits(self):
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
        panel = dialog._pid_tuning_panel

        self.assertEqual(
            panel._position_to_value("overall_gain", panel._sliders["overall_gain"].maximum()),
            40.0,
        )
        self.assertEqual(
            panel._position_to_value("pi_corner", panel._sliders["pi_corner"].maximum()),
            1_000_000.0,
        )
        self.assertEqual(panel._position_to_value("pd_corner", 0), 10_000.0)
        self.assertEqual(
            panel._position_to_value("pd_corner", panel._sliders["pd_corner"].maximum()),
            float("inf"),
        )
        saturation_slider = panel._sliders["saturation_gain"]
        self.assertEqual(
            panel._position_to_value("saturation_gain", saturation_slider.maximum() - 1),
            80.0,
        )
        self.assertEqual(
            panel._position_to_value("saturation_gain", saturation_slider.maximum()),
            float("inf"),
        )
        self.assertAlmostEqual(
            panel._position_to_value(
                "saturation_turning_frequency",
                panel._sliders["saturation_turning_frequency"].maximum(),
            ),
            125_000_000.0 / (256.0 * 2.0 * math.pi),
        )

        gain_i = next(field for field in PID_SCHEMA if field["key"] == "gain_i")
        self.assertEqual(gain_i["min"], -(2**31))
        self.assertEqual(gain_i["max"], 2**31 - 1)
        dialog.close()

    def test_pid_node_rejects_special_values_that_bypass_the_editor(self):
        node = ModulePID("PID控制器", 0, QPointF(0, 0))
        for params in (
            {"overall_gain": float("inf")},
            {"pi_corner": float("inf")},
            {"pi_corner": float("-inf")},
            {"pd_corner": float("-inf")},
            {"saturation_gain": float("-inf")},
            {"saturation_turning_frequency": float("inf")},
            {"overall_gain": float("nan")},
        ):
            with self.assertRaises(ValueError):
                node.set_params(params)

    def test_hardware_pid_special_value_contract(self):
        class StubBus:
            def __init__(self, gain_p):
                self.gain_p = gain_p

            def read(self, _name, address):
                value = self.gain_p if address == 0 else 0
                return int(value).to_bytes(4, "big", signed=True)

        pid = hw_module.ModulePID(StubBus(gain_p=2**16), "PIDC")
        self.assertEqual(
            pid.overall_gain_func(float("-inf")),
            [(0, 0), (1, 0), (2, 0)],
        )
        self.assertEqual(pid.pd_corner_func(float("inf")), [(2, 0)])
        self.assertEqual(pid.saturation_gain_func(float("inf")), [(6, 0)])

        pi_pairs = pid.pi_corner_func(1_000_000.0)
        self.assertGreater(pi_pairs[0][1], 2**23 - 1)
        self.assertLessEqual(pi_pairs[0][1], 2**31 - 1)
        with self.assertRaisesRegex(ValueError, "gain_i is out of range"):
            pid.pi_corner_func(100_000_000.0)

        pid_with_zero_p = hw_module.ModulePID(StubBus(gain_p=0), "PIDC")
        with self.assertRaisesRegex(ValueError, "gain_p is zero"):
            pid_with_zero_p.pd_corner_func(float("inf"))

        _addresses, saturation_formula = pid.saturation_gain_func()
        self.assertEqual(
            saturation_formula(((1).to_bytes(4, "big"), (0).to_bytes(4, "big"))),
            float("inf"),
        )

    def test_plot_markers_drag_to_apply_frequency_and_gain_parameters(self):
        schema = [field for field in PID_SCHEMA if field.get("mode") == "indirect"]
        applied = []
        dialog = ParamDialog(
            schema,
            {
                "overall_gain": 0.0,
                "pi_corner": 100.0,
                "pd_corner": 10_000.0,
                "saturation_gain": 20.0,
                "saturation_turning_frequency": 10.0,
            },
            apply_callback=applied.append,
            companion_widget_factory=lambda parent: PIDParamCanvas(parent),
        )
        dialog.show()
        canvas = dialog._companion_widget
        canvas.resize(620, 230)
        self._render(canvas)
        self.app.processEvents()

        handles = canvas.interactive_handle_positions()
        self.assertEqual(
            set(handles),
            {
                "overall_gain",
                "pi_corner",
                "pd_corner",
                "saturation_turning_frequency",
            },
        )

        pi_handle = handles["pi_corner"].toPoint()
        QTest.mousePress(canvas, Qt.LeftButton, pos=pi_handle)
        QTest.mouseMove(canvas, QPoint(pi_handle.x() + 35, pi_handle.y()))
        QTest.mouseRelease(
            canvas,
            Qt.LeftButton,
            pos=QPoint(pi_handle.x() + 35, pi_handle.y()),
        )
        self.app.processEvents()
        pi_value = dialog._editors["pi_corner"][1].preview_quantity_value()
        self.assertGreater(pi_value, 100.0)
        self.assertEqual(applied[-1], {"pi_corner": pi_value})

        self._render(canvas)
        gain_handle = canvas.interactive_handle_positions()["overall_gain"].toPoint()
        QTest.mousePress(canvas, Qt.LeftButton, pos=gain_handle)
        QTest.mouseMove(canvas, QPoint(gain_handle.x(), gain_handle.y() - 18))
        QTest.mouseRelease(
            canvas,
            Qt.LeftButton,
            pos=QPoint(gain_handle.x(), gain_handle.y() - 18),
        )
        self.app.processEvents()
        gain_value = dialog._editors["overall_gain"][1].preview_quantity_value()
        self.assertGreater(gain_value, 0.0)
        self.assertEqual(applied[-1], {"overall_gain": gain_value})
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
