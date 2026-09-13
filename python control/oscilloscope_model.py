"""Thread-independent sample storage and rendering reduction for the scope UI."""

from __future__ import annotations

import threading

import numpy as np


class ScopeSampleBuffer:
    """Fixed-size, multi-channel ring buffer with peak-preserving reduction."""

    def __init__(self, channel_count=4, capacity=262_144):
        if int(channel_count) <= 0 or int(capacity) <= 0:
            raise ValueError("channel_count and capacity must be positive")
        self.channel_count = int(channel_count)
        self.capacity = int(capacity)
        self._data = np.full(
            (self.channel_count, self.capacity), np.nan, dtype=np.float32
        )
        self._write_index = 0
        self._size = 0
        self._lock = threading.RLock()

    @property
    def size(self) -> int:
        with self._lock:
            return self._size

    def clear(self) -> None:
        with self._lock:
            self._data.fill(np.nan)
            self._write_index = 0
            self._size = 0

    def append(self, samples) -> None:
        values = np.asarray(samples, dtype=np.float32)
        if values.ndim == 1:
            values = values.reshape(1, -1)
        if values.ndim != 2 or values.shape[0] != self.channel_count:
            raise ValueError(
                f"samples must have shape ({self.channel_count}, sample_count)"
            )
        self._append_matrix(values)

    def append_channel(self, channel_index: int, samples) -> None:
        channel_index = int(channel_index)
        if not 0 <= channel_index < self.channel_count:
            raise IndexError("channel_index out of range")
        values = np.asarray(samples, dtype=np.float32).reshape(-1)
        matrix = np.full((self.channel_count, values.size), np.nan, dtype=np.float32)
        matrix[channel_index] = values
        self._append_matrix(matrix)

    def _append_matrix(self, values: np.ndarray) -> None:
        count = int(values.shape[1])
        if count == 0:
            return
        if count >= self.capacity:
            values = values[:, -self.capacity :]
            count = self.capacity
        with self._lock:
            first = min(count, self.capacity - self._write_index)
            self._data[:, self._write_index : self._write_index + first] = values[:, :first]
            remaining = count - first
            if remaining:
                self._data[:, :remaining] = values[:, first:]
            self._write_index = (self._write_index + count) % self.capacity
            self._size = min(self.capacity, self._size + count)

    def snapshot(self, sample_count: int | None = None) -> np.ndarray:
        with self._lock:
            count = self._size
            if sample_count is not None:
                count = min(count, max(0, int(sample_count)))
            if count == 0:
                return np.empty((self.channel_count, 0), dtype=np.float32)
            start = (self._write_index - count) % self.capacity
            if start + count <= self.capacity:
                return self._data[:, start : start + count].copy()
            first = self._data[:, start:]
            second = self._data[:, : count - first.shape[1]]
            return np.concatenate((first, second), axis=1)

    def min_max_envelope(
        self, max_columns: int, sample_count: int | None = None
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        if int(max_columns) <= 0:
            raise ValueError("max_columns must be positive")
        values = self.snapshot(sample_count)
        count = values.shape[1]
        if count == 0:
            empty = np.empty(0, dtype=np.float32)
            channels = np.empty((self.channel_count, 0), dtype=np.float32)
            return empty, channels, channels.copy()
        if count <= max_columns:
            x = np.arange(count, dtype=np.float32)
            return x, values.copy(), values.copy()

        edges = np.linspace(0, count, int(max_columns) + 1, dtype=np.int64)
        lows = np.empty((self.channel_count, max_columns), dtype=np.float32)
        highs = np.empty_like(lows)
        x = np.empty(max_columns, dtype=np.float32)
        for column in range(max_columns):
            start = int(edges[column])
            stop = max(start + 1, int(edges[column + 1]))
            block = values[:, start:stop]
            for channel in range(self.channel_count):
                finite = block[channel, np.isfinite(block[channel])]
                if finite.size:
                    lows[channel, column] = float(finite.min())
                    highs[channel, column] = float(finite.max())
                else:
                    lows[channel, column] = np.nan
                    highs[channel, column] = np.nan
            x[column] = (start + stop - 1) / 2.0
        return x, lows, highs
