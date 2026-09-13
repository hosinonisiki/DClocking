"""Cross-platform UDP receive worker for oscilloscope samples."""

from __future__ import annotations

from dataclasses import dataclass, replace
import ipaddress
import os
import queue
import socket
import threading
import time

from oscilloscope_protocol import (
    LegacyUdpScopeProtocol,
    ScopeCapabilities,
    ScopeProtocolError,
    ScopeSamplePacket,
)


@dataclass(frozen=True)
class ScopeEndpointConfig:
    local_ip: str = "0.0.0.0"
    local_port: int = LegacyUdpScopeProtocol.DEFAULT_PORT
    receive_buffer_bytes: int = 8 * 1024 * 1024
    socket_timeout_seconds: float = 0.1
    queue_packets: int = 4096
    allowed_remote_ip: str | None = None
    allowed_remote_port: int | None = None

    def __post_init__(self):
        if ipaddress.ip_address(self.local_ip).version != 4:
            raise ValueError("当前示波器传输层仅支持 IPv4")
        if (
            self.allowed_remote_ip is not None
            and ipaddress.ip_address(self.allowed_remote_ip).version != 4
        ):
            raise ValueError("FPGA 地址必须为 IPv4")
        if self.allowed_remote_port is not None and not 1 <= int(
            self.allowed_remote_port
        ) <= 65535:
            raise ValueError("FPGA UDP 源端口无效")
        if not 0 <= int(self.local_port) <= 65535:
            raise ValueError("UDP 端口必须在 0 至 65535 之间")
        if not 64 * 1024 <= int(self.receive_buffer_bytes) <= 64 * 1024 * 1024:
            raise ValueError("UDP 接收缓冲必须在 64 KiB 至 64 MiB 之间")
        if not 0.01 <= float(self.socket_timeout_seconds) <= 10.0:
            raise ValueError("socket timeout must be between 0.01 and 10 seconds")
        if not 1 <= int(self.queue_packets) <= 16_384:
            raise ValueError("queue_packets must be between 1 and 16384")


@dataclass
class ScopeReceiverStats:
    received_datagrams: int = 0
    received_sample_count: int = 0
    malformed_datagrams: int = 0
    queue_dropped_packets: int = 0
    inquiry_replies: int = 0
    foreign_datagrams: int = 0
    last_error: str = ""
    last_datagram_monotonic: float | None = None
    last_sample_monotonic: float | None = None


