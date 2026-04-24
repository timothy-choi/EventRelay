from __future__ import annotations

from pydantic import BaseModel


class SystemStatsRead(BaseModel):
    total_events_processed: int
    total_deliveries: int
    total_attempts: int
    success_rate: float
    avg_latency_ms: float | None
    p95_latency_ms: float | None
    rate_limited_count: int
    delayed_due_to_backpressure_count: int
    current_queue_depth: int
