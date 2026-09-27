"""PDH consumes one immutable acquisition, never the mixed display ring buffer."""

from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest

import numpy as np
from PySide6.QtCore import QSettings
from tests.qt_test_support import ensure_app
from oscilloscope_protocol import ScopeCapabilities
from oscilloscope_transport import ScopeReceiverStats
from qt_oscilloscope_workbench import OscilloscopeWorkbench


class _Receiver:
    is_running = True

    def __init__(self, capabilities):
        self.last_capabilities = capabilities
        self.stats = ScopeReceiverStats()
        self.pending = []

    def discard_queued_samples(self):
        self.pending = []

    def send_capture_request(self, *_args):
        pass

    def drain(self, **_kwargs):
        result, self.pending = self.pending, []
        return result

    def feed(self, values):
        values = np.asarray(values, dtype=np.float32)
        self.pending.append(SimpleNamespace(samples=values))
        self.stats.received_sample_count += values.size

    def stop(self):
        self.is_running = False


class ScopePDHSnapshotTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = ensure_app()

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.scope = OscilloscopeWorkbench(settings=QSettings(
            str(Path(self.temp.name) / "scope.ini"), QSettings.IniFormat))
        self.scope._render_timer.stop()
        self.caps = ScopeCapabilities("00:0A:35:01:FE:C0", "192.168.0.2",
                                      True, 16, 2, 1, 1_000_000, 262144)

    def tearDown(self):
        self.scope.stop_acquisition()
        self.scope.close()
        self.scope.deleteLater()
        self.app.processEvents()
        self.temp.cleanup()

    def _arm_udp(self, count=512, caps=True):
        self.scope.source_combo.setCurrentText("FPGA UDP")
        self.scope.capture_samples_spin.setValue(count)
        self.scope.acquisition_mode_combo.setCurrentText("连续")
        receiver = _Receiver(self.caps if caps else None)
        self.scope._receiver = receiver
        self.scope._is_running = True
        self.scope._validate_reported_capabilities(receiver.last_capabilities)
        self.scope._send_capture_request(receiver)
        self.scope._capture_request_sent = True
        return receiver

    def test_no_snapshot_from_empty_or_unattributed_ring_buffer(self):
        self.assertIsNone(self.scope.pdh_snapshot())
        self.scope.sample_buffer.append_channel(0, [10, 20, 30])
        self.assertIsNone(self.scope.pdh_snapshot())

    def test_udp_does_not_mix_previous_capture_with_current_partial_capture(self):
        receiver = self._arm_udp()
        self.scope.sample_buffer.append_channel(0, np.full(19000, 9999))
        receiver.feed(np.full(256, 7))
        self.scope._refresh_display()
        self.assertIsNone(self.scope.pdh_snapshot())
        receiver.feed(np.full(256, 8))
        self.scope._refresh_display()
        snap = self.scope.pdh_snapshot()
        self.assertEqual(len(snap["values"]), 512)
        self.assertEqual(snap["values"][:256], [7.] * 256)
        self.assertEqual(snap["values"][256:], [8.] * 256)
        self.assertEqual(snap["source"], "live")
        self.assertIn("无包序号", snap["label"])
        self.assertAlmostEqual(snap["time_s"][-1], 511 / 1e6)
        # The next acquisition has already started. The immutable result remains.
        self.assertEqual(self.scope._capture_received, 0)
        receiver.feed(np.full(256, 9))
        self.scope._refresh_display()
        self.assertEqual(self.scope.pdh_snapshot(), snap)

    def test_snapshot_is_detached_and_rate_is_pinned_not_plot_rate(self):
        receiver = self._arm_udp()
        receiver.feed(np.arange(512))
        self.scope._refresh_display()
        expected = self.scope.pdh_snapshot()
        changed = self.scope.pdh_snapshot()
        changed["values"][0], changed["time_s"][1] = -999, 999
        self.scope.plot.sample_rate_hz = 123
        self.scope.sample_buffer.append_channel(0, [-1, -2])
        self.assertEqual(self.scope.pdh_snapshot(), expected)

    def test_source_switch_start_and_clear_invalidate_snapshots(self):
        self.scope._generate_simulation_block()
        self.assertIsNotNone(self.scope.pdh_snapshot())
        self.scope.clear_button.click()
        self.assertIsNone(self.scope.pdh_snapshot())
        self.scope._generate_simulation_block()
        self.scope.source_combo.setCurrentText("FPGA UDP")
        self.assertIsNone(self.scope.pdh_snapshot())
        self.scope.source_combo.setCurrentText("内置仿真")
        self.scope._generate_simulation_block()
        self.scope.start_acquisition()
        self.scope._simulation_timer.stop()
        self.assertIsNone(self.scope.pdh_snapshot())

    def test_unknown_or_changed_capabilities_cannot_generate_live_snapshot(self):
        receiver = self._arm_udp(caps=False)
        receiver.feed(np.ones(512))
        self.scope._refresh_display()
        self.assertIsNone(self.scope.pdh_snapshot())
        self.scope.stop_acquisition()
        receiver = self._arm_udp()
        receiver.last_capabilities = replace(self.caps, sample_rate_hz=2_000_000)
        receiver.feed(np.ones(512))
        self.scope._refresh_display()
        self.assertIsNone(self.scope.pdh_snapshot())

    def test_completed_long_capture_is_bounded_without_stitching(self):
        receiver = self._arm_udp(32768)
        receiver.feed(np.full(32768, 13))
        self.scope._refresh_display()
        snap = self.scope.pdh_snapshot()
        self.assertEqual(len(snap["values"]), 20000)
        self.assertEqual(snap["values"], [13.] * 20000)
        self.assertEqual(snap["time_s"][0], 0.)
        self.assertAlmostEqual(snap["time_s"][-1], 19999 / 1e6)

    def test_transient_rate_change_invalidates_entire_current_capture(self):
        receiver = self._arm_udp()
        receiver.last_capabilities = replace(self.caps, sample_rate_hz=2_000_000)
        receiver.feed(np.ones(256))
        self.scope._refresh_display()
        receiver.last_capabilities = self.caps
        receiver.feed(np.ones(256))
        self.scope._refresh_display()
        self.assertIsNone(self.scope.pdh_snapshot())

    def test_simulation_block_has_fixed_demo_provenance_and_survives_stop(self):
        self.scope.plot.sample_rate_hz = 3
        self.scope._generate_simulation_block()
        snap = self.scope.pdh_snapshot()
        self.assertEqual(snap["source"], "demo")
        self.assertEqual(len(snap["values"]), 2048)
        self.assertAlmostEqual(snap["time_s"][-1], 2047 / 32e6)
        self.scope.stop_acquisition()
        self.assertEqual(self.scope.pdh_snapshot(), snap)

    def test_invalid_samples_or_known_drops_are_not_offered_for_pdh(self):
        receiver = self._arm_udp()
        receiver.feed(np.full(512, np.nan))
        self.scope._refresh_display()
        self.assertIsNone(self.scope.pdh_snapshot())
        receiver.feed(np.full(512, 100))
        receiver.stats.queue_dropped_packets = 1
        self.scope._refresh_display()
        self.assertIsNone(self.scope.pdh_snapshot())


if __name__ == "__main__":
    unittest.main()
