"""Protocol contracts for the DClocking oscilloscope data plane.

The repository currently contains a legacy UDP implementation in
``modules/waveform_storage_upload``.  This module deliberately isolates that
wire format so a future versioned protocol can be added without coupling the
Qt workbench to today\'s HDL quirks.
"""

from __future__ import annotations

from dataclasses import dataclass
import ipaddress
import re
import struct

import numpy as np


class ScopeProtocolError(ValueError):
    """Raised when a scope command or datagram violates the wire contract."""


@dataclass(frozen=True)
class ScopeCapabilities:
    fpga_mac: str
    fpga_ip: str
    signed: bool
    sample_bits: int
    sample_bytes: int
    channel_count: int
    sample_rate_hz: int
    sample_depth: int


@dataclass(frozen=True)
class ScopeSamplePacket:
    samples: np.ndarray
    header: int
    command: int
    channel_count: int = 1
    sequence: int | None = None

    @property
    def sequence_available(self) -> bool:
        return self.sequence is not None


class LegacyUdpScopeProtocol:
    """Adapter for the unversioned 8080/UDP protocol in the current HDL.

    The current ``eth_cmd.v`` accepts a 19-byte request, but captures the low
    byte of ``sample_num`` at an unreachable counter value.  Requests are
    therefore intentionally restricted to multiples of 256 until the HDL is
    corrected.  Silently rounding here would make the UI and FPGA disagree.
    """

    CMD_INQUIRY = 0x00010001
    CMD_DATA_REQUEST = 0x00010002
    REQUEST_BYTES = 19
    INQUIRY_REPLY_BYTES = 27
    DATA_PREFIX_BYTES = 5
    DATA_PACKET_BYTES = 1029
    DEFAULT_FPGA_MAC = "00:0A:35:01:FE:C0"
    DEFAULT_FPGA_IP = "192.168.0.2"
    DEFAULT_PORT = 8080
    # The unreachable low byte makes 256 the encoding granularity, while the
    # current Ethernet sender only starts when a full 512-sample FIFO packet is
    # available.  Enforce the stricter end-to-end quantum.
    LEGACY_SAMPLE_GRANULARITY = 512
    MAX_SAMPLE_COUNT = 0x40000

    @staticmethod
    def _mac_bytes(value: str | bytes | bytearray) -> bytes:
        if isinstance(value, (bytes, bytearray)):
            result = bytes(value)
        else:
            compact = re.sub(r"[:-]", "", str(value).strip())
            if not re.fullmatch(r"[0-9A-Fa-f]{12}", compact):
                raise ScopeProtocolError("FPGA MAC 地址格式无效")
            result = bytes.fromhex(compact)
        if len(result) != 6:
            raise ScopeProtocolError("FPGA MAC 地址必须为 6 字节")
        return result

    @staticmethod
    def _format_mac(value: bytes) -> str:
        return ":".join(f"{part:02X}" for part in value)

    def _build_request(
        self,
        command: int,
        *,
        fpga_mac: str | bytes,
        channel_mask: int,
        sample_count: int,
        header: int,
    ) -> bytes:
        if not 0 <= int(header) <= 0xFE or int(header) & 0x01:
            raise ScopeProtocolError("请求头最低位必须为 0")
        if not 1 <= int(channel_mask) <= 0x0F:
            raise ScopeProtocolError("通道掩码必须选择 CH1 至 CH4 中至少一个通道")
        if not self.LEGACY_SAMPLE_GRANULARITY <= int(sample_count) <= self.MAX_SAMPLE_COUNT:
            raise ScopeProtocolError("采样点数超出当前 FPGA 深度范围")
        if int(sample_count) % self.LEGACY_SAMPLE_GRANULARITY:
            raise ScopeProtocolError("当前 RTL 仅能可靠接收 512 点整数倍的采样数")
        return b"".join(
            (
                bytes((int(header),)),
                struct.pack(">I", int(command)),
                self._mac_bytes(fpga_mac),
                struct.pack(">I", int(channel_mask)),
                struct.pack(">I", int(sample_count)),
            )
        )

    def build_inquiry_request(
        self,
        *,
        fpga_mac: str | bytes = DEFAULT_FPGA_MAC,
        header: int = 0,
    ) -> bytes:
        return self._build_request(
            self.CMD_INQUIRY,
            fpga_mac=fpga_mac,
            channel_mask=1,
            sample_count=self.LEGACY_SAMPLE_GRANULARITY,
            header=header,
        )

    def build_capture_request(
        self,
        *,
        fpga_mac: str | bytes = DEFAULT_FPGA_MAC,
        channel_mask: int = 1,
        sample_count: int = 4096,
        header: int = 0,
    ) -> bytes:
        return self._build_request(
            self.CMD_DATA_REQUEST,
            fpga_mac=fpga_mac,
            channel_mask=channel_mask,
            sample_count=sample_count,
            header=header,
        )

    @staticmethod
    def _parse_reply_prefix(payload, expected_command: int) -> int:
        if len(payload) < LegacyUdpScopeProtocol.DATA_PREFIX_BYTES:
            raise ScopeProtocolError("UDP 数据报短于协议头")
        header = payload[0]
        command = struct.unpack_from(">I", payload, 1)[0]
        if not header & 0x01:
            raise ScopeProtocolError("收到的 UDP 数据报不是 FPGA 应答")
        if command != expected_command:
            raise ScopeProtocolError(f"UDP 应答命令不匹配: 0x{command:08X}")
        return header

    def parse_inquiry_reply(self, payload) -> ScopeCapabilities:
        if len(payload) != self.INQUIRY_REPLY_BYTES:
            raise ScopeProtocolError("设备信息应答长度必须为 27 字节")
        self._parse_reply_prefix(payload, self.CMD_INQUIRY)
        fpga_mac = self._format_mac(bytes(payload[5:11]))
        fpga_ip = str(ipaddress.IPv4Address(bytes(payload[11:15])))
        sample_rate_hz = struct.unpack_from(">I", payload, 19)[0]
        sample_depth = struct.unpack_from(">I", payload, 23)[0]
        return ScopeCapabilities(
            fpga_mac=fpga_mac,
            fpga_ip=fpga_ip,
            signed=payload[15] == 1,
            sample_bits=int(payload[16]),
            sample_bytes=int(payload[17]),
            # Preserve the wire value exactly. The workbench validates whether
            # it is compatible with the one-channel Legacy UDP V0 payload.
            channel_count=int(payload[18]),
            sample_rate_hz=sample_rate_hz,
            sample_depth=sample_depth,
        )

    def parse_data_packet(self, payload) -> ScopeSamplePacket:
        if len(payload) != self.DATA_PACKET_BYTES:
            raise ScopeProtocolError("Legacy UDP V0 采样数据报必须为 1029 字节")
        header = self._parse_reply_prefix(payload, self.CMD_DATA_REQUEST)
        sample_payload = memoryview(payload)[self.DATA_PREFIX_BYTES :]
        if not sample_payload or len(sample_payload) % 2:
            raise ScopeProtocolError("采样数据必须包含完整的 16 位样本")
        samples = np.frombuffer(sample_payload, dtype=">i2").astype(
            np.int16, copy=True
        )
        return ScopeSamplePacket(
            samples=samples,
            header=header,
            command=self.CMD_DATA_REQUEST,
        )

    def parse_datagram(self, payload):
        if len(payload) < self.DATA_PREFIX_BYTES:
            raise ScopeProtocolError("UDP 数据报短于协议头")
        command = struct.unpack_from(">I", payload, 1)[0]
        if command == self.CMD_INQUIRY:
            return self.parse_inquiry_reply(payload)
        if command == self.CMD_DATA_REQUEST:
            return self.parse_data_packet(payload)
        raise ScopeProtocolError(f"未知 UDP 命令: 0x{command:08X}")


class LegacyCaptureAssembler:
    """Collect a finite legacy capture without claiming unavailable telemetry."""

    def __init__(self, expected_samples: int):
        if int(expected_samples) <= 0:
            raise ValueError("expected_samples must be positive")
        self.expected_samples = int(expected_samples)
        self.packet_count = 0
        self._parts: list[np.ndarray] = []
        self._sample_count = 0

    @property
    def packet_loss_observable(self) -> bool:
        # The legacy UDP payload has no capture id or packet sequence number.
        return False

    @property
    def complete(self) -> bool:
        return self._sample_count >= self.expected_samples

    def append(self, samples) -> None:
        if self.complete:
            return
        values = np.asarray(samples, dtype=np.int16).reshape(-1)
        remaining = self.expected_samples - self._sample_count
        part = values[:remaining].copy()
        if part.size:
            self._parts.append(part)
            self._sample_count += int(part.size)
        self.packet_count += 1

    def samples(self) -> np.ndarray:
        if not self._parts:
            return np.empty(0, dtype=np.int16)
        return np.concatenate(self._parts)
