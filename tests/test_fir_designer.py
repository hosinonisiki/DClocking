import unittest

from PySide6.QtGui import QImage
from PySide6.QtWidgets import QApplication, QToolButton

from tests.qt_test_support import ensure_app
from qt_module import FIRDesignModel, FIRDesignerWidget, FIRResponseCanvas


class FIRDesignerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = ensure_app()

    @staticmethod
    def _default_specs():
        return {
            "freq_pass": 1_000_000.0,
            "freq_stop": 10_000_000.0,
            "freq_sample": 250_000_000.0,
            "weight": 1.0,
            "taps": 64,
        }

    def tearDown(self):
        for widget in QApplication.topLevelWidgets():
            if widget.objectName() == "fir_designer_window":
                widget.close()
        self.app.processEvents()

    def test_design_matches_fpga_remez_and_q23_constraints(self):
        result = FIRDesignModel.design(self._default_specs())

        self.assertEqual(result["taps"], 64)
        self.assertEqual(len(result["coefficients"]), 64)
        self.assertEqual(len(result["quantized_coefficients"]), 64)
        self.assertLessEqual(max(abs(value) for value in result["coefficients"]), 0.9800001)
        self.assertGreaterEqual(result["normalization"], 1.0)
        self.assertLessEqual(result["normalization"], 16.0)
        self.assertGreater(len(result["frequencies_hz"]), 200)
        self.assertAlmostEqual(result["magnitude_db"][0], 0.0, delta=0.2)
        self.assertGreater(result["stopband_attenuation_db"], 15.0)

    def test_invalid_frequency_edges_are_rejected(self):
        specs = self._default_specs()
        specs["freq_stop"] = specs["freq_sample"] / 2.0

        with self.assertRaisesRegex(ValueError, "Nyquist"):
            FIRDesignModel.design(specs)

    def test_live_preview_and_apply_keep_existing_special_method_contract(self):
        calls = []
        designer = FIRDesignerWidget(
            apply_callback=lambda method, args: calls.append((method, args)),
            initial_values={"design_lowpass": self._default_specs()},
        )
        before = designer.design_result()["transition_width_hz"]

        designer._editors["freq_pass"].setText("2MHz")
        self.app.processEvents()
        after = designer.design_result()["transition_width_hz"]

        self.assertNotEqual(before, after)
        designer._apply_btn.click()
        self.app.processEvents()
        self.assertEqual(calls[0][0], "design_lowpass")
        self.assertEqual(calls[0][1]["freq_pass"], 2_000_000.0)
        self.assertEqual(calls[0][1]["taps"], 64)
        designer.close()

    def test_all_analysis_views_render_from_one_design(self):
        canvas = FIRResponseCanvas()
        canvas.set_design_result(FIRDesignModel.design(self._default_specs()))
        canvas.resize(760, 420)

        rendered = []
        for view_mode in ("magnitude", "phase", "impulse", "zplane"):
            canvas.set_view_mode(view_mode)
            image = QImage(canvas.size(), QImage.Format_ARGB32)
            image.fill(0)
            canvas.render(image)
            rendered.append(image)

        self.assertTrue(all(not image.isNull() for image in rendered))

    def test_expand_button_opens_one_full_design_workbench(self):
        designer = FIRDesignerWidget(
            initial_values={"design_lowpass": self._default_specs()},
        )
        designer.show()
        self.app.processEvents()

        button = designer.findChild(QToolButton, "fir_designer_expand_button")
        self.assertIsNotNone(button)
        button.click()
        self.app.processEvents()
        button.click()
        self.app.processEvents()

        windows = [
            widget
            for widget in QApplication.topLevelWidgets()
            if widget.objectName() == "fir_designer_window"
        ]
        self.assertEqual(len(windows), 1)
        self.assertTrue(windows[0].isVisible())
        self.assertFalse(windows[0].isModal())
        self.assertGreater(windows[0].width(), designer.width())
        windows[0].close()
        self.app.processEvents()
        designer.close()


if __name__ == "__main__":
    unittest.main()
