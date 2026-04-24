import { AutoRefresh } from "../../../components/AutoRefresh";
import { getEndpointStats, getEndpoints } from "../../../lib/api";

export default async function EndpointDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;

  try {
    const [endpoints, stats] = await Promise.all([getEndpoints(), getEndpointStats(id)]);
    const endpoint = endpoints.find((item) => item.id === id);

    return (
      <div className="stack">
        <div className="page-header">
          <h1>{stats.endpoint_name}</h1>
          <p>Endpoint configuration and reliability metrics.</p>
        </div>

        <AutoRefresh label="Auto-refreshing endpoint stats every 5s" />

        {endpoint ? (
          <div className="card">
            <div className="grid two">
              <div>
                <div className="muted">Target URL</div>
                <div>{endpoint.target_url}</div>
              </div>
              <div>
                <div className="muted">Active</div>
                <div>{endpoint.is_active ? "Yes" : "No"}</div>
              </div>
              <div>
                <div className="muted">Simulation latency</div>
                <div>{endpoint.simulation_latency_ms} ms</div>
              </div>
              <div>
                <div className="muted">Simulation failure rate</div>
                <div>{endpoint.simulation_failure_rate}%</div>
              </div>
              <div>
                <div className="muted">Simulation timeout rate</div>
                <div>{endpoint.simulation_timeout_rate}%</div>
              </div>
            </div>
          </div>
        ) : null}

        <div className="grid stats">
          <div className="card">
            <div className="muted">Success rate</div>
            <div className="metric">{stats.success_rate.toFixed(1)}%</div>
          </div>
          <div className="card">
            <div className="muted">Average latency</div>
            <div className="metric">
              {stats.avg_latency_ms === null ? "n/a" : `${stats.avg_latency_ms.toFixed(1)} ms`}
            </div>
          </div>
          <div className="card">
            <div className="muted">P95 latency</div>
            <div className="metric">
              {stats.p95_latency_ms === null ? "n/a" : `${stats.p95_latency_ms} ms`}
            </div>
          </div>
        </div>

        <div className="grid two">
          <div className="card">
            <h2 className="section-title">Delivery states</h2>
            <div className="stack muted">
              <div>Total deliveries: {stats.total_deliveries}</div>
              <div>Succeeded: {stats.succeeded}</div>
              <div>Failed: {stats.failed}</div>
              <div>Retrying: {stats.retrying}</div>
              <div>Pending: {stats.pending}</div>
              <div>Total attempts: {stats.total_attempts}</div>
            </div>
          </div>
          <div className="card">
            <h2 className="section-title">Failure counts</h2>
            <div className="stack muted">
              <div>Timeouts: {stats.timeout_count}</div>
              <div>Connection errors: {stats.connection_error_count}</div>
              <div>HTTP 4xx: {stats.http_4xx_count}</div>
              <div>HTTP 5xx: {stats.http_5xx_count}</div>
            </div>
          </div>
        </div>
      </div>
    );
  } catch (error) {
    return (
      <div className="stack">
        <div className="page-header">
          <h1>Endpoint detail</h1>
        </div>
        <div className="error-box">
          {error instanceof Error ? error.message : "Failed to load endpoint detail."}
        </div>
      </div>
    );
  }
}
