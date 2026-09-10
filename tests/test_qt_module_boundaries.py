import unittest

import qt_filter_designer
import qt_module
import qt_pid_tuning
import qt_quantity_edit


class QtModuleBoundaryTests(unittest.TestCase):
    def test_legacy_qt_module_exports_point_to_split_modules(self):
        self.assertIs(qt_module.QuantityLineEdit, qt_quantity_edit.QuantityLineEdit)
        for name in (
            "FIRDesignModel",
            "FIRResponseCanvas",
            "FIRDesignerWidget",
            "FIRDesignerWindow",
            "IIRDesignModel",
            "IIRResponseCanvas",
            "IIRDesignerWidget",
            "IIRDesignerWindow",
        ):
            with self.subTest(name=name):
                self.assertIs(getattr(qt_module, name), getattr(qt_filter_designer, name))

        for name in (
            "PIDParamCanvas",
            "PIDSliderSpec",
            "PIDManualTuningPanel",
            "PIDResponseWindow",
        ):
            with self.subTest(name=name):
                self.assertIs(getattr(qt_module, name), getattr(qt_pid_tuning, name))


if __name__ == "__main__":
    unittest.main()
