import Link from "next/link";
import { AutoRefresh } from "../../components/AutoRefresh";
import { getDeliveries } from "../../lib/api";

export default async function DeliveriesPage() {
  try {
    const deliveries = await getDeliveries();

    return (
      <div className="stack">
        <div className="page-header">
          <h1>Deliveries</h1>
          <p>Track delivery state, retries, and the most recent error for each event.</p>
        </div>

        <AutoRefresh label="Auto-refreshing deliveries every 5s" />

        <div className="card">
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Status</th>
                  <th>Event</th>
                  <th>Endpoint</th>
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
                    <td>{delivery.total_attempts}</td>
                    <td>{delivery.last_error ?? "n/a"}</td>
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
          <h1>Deliveries</h1>
        </div>
        <div className="error-box">
          {error instanceof Error ? error.message : "Failed to load deliveries."}
        </div>
      </div>
    );
  }
}
