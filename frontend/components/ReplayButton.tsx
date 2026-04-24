"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { notifyDataChanged } from "../lib/refresh";

export function ReplayButton({ deliveryId }: { deliveryId: string }) {
  const router = useRouter();
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleClick() {
    setPending(true);
    setError(null);

    try {
      const response = await fetch(`/api/deliveries/${deliveryId}/replay`, {
        method: "POST",
      });
      if (!response.ok) {
        throw new Error(await response.text());
      }
      const replayedDelivery = (await response.json()) as { id: string };
      notifyDataChanged();
      router.push(`/deliveries/${replayedDelivery.id}`);
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to replay delivery");
    } finally {
      setPending(false);
    }
  }

  return (
    <div className="action-stack">
      <button className="button" disabled={pending} onClick={handleClick}>
        {pending ? "Replaying..." : "Replay delivery"}
      </button>
      {error ? <p className="inline-error">{error}</p> : null}
    </div>
  );
}
