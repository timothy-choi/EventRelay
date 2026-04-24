import Link from "next/link";
import { AutoRefresh } from "../components/AutoRefresh";
import { getDeliveries, getEndpoints } from "../lib/api";

export default async function DashboardHome() {
  try {
    const [endpoints, deliveries] = await Promise.all([getEndpoints(), getDeliveries()]);
    const succeeded = deliveries.filter((delivery) => delivery.status === "succeeded").length;
    const failed = deliveries.filter((delivery) => delivery.status === "failed").length;
    const recentDeliveries = deliveries.slice(0, 5);

    return (
      <div className="stack">
        <div className="page-header">
          <h1>Dashboard</h1>
          <p>Watch endpoint volume, recent delivery activity, and reliability at a glance.</p>
        </div>

        <AutoRefresh />

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
  } catch (error) {
    return (
      <div className="stack">
        <div className="page-header">
          <h1>Dashboard</h1>
        </div>
        <div className="error-box">
          {error instanceof Error ? error.message : "Failed to load dashboard."}
        </div>
      </div>
    );
  }
}
