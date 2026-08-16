import unittest

import numpy as np
from PySide6.QtGui import QImage
from PySide6.QtWidgets import QApplication, QToolButton

from tests.qt_test_support import ensure_app
from module import IIR
from qt_module import IIRDesignModel, IIRDesignerWidget, IIRResponseCanvas


class IIRDesignerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = ensure_app()

    @staticmethod
    def _default_specs(filter_type="butter"):
        return {
            "filter_type": filter_type,
            "freq_pass": 1_000_000.0,
            "freq_sample": 250_000_000.0,
        }

    def tearDown(self):
        for widget in QApplication.topLevelWidgets():
            if widget.objectName() == "iir_designer_window":
                widget.close()
        self.app.processEvents()

    def test_design_uses_existing_parallel_biquad_and_fpga_quantization(self):
        specs = self._default_specs()
        result = IIRDesignModel.design(specs)
        expected_b1, expected_a1, expected_b2, expected_a2 = IIR.get_IIR_parameters(
            "butter", specs["freq_pass"], specs["freq_sample"]
        )

        self.assertEqual(result["order"], 4)
        self.assertEqual(result["section_count"], 2)
        np.testing.assert_allclose(result["branch_b"][0], expected_b1)
        np.testing.assert_allclose(result["branch_b"][1], expected_b2)
        np.testing.assert_allclose(result["feedback_a"], (expected_a1[4::4], expected_a2[4::4]))
        self.assertEqual(len(result["coefficient_words_b"][0]), 9)
        self.assertEqual(len(result["coefficient_words_a"][0]), 2)
        self.assertLess(max(abs(value) for value in result["coefficient_words_b"][0]), 2**26)
        self.assertLess(max(abs(value) for value in result["coefficient_words_a"][0]), 2**26)
        self.assertAlmostEqual(result["magnitude_db"][0], 0.0, delta=0.2)
        self.assertTrue(result["stable"])
        self.assertLess(result["max_pole_radius"], 1.0)

    def test_all_existing_filter_families_generate_stable_preview(self):
        for filter_type in ("butter", "ellip", "cheby1", "cheby2", "bessel"):
            with self.subTest(filter_type=filter_type):
                result = IIRDesignModel.design(self._default_specs(filter_type))
                self.assertEqual(result["filter_type"], filter_type)
                self.assertTrue(result["stable"])
                self.assertGreater(result["stopband_attenuation_db"], 10.0)

    def test_invalid_cutoff_is_rejected(self):
        specs = self._default_specs()
        specs["freq_pass"] = specs["freq_sample"] / 2.0

        with self.assertRaisesRegex(ValueError, "Nyquist"):
            IIRDesignModel.design(specs)

    def test_live_preview_and_apply_keep_existing_special_method_contract(self):
        calls = []
        designer = IIRDesignerWidget(
            apply_callback=lambda method, args: calls.append((method, args)),
            initial_values={"design_lowpass": self._default_specs()},
        )
        before = designer.design_result()["max_pole_radius"]

        designer._editors["freq_pass"].setText("2MHz")
        self.app.processEvents()
        after = designer.design_result()["max_pole_radius"]

        self.assertNotEqual(before, after)
        designer._filter_type_combo.setCurrentIndex(
            designer._filter_type_combo.findData("ellip")
        )
        designer._apply_btn.click()
        self.app.processEvents()
        self.assertEqual(calls[0][0], "design_lowpass")
        self.assertEqual(calls[0][1]["filter_type"], "ellip")
        self.assertEqual(calls[0][1]["freq_pass"], 2_000_000.0)
        designer.close()

    def test_all_analysis_views_render_from_one_design(self):
        canvas = IIRResponseCanvas()
        canvas.set_design_result(IIRDesignModel.design(self._default_specs()))
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
        designer = IIRDesignerWidget(
            initial_values={"design_lowpass": self._default_specs()},
        )
        designer.show()
        self.app.processEvents()

        button = designer.findChild(QToolButton, "iir_designer_expand_button")
        self.assertIsNotNone(button)
        button.click()
        self.app.processEvents()
        button.click()
        self.app.processEvents()

        windows = [
            widget
            for widget in QApplication.topLevelWidgets()
            if widget.objectName() == "iir_designer_window"
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