class UdpScopeReceiver:
    """Own one UDP socket and publish parsed packets through a bounded queue."""

    def __init__(self, config: ScopeEndpointConfig, protocol=None):
        self.config = config
        self.protocol = protocol or LegacyUdpScopeProtocol()
        self._queue: queue.Queue[ScopeSamplePacket] = queue.Queue(
            maxsize=config.queue_packets
        )
        self._queue_lock = threading.Lock()
        self._stats = ScopeReceiverStats()
        self._stats_lock = threading.Lock()
        self._lifecycle_lock = threading.RLock()
        self._stop_event = threading.Event()
        self._ready_event = threading.Event()
        self._socket: socket.socket | None = None
        self._thread: threading.Thread | None = None
        self._bound_endpoint: tuple[str, int] | None = None
        self._last_capabilities: ScopeCapabilities | None = None

    @property
    def stats(self) -> ScopeReceiverStats:
        with self._stats_lock:
            return replace(self._stats)

    @property
    def last_capabilities(self) -> ScopeCapabilities | None:
        return self._last_capabilities

    @property
    def bound_endpoint(self) -> tuple[str, int] | None:
        return self._bound_endpoint

    @property
    def is_running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def start(self) -> None:
        with self._lifecycle_lock:
            existing = self._thread
            if existing is not None and existing.is_alive():
                if self._stop_event.is_set():
                    raise RuntimeError("上一次 UDP 接收线程仍在停止中，请稍后重试")
                return
            self._thread = None
            self._socket = None
            self._bound_endpoint = None
            self._ready_event.clear()
            self._last_capabilities = None
            with self._stats_lock:
                self._stats = ScopeReceiverStats()
            self.discard_queued_samples()

            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            try:
                if os.name == "nt" and hasattr(socket, "SO_EXCLUSIVEADDRUSE"):
                    sock.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
                else:
                    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                sock.setsockopt(
                    socket.SOL_SOCKET,
                    socket.SO_RCVBUF,
                    int(self.config.receive_buffer_bytes),
                )
                sock.settimeout(float(self.config.socket_timeout_seconds))
                sock.bind((self.config.local_ip, int(self.config.local_port)))
            except Exception:
                sock.close()
                raise

            stop_event = threading.Event()
            thread = threading.Thread(
                target=self._receive_loop,
                args=(sock, stop_event),
                name="DClockingUdpScopeReceiver",
                daemon=True,
            )
            self._socket = sock
            self._stop_event = stop_event
            self._thread = thread
            host, port = sock.getsockname()[:2]
            self._bound_endpoint = (str(host), int(port))
            self._ready_event.set()
            thread.start()

    def wait_until_ready(self, timeout=None) -> bool:
        return self._ready_event.wait(timeout)

    def _receive_loop(self, sock: socket.socket, stop_event: threading.Event) -> None:
        # Winsock raises WSAEMSGSIZE when recvfrom_into receives a datagram larger
        # than its buffer.  Allocate the maximum UDP datagram once, then enforce
        # the protocol's exact 27/1029-byte gate below without killing the worker.
        buffer = bytearray(65_535)
        view = memoryview(buffer)
        while not stop_event.is_set():
            try:
                count, source = sock.recvfrom_into(view)
            except socket.timeout:
                continue
            except OSError as exc:
                if not stop_event.is_set():
                    with self._stats_lock:
                        self._stats.last_error = str(exc)
                break
            if (
                self.config.allowed_remote_ip is not None
                and source[0] != self.config.allowed_remote_ip
            ):
                with self._stats_lock:
                    self._stats.foreign_datagrams += 1
                continue
            if (
                self.config.allowed_remote_port is not None
                and int(source[1]) != int(self.config.allowed_remote_port)
            ):
                with self._stats_lock:
                    self._stats.foreign_datagrams += 1
                continue
            received_at = time.monotonic()
            accepted_lengths = {
                self.protocol.INQUIRY_REPLY_BYTES,
                self.protocol.DATA_PACKET_BYTES,
            }
            if count not in accepted_lengths:
                with self._stats_lock:
                    self._stats.received_datagrams += 1
                    self._stats.malformed_datagrams += 1
                    self._stats.last_datagram_monotonic = received_at
                    self._stats.last_error = f"Legacy UDP 数据报长度无效: {count} 字节"
                continue
            try:
                parsed = self.protocol.parse_datagram(view[:count])
            except (ScopeProtocolError, ValueError, TypeError) as exc:
                with self._stats_lock:
                    self._stats.received_datagrams += 1
                    self._stats.malformed_datagrams += 1
                    self._stats.last_datagram_monotonic = received_at
                    self._stats.last_error = str(exc)
                continue
            with self._stats_lock:
                self._stats.received_datagrams += 1
                self._stats.last_datagram_monotonic = received_at
            if isinstance(parsed, ScopeCapabilities):
                self._last_capabilities = parsed
                with self._stats_lock:
                    self._stats.inquiry_replies += 1
                continue
            with self._stats_lock:
                self._stats.last_sample_monotonic = received_at
            self._enqueue(parsed)
        try:
            sock.close()
        except OSError:
            pass

    def _enqueue(self, packet: ScopeSamplePacket) -> None:
        with self._queue_lock:
            try:
                self._queue.put_nowait(packet)
            except queue.Full:
                try:
                    self._queue.get_nowait()
                except queue.Empty:
                    pass
                with self._stats_lock:
                    self._stats.queue_dropped_packets += 1
                self._queue.put_nowait(packet)
        with self._stats_lock:
            self._stats.received_sample_count += int(packet.samples.size)

    def drain(self, max_packets=4096) -> list[ScopeSamplePacket]:
        packets = []
        with self._queue_lock:
            for _ in range(max(0, int(max_packets))):
                try:
                    packets.append(self._queue.get_nowait())
                except queue.Empty:
                    break
        return packets

    def discard_queued_samples(self) -> int:
        """Drop packets queued before a new legacy capture request."""
        # Swap generations under a short lock. A producer can never refill the
        # discarded queue while the Qt thread is trying to clear it.
        with self._queue_lock:
            discarded = self._queue.qsize()
            self._queue = queue.Queue(maxsize=self.config.queue_packets)
        return discarded

    def send_inquiry(self, remote_ip: str, remote_port: int, fpga_mac: str) -> int:
        return self._send(
            self.protocol.build_inquiry_request(fpga_mac=fpga_mac),
            remote_ip,
            remote_port,
        )

    def send_capture_request(
        self,
        remote_ip: str,
        remote_port: int,
        fpga_mac: str,
        channel_mask: int,
        sample_count: int,
    ) -> int:
        payload = self.protocol.build_capture_request(
            fpga_mac=fpga_mac,
            channel_mask=channel_mask,
            sample_count=sample_count,
        )
        return self._send(payload, remote_ip, remote_port)

    def _send(self, payload: bytes, remote_ip: str, remote_port: int) -> int:
        ipaddress.ip_address(remote_ip)
        if not 1 <= int(remote_port) <= 65535:
            raise ValueError("FPGA UDP 端口无效")
        sock = self._socket
        if sock is None:
            raise RuntimeError("UDP 接收器尚未启动")
        return sock.sendto(payload, (remote_ip, int(remote_port)))

    def stop(self, timeout=1.0) -> None:
        with self._lifecycle_lock:
            stop_event = self._stop_event
            thread = self._thread
            sock = self._socket
            stop_event.set()
            if self._socket is sock:
                self._socket = None
            self._bound_endpoint = None
            self._ready_event.clear()
        if sock is not None:
            try:
                sock.close()
            except OSError:
                pass
        if thread is not None and thread is not threading.current_thread():
            thread.join(max(0.0, float(timeout)))
        with self._lifecycle_lock:
            # If close() did not interrupt recvfrom promptly, retain the exact
            # generation so start() cannot clear its event or lose track of it.
            if self._thread is thread and (
                thread is None or not thread.is_alive()
            ):
                self._thread = None
