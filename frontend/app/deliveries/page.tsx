"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { DeliveryListItem } from "../../lib/types";
import { DATA_CHANGED_EVENT } from "../../lib/refresh";

async function fetchDeliveries(): Promise<DeliveryListItem[]> {
  const response = await fetch("/api/deliveries", {
    cache: "no-store",
  });
  if (!response.ok) {
    throw new Error(await response.text());
  }
  const deliveries = (await response.json()) as DeliveryListItem[];
  return deliveries.sort(
    (left, right) => new Date(right.created_at).getTime() - new Date(left.created_at).getTime(),
  );
}

export default function DeliveriesPage() {
  const [deliveries, setDeliveries] = useState<DeliveryListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;

    async function load() {
      try {
        setError(null);
        const data = await fetchDeliveries();
        if (active) {
          setDeliveries(data);
        }
      } catch (err) {
        if (active) {
          setError(err instanceof Error ? err.message : "Failed to load deliveries.");
        }
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    }

    void load();

    const timer = window.setInterval(() => {
      void load();
    }, 3000);

    function handleDataChanged() {
      void load();
    }

    window.addEventListener(DATA_CHANGED_EVENT, handleDataChanged);
    return () => {
      active = false;
      window.clearInterval(timer);
      window.removeEventListener(DATA_CHANGED_EVENT, handleDataChanged);
    };
  }, []);

  async function handleRefresh() {
    setLoading(true);
    try {
      setDeliveries(await fetchDeliveries());
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load deliveries.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="stack">
      <div className="page-header">
        <h1>Deliveries</h1>
        <p>Track delivery state, retries, and the most recent error for each event.</p>
      </div>

      <div className="refresh-bar">
        <span className="muted">{loading ? "Refreshing deliveries..." : "Polling every 3s"}</span>
        <button className="button" onClick={handleRefresh}>
          Refresh
        </button>
      </div>

      {error ? (
        <div className="error-box">{error}</div>
      ) : (
        <div className="card">
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Status</th>
                  <th>Event</th>
                  <th>Endpoint</th>
                  <th>Created</th>
                  <th>Attempts</th>
                  <th>Last error</th>
                </tr>
              </thead>
              <tbody>
                {deliveries.map((delivery) => (
                  <tr key={delivery.id}>
                    <td>
                      <span className={`badge ${delivery.status}`}>{delivery.status}</span>
                    </td>
                    <td>
                      <Link href={`/deliveries/${delivery.id}`}>{delivery.event_type}</Link>
                    </td>
                    <td>{delivery.endpoint_name}</td>
                    <td>{delivery.created_at}</td>
                    <td>{delivery.total_attempts}</td>
                    <td>{delivery.last_error ?? "n/a"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
