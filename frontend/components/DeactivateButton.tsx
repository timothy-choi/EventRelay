"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { apiUrl } from "../lib/api";
import { notifyDataChanged } from "../lib/refresh";

export function DeactivateButton({
  endpointId,
  isActive,
}: {
  endpointId: string;
  isActive: boolean;
}) {
  const router = useRouter();
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleClick() {
    if (!isActive) {
      return;
    }
    setPending(true);
    setError(null);

    try {
      const response = await fetch(apiUrl(`/endpoints/${endpointId}`), {
        method: "PATCH",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ is_active: false }),
      });
      if (!response.ok) {
        throw new Error(await response.text());
      }
      notifyDataChanged();
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to deactivate endpoint");
    } finally {
      setPending(false);
    }
  }

  return (
    <div className="action-stack">
      <button className="button" disabled={!isActive || pending} onClick={handleClick}>
        {pending ? "Deactivating..." : isActive ? "Deactivate" : "Inactive"}
      </button>
      {error ? <p className="inline-error">{error}</p> : null}
    </div>
  );
}
