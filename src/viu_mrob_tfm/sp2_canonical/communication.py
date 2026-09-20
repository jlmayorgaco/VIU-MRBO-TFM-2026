"""Auditable local communication model for SP2.N3."""

from __future__ import annotations

import heapq
import json
from dataclasses import dataclass, field
from typing import Any

import numpy as np


def canonical_message_bytes(payload: dict[str, Any]) -> int:
    """Return UTF-8 bytes of deterministic compact JSON serialization."""

    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return len(encoded)


@dataclass(frozen=True, slots=True)
class ChannelConfig:
    communication_radius_m: float
    delay_mean_s: float = 0.0
    delay_jitter_s: float = 0.0
    loss_probability: float = 0.0
    bandwidth_bytes_s: float = float("inf")
    retransmissions: int = 0

    def __post_init__(self) -> None:
        if self.communication_radius_m <= 0.0:
            raise ValueError("communication radius must be strictly positive")
        if min(self.delay_mean_s, self.delay_jitter_s) < 0.0:
            raise ValueError("delays must be non-negative")
        if not 0.0 <= self.loss_probability <= 1.0:
            raise ValueError("loss probability must lie in [0, 1]")
        if self.bandwidth_bytes_s <= 0.0:
            raise ValueError("bandwidth must be strictly positive")
        if self.retransmissions < 0:
            raise ValueError("retransmissions must be non-negative")


@dataclass(frozen=True, slots=True)
class Delivery:
    sender: str
    receiver: str
    sequence: int
    sent_at_s: float
    delivered_at_s: float | None
    size_bytes: int
    attempts: int
    status: str
    payload: dict[str, Any]


@dataclass(slots=True)
class NetworkStats:
    attempted_messages: int = 0
    queued_messages: int = 0
    delivered_messages: int = 0
    dropped_messages: int = 0
    attempted_bytes: int = 0
    queued_bytes: int = 0
    delivered_bytes: int = 0
    dropped_bytes: int = 0
    latencies_s: list[float] = field(default_factory=list)

    @property
    def delivery_ratio(self) -> float:
        return self.delivered_messages / max(self.attempted_messages, 1)

    @property
    def mean_latency_s(self) -> float:
        return float(np.mean(self.latencies_s)) if self.latencies_s else float("nan")


class SeededLocalChannel:
    """Local point-to-point channel with reproducible delay, loss and capacity."""

    def __init__(self, config: ChannelConfig, seed: int) -> None:
        self.config = config
        self.rng = np.random.default_rng(seed)
        self.stats = NetworkStats()
        self._receiver_available_at: dict[str, float] = {}
        self._queue: list[tuple[float, int, Delivery]] = []
        self._counter = 0

    def send(
        self,
        message: dict[str, Any],
        receiver: str,
        sender_position_m: np.ndarray,
        receiver_position_m: np.ndarray,
        now_s: float,
    ) -> Delivery:
        sender = str(message["sender"])
        sequence = int(message["sequence"])
        size = canonical_message_bytes(message)
        self.stats.attempted_messages += 1
        self.stats.attempted_bytes += size
        distance = float(
            np.linalg.norm(
                np.asarray(sender_position_m, dtype=float)
                - np.asarray(receiver_position_m, dtype=float)
            )
        )
        if distance > self.config.communication_radius_m:
            self.stats.dropped_messages += 1
            self.stats.dropped_bytes += size
            return Delivery(sender, receiver, sequence, now_s, None, size, 0, "out_of_range", message)

        attempts = 0
        delivered = False
        while attempts <= self.config.retransmissions and not delivered:
            attempts += 1
            delivered = bool(self.rng.random() >= self.config.loss_probability)
        if not delivered:
            self.stats.dropped_messages += 1
            self.stats.dropped_bytes += size
            return Delivery(sender, receiver, sequence, now_s, None, size, attempts, "lost", message)

        jitter = float(self.rng.uniform(-self.config.delay_jitter_s, self.config.delay_jitter_s))
        propagation = max(0.0, self.config.delay_mean_s + jitter)
        available = max(now_s, self._receiver_available_at.get(receiver, now_s))
        serialization = 0.0 if np.isinf(self.config.bandwidth_bytes_s) else size / self.config.bandwidth_bytes_s
        delivered_at = available + propagation + serialization
        self._receiver_available_at[receiver] = delivered_at
        delivery = Delivery(sender, receiver, sequence, now_s, delivered_at, size, attempts, "queued", message)
        self.stats.queued_messages += 1
        self.stats.queued_bytes += size
        heapq.heappush(self._queue, (delivered_at, self._counter, delivery))
        self._counter += 1
        return delivery

    def receive_until(self, now_s: float) -> list[Delivery]:
        delivered: list[Delivery] = []
        while self._queue and self._queue[0][0] <= now_s:
            _, _, item = heapq.heappop(self._queue)
            complete = Delivery(
                item.sender,
                item.receiver,
                item.sequence,
                item.sent_at_s,
                item.delivered_at_s,
                item.size_bytes,
                item.attempts,
                "delivered",
                item.payload,
            )
            delivered.append(complete)
            self.stats.delivered_messages += 1
            self.stats.delivered_bytes += item.size_bytes
            self.stats.latencies_s.append(float(item.delivered_at_s - item.sent_at_s))
        return delivered


