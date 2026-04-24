"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

export function AutoRefresh({
  intervalMs = 5000,
  label = "Auto-refreshing every 5s",
}: {
  intervalMs?: number;
  label?: string;
}) {
  const router = useRouter();
  const [enabled, setEnabled] = useState(true);

  useEffect(() => {
    if (!enabled) {
      return;
    }

    const timer = window.setInterval(() => {
      router.refresh();
    }, intervalMs);

    return () => window.clearInterval(timer);
  }, [enabled, intervalMs, router]);

  return (
    <div className="refresh-bar">
      <span className="muted">{enabled ? label : "Auto-refresh paused"}</span>
      <button className="button" onClick={() => setEnabled((value) => !value)}>
        {enabled ? "Pause" : "Resume"}
      </button>
    </div>
  );
}
