import { AutoRefresh } from "../../../components/AutoRefresh";
import { ReplayButton } from "../../../components/ReplayButton";
import { getDelivery } from "../../../lib/api";

export default async function DeliveryDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;

  try {
    const delivery = await getDelivery(id);

    return (
      <div className="stack">
        <div className="page-header">
          <h1>Delivery detail</h1>
          <p>{delivery.event_type} for {delivery.endpoint_name}</p>
        </div>

        <AutoRefresh label="Auto-refreshing delivery detail every 5s" />

        <div className="card">
          <div className="grid two">
            <div>
              <div className="muted">Status</div>
              <div>
                <span className={`badge ${delivery.status}`}>{delivery.status}</span>
              </div>
            </div>
            <div>
              <div className="muted">Attempts</div>
              <div>{delivery.total_attempts}</div>
            </div>
            <div>
              <div className="muted">Last error</div>
              <div>{delivery.last_error ?? "n/a"}</div>
            </div>
            <div>
              <div className="muted">Next retry</div>
              <div>{delivery.next_retry_at ?? "n/a"}</div>
            </div>
          </div>
        </div>

        <div className="card">
          <h2 className="section-title">Event payload</h2>
          <pre>{JSON.stringify(delivery.event_payload, null, 2)}</pre>
        </div>

        <div className="card">
          <div className="page-header">
            <h2 className="section-title">Delivery attempts</h2>
            <p>Attempt-level latency and failure details.</p>
          </div>
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>#</th>
                  <th>Status</th>
                  <th>Response</th>
                  <th>Latency</th>
                  <th>Failure type</th>
                  <th>Error</th>
                </tr>
              </thead>
              <tbody>
                {delivery.attempts.map((attempt) => (
                  <tr key={attempt.id}>
                    <td>{attempt.attempt_number}</td>
                    <td>{attempt.status}</td>
                    <td>{attempt.response_code ?? "n/a"}</td>
                    <td>{attempt.latency_ms === null ? "n/a" : `${attempt.latency_ms} ms`}</td>
                    <td>{attempt.failure_type ?? "n/a"}</td>
                    <td>{attempt.error_message ?? "n/a"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        <ReplayButton deliveryId={delivery.id} />
      </div>
    );
  } catch (error) {
    return (
      <div className="stack">
        <div className="page-header">
          <h1>Delivery detail</h1>
        </div>
        <div className="error-box">
          {error instanceof Error ? error.message : "Failed to load delivery detail."}
        </div>
      </div>
    );
  }
}
