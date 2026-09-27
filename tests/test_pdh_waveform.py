"""Mouse-level regression tests for the PDH observation/draft canvas."""

import math
import unittest

from tests.qt_test_support import ensure_app
from PySide6.QtCore import QPoint, Qt
from PySide6.QtTest import QTest
from qt_pdh_waveform import PDHWaveformCanvas


PARAMS = dict(threshold_signal_scan=-2000, threshold_signal_lock=2000,
              time_scan=100, time_lock=300)


class PDHWaveformTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = ensure_app()

    def setUp(self):
        self.widget = PDHWaveformCanvas()
        self.widget.resize(800, 420)
        self.widget.show()
        self.widget.set_trace([0, 0.001, 0.002, 0.003], [5000.5, -8000.2, -3000.1, 5000.5],
                              source_label="文件回放 · 非实时")
        self.widget.set_parameters(PARAMS, clock_hz=1_000_000)
        self.edits, self.selections = [], []
        self.widget.parameter_changed.connect(lambda key, value: self.edits.append((key, value)))
        self.widget.selection_changed.connect(lambda start, end: self.selections.append((start, end)))
        self.app.processEvents()

    def tearDown(self):
        self.widget.close()
        self.widget.deleteLater()
        self.app.processEvents()

    def test_programmatic_updates_are_silent_and_accept_float_trace(self):
        self.widget.set_parameters(dict(PARAMS, time_scan=2**32 - 1), clock_hz=1e6)
        self.widget.set_selection(0.002, 0.001)
        self.assertEqual(self.widget.selection, (0.001, 0.002))
        self.assertEqual(self.widget._parameters["time_scan"], 2**32 - 1)
        self.assertEqual(self.edits, [])
        self.assertEqual(self.selections, [])

    def test_invalid_trace_is_rejected_without_losing_previous_trace(self):
        previous = self.widget._times, self.widget._values
        for times, values in (([0], [0]), ([0, 0], [1, 2]), ([0, 1], [0, math.nan]),
                              ([0, math.inf], [0, 1]), ([0, 1], [0, 32768]),
                              ([0, 1], [False, 1]), ([0, 1], [1])):
            with self.subTest(times=times, values=values), self.assertRaises(ValueError):
                self.widget.set_trace(times, values)
            self.assertEqual((self.widget._times, self.widget._values), previous)

    def test_threshold_drag_emits_integer_draft(self):
        for key in ("threshold_signal_scan", "threshold_signal_lock"):
            with self.subTest(key=key):
                start = self.widget.marker_position(key).toPoint()
                QTest.mousePress(self.widget, Qt.LeftButton, pos=start)
                QTest.mouseMove(self.widget, start + QPoint(0, -20))
                QTest.mouseRelease(self.widget, Qt.LeftButton, pos=start + QPoint(0, -20))
                self.assertEqual(self.edits[-1][0], key)
                self.assertIs(type(self.edits[-1][1]), int)
                self.assertGreater(self.edits[-1][1], PARAMS[key])

    def test_parent_echo_keeps_scale_frozen_until_release(self):
        def echo(key, value):
            self.widget.set_parameters({key: value}, clock_hz=1e6)
        self.widget.parameter_changed.connect(echo)
        start = self.widget.marker_position("threshold_signal_scan").toPoint()
        original_range = self.widget._y_range()
        QTest.mousePress(self.widget, Qt.LeftButton, pos=start)
        destination = QPoint(start.x(), 20)
        QTest.mouseMove(self.widget, destination)
        first_value = self.edits[-1][1]
        self.assertEqual(self.widget._y_range(), original_range)
        QTest.mouseMove(self.widget, destination)
        self.assertEqual(self.widget._parameters["threshold_signal_scan"], first_value)
        QTest.mouseRelease(self.widget, Qt.LeftButton, pos=destination)
        self.assertIsNone(self.widget._frozen_range)

    def test_duration_drag_uses_confirmed_clock_and_caps_new_values(self):
        self.widget.set_parameters(PARAMS, clock_hz=1e13)
        start = self.widget.marker_position("time_scan").toPoint()
        end = QPoint(int(self.widget._plot_rect().right()), start.y())
        QTest.mousePress(self.widget, Qt.LeftButton, pos=start)
        QTest.mouseMove(self.widget, end)
        QTest.mouseRelease(self.widget, Qt.LeftButton, pos=end)
        self.assertEqual(self.edits[-1], ("time_scan", 2**31 - 1))

    def test_unknown_clock_never_allows_duration_drag(self):
        for clock in (None, 0, -1, math.nan, math.inf, True):
            self.widget.set_parameters(PARAMS, clock_hz=clock)
            self.assertIsNone(self.widget.marker_position("time_scan"))
            self.assertIsNone(self.widget.marker_position("time_lock"))
        self.assertEqual(self.edits, [])

    def test_blank_plot_drag_selects_bounded_time_interval(self):
        rect = self.widget._plot_rect()
        start = QPoint(int(rect.left() + rect.width() * 0.2), int(rect.top() + 10))
        end = QPoint(int(rect.left() + rect.width() * 0.8), start.y())
        QTest.mousePress(self.widget, Qt.LeftButton, pos=start)
        QTest.mouseMove(self.widget, end)
        QTest.mouseRelease(self.widget, Qt.LeftButton, pos=end)
        self.assertTrue(self.selections)
        self.assertAlmostEqual(self.widget.selection[0], 0.0006, delta=0.00001)
        self.assertAlmostEqual(self.widget.selection[1], 0.0024, delta=0.00001)
        self.assertEqual(self.edits, [])

    def test_selection_clips_reorders_and_clears_zero_width(self):
        self.widget.set_selection(1, -1)
        self.assertEqual(self.widget.selection, (0, 0.003))
        self.widget.set_selection(0.001, 0.001)
        self.assertIsNone(self.widget.selection)

    def test_empty_trace_clears_selection_and_disables_markers(self):
        self.widget.set_selection(0, 0.001)
        self.widget.set_trace([], [], source_label="尚无数据")
        self.assertIsNone(self.widget.selection)
        self.assertIsNone(self.widget.marker_position("threshold_signal_scan"))
        self.assertEqual(self.widget._values, ())
        self.assertTrue(self.widget.grab().width() >= 520)

    def test_labels_preserve_source_and_do_not_claim_adc_or_hardware_state(self):
        self.assertIn("文件回放", self.widget.accessibleDescription())
        self.assertIn("内部信号码", self.widget.accessibleDescription())
        self.assertNotIn("ADC", self.widget.accessibleDescription())
        self.assertTrue(self.widget.grab().width() >= 520)

    def test_parameter_rejection_is_atomic(self):
        with self.assertRaises(ValueError):
            self.widget.set_parameters({"threshold_signal_scan": 123, "time_lock": 2**32})
        self.assertEqual(self.widget._parameters, PARAMS)


if __name__ == "__main__":
    unittest.main()
