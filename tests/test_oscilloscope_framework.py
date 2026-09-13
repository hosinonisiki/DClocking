import socket
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np
from PySide6.QtCore import QSettings
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QWidget

from tests.qt_test_support import ensure_app
from oscilloscope_model import ScopeSampleBuffer
from oscilloscope_protocol import (
    LegacyCaptureAssembler,
    LegacyUdpScopeProtocol,
    ScopeCapabilities,
    ScopeProtocolError,
)
from oscilloscope_transport import (
    ScopeEndpointConfig,
    ScopeReceiverStats,
    UdpScopeReceiver,
)
from qt_oscilloscope_workbench import OscilloscopeWorkbench, ScopePlotWidget
from qt_ui_mainwindow import MainWindow


class LegacyScopeProtocolTests(unittest.TestCase):
    def setUp(self):
        self.protocol = LegacyUdpScopeProtocol()

    def test_capture_request_matches_current_rtl_byte_contract(self):
        request = self.protocol.build_capture_request(
            fpga_mac="00:0A:35:01:FE:C0",
            channel_mask=0x00000001,
            sample_count=4096,
            header=0x20,
        )

        self.assertEqual(len(request), 19)
        self.assertEqual(request[0], 0x20)
        self.assertEqual(request[1:5], b"\x00\x01\x00\x02")
        self.assertEqual(request[5:11], bytes.fromhex("000A3501FEC0"))
        self.assertEqual(request[11:15], b"\x00\x00\x00\x01")
        self.assertEqual(request[15:19], b"\x00\x00\x10\x00")

    def test_capture_request_rejects_values_current_rtl_cannot_represent(self):
        with self.assertRaisesRegex(ScopeProtocolError, "512"):
            self.protocol.build_capture_request(
                fpga_mac="00:0A:35:01:FE:C0",
                channel_mask=1,
                sample_count=513,
            )
        with self.assertRaisesRegex(ScopeProtocolError, "通道"):
            self.protocol.build_capture_request(
                fpga_mac="00:0A:35:01:FE:C0",
                channel_mask=0,
                sample_count=512,
            )

    def test_inquiry_reply_decodes_capabilities(self):
        payload = (
            b"\x01\x00\x01\x00\x01"
            + bytes.fromhex("000A3501FEC0")
            + bytes([192, 168, 0, 2])
            + b"\x01\x10\x02\x01"
            + (32_000_000).to_bytes(4, "big")
            + (0x40000).to_bytes(4, "big")
        )

        capabilities = self.protocol.parse_inquiry_reply(payload)

        self.assertEqual(capabilities.fpga_ip, "192.168.0.2")
        self.assertEqual(capabilities.fpga_mac, "00:0A:35:01:FE:C0")
        self.assertEqual(capabilities.sample_rate_hz, 32_000_000)
        self.assertEqual(capabilities.sample_depth, 0x40000)
        self.assertTrue(capabilities.signed)
        self.assertEqual(capabilities.sample_bits, 16)
        self.assertEqual(capabilities.channel_count, 1)

    def test_data_packet_decodes_signed_big_endian_samples(self):
        expected = np.resize(
            np.array([-32768, -1, 0, 32767], dtype=np.int16), 512
        )
        payload = b"\x01\x00\x01\x00\x02" + expected.astype(">i2").tobytes()

        packet = self.protocol.parse_data_packet(payload)

        np.testing.assert_array_equal(packet.samples, expected)
        self.assertFalse(packet.sequence_available)
        self.assertEqual(packet.channel_count, 1)

    def test_data_packet_rejects_wrong_command_and_odd_sample_bytes(self):
        with self.assertRaises(ScopeProtocolError):
            self.protocol.parse_data_packet(b"\x01\x00\x01\x00\x01\x00\x00")
        with self.assertRaises(ScopeProtocolError):
            self.protocol.parse_data_packet(b"\x01\x00\x01\x00\x02\x00")

    def test_legacy_assembler_trims_final_packet_without_inventing_loss_stats(self):
        assembler = LegacyCaptureAssembler(expected_samples=600)
        first = np.arange(512, dtype=np.int16)
        second = np.arange(512, 1024, dtype=np.int16)

        assembler.append(first)
        assembler.append(second)

        self.assertTrue(assembler.complete)
        self.assertEqual(assembler.packet_count, 2)
        self.assertFalse(assembler.packet_loss_observable)
        np.testing.assert_array_equal(
            assembler.samples(), np.arange(600, dtype=np.int16)
        )


