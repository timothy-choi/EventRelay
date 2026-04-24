"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { DeactivateButton } from "../../components/DeactivateButton";
import { Endpoint } from "../../lib/types";
import { DATA_CHANGED_EVENT } from "../../lib/refresh";

async function fetchEndpoints(): Promise<Endpoint[]> {
  const response = await fetch("/api/endpoints", {
    cache: "no-store",
  });
  if (!response.ok) {
    throw new Error(await response.text());
  }
  return response.json() as Promise<Endpoint[]>;
}

export default function EndpointsPage() {
  const [endpoints, setEndpoints] = useState<Endpoint[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;

    async function load() {
      try {
        setError(null);
        const data = await fetchEndpoints();
        if (active) {
          setEndpoints(data);
        }
      } catch (err) {
        if (active) {
          setError(err instanceof Error ? err.message : "Failed to load endpoints.");
        }
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    }

    void load();

    function handleDataChanged() {
      void load();
    }

    window.addEventListener(DATA_CHANGED_EVENT, handleDataChanged);
    return () => {
      active = false;
      window.removeEventListener(DATA_CHANGED_EVENT, handleDataChanged);
    };
  }, []);

  async function handleRefresh() {
    setLoading(true);
    try {
      setEndpoints(await fetchEndpoints());
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load endpoints.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="stack">
      <div className="page-header">
        <h1>Endpoints</h1>
        <p>Inspect endpoint state, simulation config, and drill into reliability metrics.</p>
      </div>

      <div className="refresh-bar">
        <span className="muted">{loading ? "Refreshing endpoints..." : "Endpoint data is live."}</span>
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
                  <th>Name</th>
                  <th>Target URL</th>
                  <th>Active</th>
                  <th>Latency</th>
                  <th>Failure rate</th>
                  <th>Timeout rate</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {endpoints.map((endpoint) => (
                  <tr key={endpoint.id}>
                    <td>
                      <Link href={`/endpoints/${endpoint.id}`}>{endpoint.name}</Link>
                    </td>
                    <td>{endpoint.target_url}</td>
                    <td>{endpoint.is_active ? "Yes" : "No"}</td>
                    <td>{endpoint.simulation_latency_ms} ms</td>
                    <td>{endpoint.simulation_failure_rate}%</td>
                    <td>{endpoint.simulation_timeout_rate}%</td>
                    <td>
                      <DeactivateButton endpointId={endpoint.id} isActive={endpoint.is_active} />
                    </td>
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