def _header(
    *,
    message_type: str,
    coalition_id: str,
    membership_version: int,
    sequence: int,
    sender_id: str,
    timestamp_s: float,
) -> dict[str, Any]:
    return {
        "coalition": coalition_id,
        "membership_version": int(membership_version),
        "sequence": int(sequence),
        "sender": sender_id,
        "timestamp_s": float(timestamp_s),
        "type": message_type,
    }


def leader_follower_update(
    *,
    coalition_id: str,
    membership_version: int,
    sequence: int,
    pose: list[float],
    twist: list[float],
    sender_id: str = "leader",
    timestamp_s: float = 0.0,
) -> dict[str, Any]:
    message = _header(
        message_type="leader_reference",
        coalition_id=coalition_id,
        membership_version=membership_version,
        sequence=sequence,
        sender_id=sender_id,
        timestamp_s=timestamp_s,
    )
    message.update({"pose": pose, "twist": twist})
    return message


def virtual_structure_update(
    *,
    coalition_id: str,
    membership_version: int,
    sequence: int,
    robot_id: str,
    pose_estimate: list[float],
    twist_estimate: list[float],
    confidence: float = 1.0,
    timestamp_s: float = 0.0,
    covariance_diagonal: list[float] | None = None,
) -> dict[str, Any]:
    """Create a local estimate message with optional marginal variances.

    ``covariance_diagonal`` is descriptive metadata from the local estimator;
    transmitting it does not imply that the receiver implements a covariance
    filter.
    """

    if covariance_diagonal is not None:
        covariance = np.asarray(covariance_diagonal, dtype=float)
        if covariance.shape != (3,) or np.any(covariance < 0.0) or not np.all(np.isfinite(covariance)):
            raise ValueError("covariance_diagonal must contain three finite non-negative values")
    message = _header(
        message_type="virtual_structure_estimate",
        coalition_id=coalition_id,
        membership_version=membership_version,
        sequence=sequence,
        sender_id=robot_id,
        timestamp_s=timestamp_s,
    )
    message.update(
        {
            "confidence": float(confidence),
            "pose_estimate": pose_estimate,
            "twist_estimate": twist_estimate,
        }
    )
    if covariance_diagonal is not None:
        message["covariance_diagonal"] = covariance.tolist()
    return message


__all__ = [
    "ChannelConfig",
    "Delivery",
    "NetworkStats",
    "SeededLocalChannel",
    "canonical_message_bytes",
    "leader_follower_update",
    "virtual_structure_update",
]