class ScopeSampleBufferTests(unittest.TestCase):
    def test_ring_buffer_keeps_latest_samples_for_all_channels(self):
        buffer = ScopeSampleBuffer(channel_count=2, capacity=5)
        buffer.append(np.array([[0, 1, 2], [10, 11, 12]], dtype=np.float32))
        buffer.append(np.array([[3, 4, 5, 6], [13, 14, 15, 16]], dtype=np.float32))

        snapshot = buffer.snapshot()

        np.testing.assert_array_equal(snapshot[0], [2, 3, 4, 5, 6])
        np.testing.assert_array_equal(snapshot[1], [12, 13, 14, 15, 16])

    def test_envelope_preserves_minimum_and_maximum_peaks(self):
        buffer = ScopeSampleBuffer(channel_count=1, capacity=32)
        values = np.array([[0, 1, 8, -7, 2, 3, 4, 5]], dtype=np.float32)
        buffer.append(values)

        x, low, high = buffer.min_max_envelope(max_columns=4)

        self.assertLessEqual(x.size, 4)
        self.assertEqual(float(low.min()), -7.0)
        self.assertEqual(float(high.max()), 8.0)


class UdpScopeReceiverTests(unittest.TestCase):
    def test_loopback_receiver_parses_datagram_and_stops_cleanly(self):
        protocol = LegacyUdpScopeProtocol()
        receiver = UdpScopeReceiver(
            ScopeEndpointConfig(local_ip="127.0.0.1", local_port=0),
            protocol=protocol,
        )
        sender = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            receiver.start()
            self.assertTrue(receiver.wait_until_ready(1.0))
            endpoint = receiver.bound_endpoint
            self.assertIsNotNone(endpoint)
            expected = np.resize(np.array([1, -2, 3], dtype=np.int16), 512)
            payload = b"\x01\x00\x01\x00\x02" + expected.astype(">i2").tobytes()
            sender.sendto(payload, endpoint)

            deadline = time.monotonic() + 1.0
            packets = []
            while time.monotonic() < deadline and not packets:
                packets = receiver.drain()
                time.sleep(0.01)

            self.assertEqual(len(packets), 1)
            np.testing.assert_array_equal(packets[0].samples, expected)
            self.assertEqual(receiver.stats.received_datagrams, 1)
            self.assertEqual(receiver.stats.malformed_datagrams, 0)
        finally:
            sender.close()
            receiver.stop()
        self.assertFalse(receiver.is_running)

    def test_malformed_packet_is_counted_without_killing_receiver(self):
        receiver = UdpScopeReceiver(
            ScopeEndpointConfig(local_ip="127.0.0.1", local_port=0),
            protocol=LegacyUdpScopeProtocol(),
        )
        sender = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            receiver.start()
            self.assertTrue(receiver.wait_until_ready(1.0))
            sender.sendto(b"bad", receiver.bound_endpoint)
            deadline = time.monotonic() + 1.0
            while (
                time.monotonic() < deadline
                and receiver.stats.malformed_datagrams == 0
            ):
                time.sleep(0.01)
            self.assertEqual(receiver.stats.malformed_datagrams, 1)
            self.assertTrue(receiver.is_running)
        finally:
            sender.close()
            receiver.stop()

    def test_unexpected_source_ip_is_dropped_before_protocol_parsing(self):
        receiver = UdpScopeReceiver(
            ScopeEndpointConfig(
                local_ip="127.0.0.1",
                local_port=0,
                allowed_remote_ip="127.0.0.2",
            ),
            protocol=LegacyUdpScopeProtocol(),
        )
        sender = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            receiver.start()
            sender.sendto(b"bad", receiver.bound_endpoint)
            deadline = time.monotonic() + 1.0
            while (
                time.monotonic() < deadline
                and receiver.stats.foreign_datagrams == 0
            ):
                time.sleep(0.01)
            self.assertEqual(receiver.stats.foreign_datagrams, 1)
            self.assertEqual(receiver.stats.malformed_datagrams, 0)
        finally:
            sender.close()
            receiver.stop()

    def test_receiver_rejects_unexpected_length_before_protocol_parser(self):
        protocol = LegacyUdpScopeProtocol()
        receiver = UdpScopeReceiver(
            ScopeEndpointConfig(local_ip="127.0.0.1", local_port=0),
            protocol=protocol,
        )
        sender = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            receiver.start()
            # Larger than the old 2 KiB receive buffer: Winsock used to raise
            # WSAEMSGSIZE and terminate the worker instead of counting a bad packet.
            sender.sendto(b"\x01\x00\x01\x00\x02" + b"x" * 3000, receiver.bound_endpoint)
            deadline = time.monotonic() + 1.0
            while time.monotonic() < deadline and not receiver.stats.malformed_datagrams:
                time.sleep(0.01)
            self.assertEqual(receiver.stats.malformed_datagrams, 1)
            self.assertIn("长度", receiver.stats.last_error)
            self.assertTrue(receiver.is_running)
        finally:
            sender.close()
            receiver.stop()

    def test_endpoint_config_caps_memory_and_queue_settings(self):
        with self.assertRaises(ValueError):
            ScopeEndpointConfig(receive_buffer_bytes=128 * 1024 * 1024)
        with self.assertRaises(ValueError):
            ScopeEndpointConfig(queue_packets=100_000)
        with self.assertRaises(ValueError):
            ScopeEndpointConfig(socket_timeout_seconds=60)

    def test_stop_timeout_retains_generation_and_blocks_unsafe_restart(self):
        class StuckThread:
            alive = True

            def is_alive(self):
                return self.alive

            def join(self, _timeout):
                pass

        class FakeSocket:
            def close(self):
                pass

        receiver = UdpScopeReceiver(
            ScopeEndpointConfig(local_ip="127.0.0.1", local_port=0)
        )
        thread = StuckThread()
        receiver._thread = thread
        receiver._socket = FakeSocket()
        receiver._stop_event = threading.Event()

        receiver.stop(timeout=0)

        self.assertIs(receiver._thread, thread)
        with self.assertRaisesRegex(RuntimeError, "仍在停止"):
            receiver.start()
        thread.alive = False
        receiver.stop(timeout=0)
        self.assertIsNone(receiver._thread)


class OscilloscopeWorkbenchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = ensure_app()

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.settings = QSettings(
            f"{self.temp_dir.name}/scope.ini", QSettings.IniFormat
        )
        self.workbench = OscilloscopeWorkbench(settings=self.settings)
        self.workbench.resize(1280, 760)
        self.workbench.show()
        self.app.processEvents()

    def tearDown(self):
        self.workbench.shutdown()
        self.workbench.close()
        self.app.processEvents()
        self.temp_dir.cleanup()

    def test_simulator_updates_real_buffer_and_visible_metrics(self):
        self.workbench.source_combo.setCurrentText("内置仿真")
        self.workbench.start_button.click()
        QTest.qWait(180)
        self.app.processEvents()

        self.assertGreater(self.workbench.sample_buffer.size, 0)
        self.assertIn("仿真运行", self.workbench.connection_status_label.text())
        self.assertIsInstance(
            self.workbench.findChild(ScopePlotWidget, "oscilloscope_plot"),
            ScopePlotWidget,
        )

        self.workbench.stop_button.click()
        self.assertFalse(self.workbench.is_running)

    def test_hardware_draft_controls_are_explicitly_marked(self):
        self.assertIn("协议草案", self.workbench.protocol_badge.text())
        self.assertIn("待硬件确认", self.workbench.hardware_mapping_label.text())
        self.assertEqual(self.workbench.capture_samples_spin.singleStep(), 512)

    def test_visible_sample_selector_matches_plot_and_is_restored(self):
        self.assertEqual(
            self.workbench.plot.visible_samples,
            int(self.workbench.visible_samples_combo.currentData()),
        )
        self.workbench.visible_samples_combo.setCurrentIndex(3)
        self.workbench.shutdown()

        restored = OscilloscopeWorkbench(settings=self.settings)
        try:
            self.assertEqual(restored.plot.visible_samples, 65_536)
            self.assertEqual(restored.visible_samples_combo.currentData(), 65_536)
        finally:
            restored.shutdown()

    def test_legacy_udp_locks_port_and_exposes_only_ch1(self):
        self.workbench.source_combo.setCurrentText("FPGA UDP")
        self.app.processEvents()

        self.assertEqual(self.workbench.local_port_spin.value(), 8080)
        self.assertFalse(self.workbench.local_port_spin.isEnabled())
        self.assertTrue(self.workbench.channel_checks[0].isChecked())
        self.assertTrue(self.workbench.channel_checks[0].isEnabled())
        for check in self.workbench.channel_checks[1:]:
            self.assertFalse(check.isChecked())
            self.assertFalse(check.isEnabled())
        self.assertEqual(self.workbench._channel_mask(), 1)

    def test_idle_udp_status_is_not_reported_as_simulator(self):
        self.workbench.source_combo.setCurrentText("FPGA UDP")
        self.workbench._refresh_display()

        self.assertNotIn("SIM", self.workbench.packet_metric[1].text())

    def test_switching_back_to_simulation_restores_rate_status_and_channels(self):
        self.workbench.channel_checks[1].setChecked(False)
        self.workbench.source_combo.setCurrentText("FPGA UDP")
        self.workbench.plot.sample_rate_hz = 1_000_000
        self.workbench.sample_rate_metric[1].setText("1.00 MS/s")
        self.workbench.loss_status_label.setText("坏包 7")

        self.workbench.source_combo.setCurrentText("内置仿真")

        self.assertEqual(
            self.workbench.plot.sample_rate_hz,
            self.workbench.SIMULATION_SAMPLE_RATE_HZ,
        )
        self.assertEqual(self.workbench.sample_rate_metric[1].text(), "32.00 MS/s")
        self.assertIn("无网络丢包", self.workbench.loss_status_label.text())
        self.assertFalse(self.workbench.channel_checks[1].isChecked())
        self.assertTrue(self.workbench.channel_checks[2].isChecked())

    def test_udp_receiver_failure_transitions_out_of_running_state(self):
        class FailedReceiver:
            bound_endpoint = ("127.0.0.1", 8080)
            last_capabilities = None
            is_running = False
            stats = ScopeReceiverStats(last_error="injected receive failure")

            def __init__(self, *_args, **_kwargs):
                pass

            def start(self):
                self.is_running = True

            def send_inquiry(self, *_args):
                pass

            def send_capture_request(self, *_args):
                self.is_running = False

            def drain(self, *_args, **_kwargs):
                return []

            def stop(self):
                self.is_running = False

        self.workbench.source_combo.setCurrentText("FPGA UDP")
        self.workbench.local_ip_combo.setCurrentText("127.0.0.1")
        self.workbench.fpga_ip_edit.setText("127.0.0.1")
        with patch("qt_oscilloscope_workbench.UdpScopeReceiver", FailedReceiver):
            self.assertTrue(self.workbench.start_acquisition())
            self.workbench._capture_request_due = 0.0
            self.workbench._refresh_display()

        self.assertFalse(self.workbench.is_running)
        self.assertIn("失败", self.workbench.connection_status_label.text())
        self.assertIn("injected", self.workbench.detail_status_label.text())

    def test_udp_capture_timeout_stops_instead_of_hanging(self):
        class SilentReceiver:
            bound_endpoint = ("127.0.0.1", 8080)
            last_capabilities = None
            is_running = True
            stats = ScopeReceiverStats()

            def __init__(self, *_args, **_kwargs):
                pass

            def start(self):
                pass

            def send_inquiry(self, *_args):
                pass

            def send_capture_request(self, *_args):
                pass

            def drain(self, *_args, **_kwargs):
                return []

            def stop(self):
                self.is_running = False

        self.workbench.source_combo.setCurrentText("FPGA UDP")
        self.workbench.local_ip_combo.setCurrentText("127.0.0.1")
        self.workbench.fpga_ip_edit.setText("127.0.0.1")
        with patch("qt_oscilloscope_workbench.UdpScopeReceiver", SilentReceiver):
            self.assertTrue(self.workbench.start_acquisition())
            self.workbench._capture_request_due = 0.0
            self.workbench._refresh_display()
            self.workbench._capture_deadline = 0.0
            self.workbench._refresh_display()

        self.assertFalse(self.workbench.is_running)
        self.assertIn("超时", self.workbench.detail_status_label.text())

    def test_udp_packets_are_appended_to_ring_in_one_batch(self):
        packets = []
        protocol = LegacyUdpScopeProtocol()
        for value in (1, 2, 3):
            payload = (
                b"\x01\x00\x01\x00\x02"
                + np.full(512, value, dtype=np.int16).astype(">i2").tobytes()
            )
            packets.append(protocol.parse_data_packet(payload))

        class BurstReceiver:
            bound_endpoint = ("127.0.0.1", 8080)
            last_capabilities = None
            is_running = True

            def __init__(self, *_args, **_kwargs):
                self.stats = ScopeReceiverStats()
                self._packets = []

            def start(self):
                pass

            def send_inquiry(self, *_args):
                pass

            def send_capture_request(self, *_args):
                self._packets = list(packets)

            def drain(self, *_args, **_kwargs):
                result, self._packets = self._packets, []
                self.stats.received_sample_count += sum(p.samples.size for p in result)
                return result

            def stop(self):
                self.is_running = False

        self.workbench.source_combo.setCurrentText("FPGA UDP")
        self.workbench.local_ip_combo.setCurrentText("127.0.0.1")
        self.workbench.fpga_ip_edit.setText("127.0.0.1")
        self.workbench.capture_samples_spin.setValue(1536)
        with patch("qt_oscilloscope_workbench.UdpScopeReceiver", BurstReceiver):
            self.assertTrue(self.workbench.start_acquisition())
            self.workbench._capture_request_due = 0.0
            with patch.object(self.workbench.sample_buffer, "append_channel", wraps=self.workbench.sample_buffer.append_channel) as append:
                self.workbench._refresh_display()
            self.assertEqual(append.call_count, 1)
            self.assertEqual(self.workbench.sample_buffer.size, 1536)

    def test_invalid_capability_frame_is_rejected_before_capture(self):
        class InvalidCapabilityReceiver:
            bound_endpoint = ("127.0.0.1", 8080)
            is_running = True
            stats = ScopeReceiverStats(inquiry_replies=1)
            last_capabilities = ScopeCapabilities(
                fpga_mac="00:0A:35:01:FE:C0",
                fpga_ip="127.0.0.1",
                signed=False,
                sample_bits=0,
                sample_bytes=0,
                channel_count=0,
                sample_rate_hz=0,
                sample_depth=0,
            )

            def __init__(self, *_args, **_kwargs):
                self.capture_sent = False

            def start(self):
                pass

            def send_inquiry(self, *_args):
                pass

            def send_capture_request(self, *_args):
                self.capture_sent = True

            def drain(self, *_args, **_kwargs):
                return []

            def stop(self):
                self.is_running = False

        self.workbench.source_combo.setCurrentText("FPGA UDP")
        self.workbench.local_ip_combo.setCurrentText("127.0.0.1")
        self.workbench.fpga_ip_edit.setText("127.0.0.1")
        with patch(
            "qt_oscilloscope_workbench.UdpScopeReceiver",
            InvalidCapabilityReceiver,
        ):
            self.assertTrue(self.workbench.start_acquisition())
            receiver = self.workbench._receiver
            self.workbench._refresh_display()

        self.assertFalse(receiver.capture_sent)
        self.assertFalse(self.workbench.is_running)
        self.assertIn("协议不兼容", self.workbench.detail_status_label.text())

    def test_capture_deadline_has_a_hard_upper_bound(self):
        class SlowReceiver:
            stats = ScopeReceiverStats()

            def discard_queued_samples(self):
                return 0

            def send_capture_request(self, *_args):
                pass

        self.workbench.plot.sample_rate_hz = 1.0
        before = time.monotonic()
        self.workbench._send_capture_request(SlowReceiver())
        self.assertLessEqual(
            self.workbench._capture_deadline - before,
            self.workbench.MAX_CAPTURE_TIMEOUT_SECONDS + 0.1,
        )

    def test_udp_queue_drop_marks_capture_incomplete_and_stops(self):
        class DroppingReceiver:
            bound_endpoint = ("127.0.0.1", 8080)
            last_capabilities = None
            is_running = True

            def __init__(self, *_args, **_kwargs):
                self.stats = ScopeReceiverStats()

            def start(self):
                pass

            def send_inquiry(self, *_args):
                pass

            def send_capture_request(self, *_args):
                self.stats.received_sample_count = 512
                self.stats.queue_dropped_packets = 1

            def drain(self, *_args, **_kwargs):
                return []

            def stop(self):
                self.is_running = False

        self.workbench.source_combo.setCurrentText("FPGA UDP")
        self.workbench.local_ip_combo.setCurrentText("127.0.0.1")
        self.workbench.fpga_ip_edit.setText("127.0.0.1")
        with patch("qt_oscilloscope_workbench.UdpScopeReceiver", DroppingReceiver):
            self.assertTrue(self.workbench.start_acquisition())
            self.workbench._capture_request_due = 0.0
            self.workbench._refresh_display()

        self.assertFalse(self.workbench.is_running)
        self.assertIn("不完整", self.workbench.detail_status_label.text())
        self.assertIn("队列丢弃", self.workbench.loss_status_label.text())

    def test_single_shot_simulation_stops_after_requested_sample_count(self):
        self.workbench.source_combo.setCurrentText("内置仿真")
        self.workbench.acquisition_mode_combo.setCurrentText("单次")
        self.workbench.capture_samples_spin.setValue(512)

        self.workbench.start_button.click()
        QTest.qWait(100)
        self.app.processEvents()

        self.assertFalse(self.workbench.is_running)
        self.assertEqual(self.workbench.sample_buffer.size, 512)
        self.assertIn("单次采集完成", self.workbench.connection_status_label.text())

    def test_udp_capture_request_waits_until_inquiry_reply_or_timeout(self):
        calls = []

        class FakeReceiver:
            def __init__(self, _config, protocol=None):
                self.protocol = protocol
                self.bound_endpoint = ("127.0.0.1", 8080)
                self.last_capabilities = None
                self.stats = ScopeReceiverStats()

            def start(self):
                calls.append("start")

            def send_inquiry(self, *_args):
                calls.append("inquiry")

            def send_capture_request(self, *_args):
                calls.append("capture")

            def drain(self, *_args, **_kwargs):
                return []

            def stop(self):
                calls.append("stop")

        self.workbench.source_combo.setCurrentText("FPGA UDP")
        self.workbench.local_ip_combo.setCurrentText("127.0.0.1")
        self.workbench.fpga_ip_edit.setText("127.0.0.1")
        with patch("qt_oscilloscope_workbench.UdpScopeReceiver", FakeReceiver):
            self.assertTrue(self.workbench.start_acquisition())
            self.assertEqual(calls, ["start", "inquiry"])
            self.workbench._capture_request_due = 0.0
            self.workbench._refresh_display()
            self.assertEqual(calls, ["start", "inquiry", "capture"])

    def test_udp_stale_samples_before_capture_request_are_not_accepted(self):
        protocol = LegacyUdpScopeProtocol()
        payload = (
            b"\x01\x00\x01\x00\x02"
            + np.full(512, 9, dtype=np.int16).astype(">i2").tobytes()
        )
        stale_packet = protocol.parse_data_packet(payload)

        class StaleReceiver:
            bound_endpoint = ("127.0.0.1", 8080)
            last_capabilities = None
            is_running = True

            def __init__(self, *_args, **_kwargs):
                self.stats = ScopeReceiverStats(received_sample_count=512)
                self._packets = [stale_packet]

            def start(self):
                pass

            def send_inquiry(self, *_args):
                pass

            def send_capture_request(self, *_args):
                pass

            def drain(self, *_args, **_kwargs):
                result, self._packets = self._packets, []
                return result

            def discard_queued_samples(self):
                count = len(self._packets)
                self._packets.clear()
                return count

            def stop(self):
                self.is_running = False

        self.workbench.source_combo.setCurrentText("FPGA UDP")
        self.workbench.local_ip_combo.setCurrentText("127.0.0.1")
        self.workbench.fpga_ip_edit.setText("127.0.0.1")
        self.workbench.acquisition_mode_combo.setCurrentText("单次")
        self.workbench.capture_samples_spin.setValue(512)
        with patch("qt_oscilloscope_workbench.UdpScopeReceiver", StaleReceiver):
            self.assertTrue(self.workbench.start_acquisition())
            self.workbench._refresh_display()
            self.assertFalse(self.workbench._capture_request_sent)
            self.assertEqual(self.workbench.sample_buffer.size, 0)

            self.workbench._capture_request_due = 0.0
            self.workbench._refresh_display()
            self.assertTrue(self.workbench._capture_request_sent)
            self.assertEqual(self.workbench.sample_buffer.size, 0)


class OscilloscopeMainWindowIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = ensure_app()

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        settings = QSettings(
            f"{self.temp_dir.name}/main.ini", QSettings.IniFormat
        )
        self.window = MainWindow(
            settings=settings,
            experiment_repository_path=Path(self.temp_dir.name) / "records",
        )
        self.window.resize(1400, 820)
        self.window.show()
        self.app.processEvents()

    def tearDown(self):
        self.window.close()
        self.app.processEvents()
        self.temp_dir.cleanup()

    def test_left_rail_opens_singleton_scope_as_detachable_workspace_tab(self):
        self.assertEqual(
            self.window.oscilloscope_rail_btn.accessibleName(),
            "打开实时示波器工作台",
        )
        self.window.oscilloscope_rail_btn.click()
        self.app.processEvents()
        first = self.window._oscilloscope_workbench
        first_index = self.window.workspace_tabs.indexOf(first)

        self.assertIsInstance(first, OscilloscopeWorkbench)
        self.assertGreaterEqual(first_index, 1)
        self.assertEqual(
            self.window.workspace_tabs.tabText(first_index), "实时示波器"
        )

        self.window.workspace_tabs.show_home()
        second = self.window.open_oscilloscope_workbench()
        self.assertIs(first, second)
        self.assertEqual(
            sum(
                self.window.workspace_tabs.widget(index) is first
                for index in range(self.window.workspace_tabs.count())
            ),
            1,
        )

    def test_closing_scope_tab_stops_acquisition_and_reopening_restarts_rendering(self):
        scope = self.window.open_oscilloscope_workbench()
        scope.source_combo.setCurrentText("内置仿真")
        scope.start_button.click()
        QTest.qWait(80)
        self.assertTrue(scope.is_running)

        self.assertTrue(
            self.window.workspace_tabs.close_workspace("oscilloscope-workbench")
        )
        self.assertFalse(scope.is_running)

        reopened = self.window.open_oscilloscope_workbench()
        self.app.processEvents()
        self.assertIs(reopened, scope)
        self.assertTrue(reopened._render_timer.isActive())


if __name__ == "__main__":
    unittest.main()
