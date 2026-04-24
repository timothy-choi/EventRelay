"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { DeliveryListItem, Endpoint } from "../lib/types";
import { DATA_CHANGED_EVENT } from "../lib/refresh";

async function fetchDashboardData(): Promise<{ endpoints: Endpoint[]; deliveries: DeliveryListItem[] }> {
  const [endpointsResponse, deliveriesResponse] = await Promise.all([
    fetch("/api/endpoints", { cache: "no-store" }),
    fetch("/api/deliveries", { cache: "no-store" }),
  ]);

  if (!endpointsResponse.ok) {
    throw new Error(await endpointsResponse.text());
  }
  if (!deliveriesResponse.ok) {
    throw new Error(await deliveriesResponse.text());
  }

  const endpoints = (await endpointsResponse.json()) as Endpoint[];
  const deliveries = ((await deliveriesResponse.json()) as DeliveryListItem[]).sort(
    (left, right) => new Date(right.created_at).getTime() - new Date(left.created_at).getTime(),
  );

  return { endpoints, deliveries };
}

export default function DashboardHome() {
  const [endpoints, setEndpoints] = useState<Endpoint[]>([]);
  const [deliveries, setDeliveries] = useState<DeliveryListItem[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;

    async function load() {
      try {
        setError(null);
        const data = await fetchDashboardData();
        if (active) {
          setEndpoints(data.endpoints);
          setDeliveries(data.deliveries);
        }
      } catch (err) {
        if (active) {
          setError(err instanceof Error ? err.message : "Failed to load dashboard.");
        }
      }
    }

    void load();

    const timer = window.setInterval(() => {
      void load();
    }, 5000);

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

  if (error) {
    return (
      <div className="stack">
        <div className="page-header">
          <h1>Dashboard</h1>
        </div>
        <div className="error-box">{error}</div>
      </div>
    );
  }

  const succeeded = deliveries.filter((delivery) => delivery.status === "succeeded").length;
  const failed = deliveries.filter((delivery) => delivery.status === "failed").length;
  const recentDeliveries = deliveries.slice(0, 5);

  return (
    <div className="stack">
      <div className="page-header">
        <h1>Dashboard</h1>
        <p>Watch endpoint volume, recent delivery activity, and reliability at a glance.</p>
      </div>

      <div className="grid stats">
        <div className="card">
          <div className="muted">Total endpoints</div>
          <div className="metric">{endpoints.length}</div>
        </div>
        <div className="card">
          <div className="muted">Succeeded deliveries</div>
          <div className="metric">{succeeded}</div>
        </div>
        <div className="card">
          <div className="muted">Failed deliveries</div>
          <div className="metric">{failed}</div>
        </div>
      </div>

      <div className="card">
        <div className="page-header">
          <h2 className="section-title">Recent deliveries</h2>
          <p>Newest deliveries across all endpoints.</p>
        </div>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Status</th>
                <th>Event</th>
                <th>Endpoint</th>
                <th>Attempts</th>
              </tr>
            </thead>
            <tbody>
              {recentDeliveries.map((delivery) => (
                <tr key={delivery.id}>
                  <td>
                    <span className={`badge ${delivery.status}`}>{delivery.status}</span>
                  </td>
                  <td>
                    <Link href={`/deliveries/${delivery.id}`}>{delivery.event_type}</Link>
                  </td>
                  <td>{delivery.endpoint_name}</td>
                  <td>{delivery.total_attempts}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
