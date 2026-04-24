"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import DashboardCharts from "../components/DashboardCharts";
import { DATA_CHANGED_EVENT } from "../lib/refresh";
import { DeliveryListItem, Endpoint, EndpointStats, SystemStats } from "../lib/types";

type DashboardData = {
  endpoints: Endpoint[];
  deliveries: DeliveryListItem[];
  endpointStats: EndpointStats[];
  systemStats: SystemStats | null;
};

async function fetchDashboardData(): Promise<DashboardData> {
  const [endpointsResponse, deliveriesResponse, systemStatsResponse] = await Promise.all([
    fetch("/api/endpoints", { cache: "no-store" }),
    fetch("/api/deliveries", { cache: "no-store" }),
    fetch("/api/system/stats", { cache: "no-store" }),
  ]);

  if (!endpointsResponse.ok) {
    throw new Error(await endpointsResponse.text());
  }
  if (!deliveriesResponse.ok) {
    throw new Error(await deliveriesResponse.text());
  }
  if (!systemStatsResponse.ok) {
    throw new Error(await systemStatsResponse.text());
  }

  const endpoints = (await endpointsResponse.json()) as Endpoint[];
  const deliveries = ((await deliveriesResponse.json()) as DeliveryListItem[]).sort(
    (left, right) => new Date(right.created_at).getTime() - new Date(left.created_at).getTime(),
  );
  const systemStats = (await systemStatsResponse.json()) as SystemStats;
  const endpointStatsResponses = await Promise.all(
    endpoints.map(async (endpoint) => {
      const response = await fetch(`/api/endpoints/${endpoint.id}/stats`, { cache: "no-store" });
      if (!response.ok) {
        throw new Error(await response.text());
      }
      return (await response.json()) as EndpointStats;
    }),
  );

  return { endpoints, deliveries, endpointStats: endpointStatsResponses, systemStats };
}

function formatTimestamp(timestamp: string): string {
  return new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  }).format(new Date(timestamp));
}

function getDeliveriesOverTime(deliveries: DeliveryListItem[], windowMinutes = 12): Array<{ minute: string; count: number }> {
  const now = Date.now();
  const start = now - windowMinutes * 60 * 1000;
  const counts = new Map<string, number>();

  for (let index = 0; index < windowMinutes; index += 1) {
    const bucket = new Date(start + index * 60 * 1000);
    const key = bucket.toISOString().slice(0, 16);
    counts.set(key, 0);
  }

  deliveries.forEach((delivery) => {
    const createdAt = new Date(delivery.created_at);
    if (createdAt.getTime() < start) {
      return;
    }

    createdAt.setSeconds(0, 0);
    const key = createdAt.toISOString().slice(0, 16);
    counts.set(key, (counts.get(key) ?? 0) + 1);
  });

  return Array.from(counts.entries()).map(([minute, count]) => ({
    minute: new Intl.DateTimeFormat("en-US", { hour: "numeric", minute: "2-digit" }).format(new Date(minute)),
    count,
  }));
}

export default function DashboardHome() {
  const [endpoints, setEndpoints] = useState<Endpoint[]>([]);
  const [deliveries, setDeliveries] = useState<DeliveryListItem[]>([]);
  const [endpointStats, setEndpointStats] = useState<EndpointStats[]>([]);
  const [systemStats, setSystemStats] = useState<SystemStats | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;

    async function load() {
      try {
        if (active) {
          setLoading(true);
        }
        setError(null);
        const data = await fetchDashboardData();
        if (active) {
          setEndpoints(data.endpoints);
          setDeliveries(data.deliveries);
          setEndpointStats(data.endpointStats);
          setSystemStats(data.systemStats);
        }
      } catch (err) {
        if (active) {
          setError(err instanceof Error ? err.message : "Failed to load dashboard.");
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
  const retrying = deliveries.filter((delivery) => delivery.status === "retrying").length;
  const recentDeliveries = deliveries.slice(0, 5);
  const deliveriesOverTime = getDeliveriesOverTime(deliveries);

  return (
    <div className="stack">
      <div className="page-header">
        <h1>Dashboard</h1>
        <p>Watch endpoint volume, recent delivery activity, and reliability at a glance.</p>
      </div>

      {loading ? <div className="card muted">Loading dashboard charts and recent delivery activity...</div> : null}

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

      <DashboardCharts
        endpointStats={endpointStats}
        statusCounts={{ succeeded, failed, retrying }}
        systemStats={systemStats}
        deliveriesOverTime={deliveriesOverTime}
      />

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
                <th>Created</th>
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
                  <td>{formatTimestamp(delivery.created_at)}</td>
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
