import { AutoRefresh } from "../../components/AutoRefresh";
import { CreateTestWebhookForm } from "../../components/CreateTestWebhookForm";
import { getTestWebhookReceivers, getTestWebhookRequests } from "../../lib/api";

export default async function TestWebhooksPage() {
  try {
    const receivers = await getTestWebhookReceivers();
    const requestsByReceiver = await Promise.all(
      receivers.map(async (receiver) => ({
        receiverId: receiver.id,
        requests: await getTestWebhookRequests(receiver.id),
      })),
    );

    return (
      <div className="stack">
        <div className="page-header">
          <h1>Test Webhooks</h1>
          <p>Create built-in receiver URLs and inspect the exact requests EventRelay delivers.</p>
          <p className="muted">
            Use the generated receiver URL as an endpoint target. In Docker, this may use the internal
            <code> backend </code>
            hostname so the worker can reach it.
          </p>
        </div>

        <AutoRefresh label="Auto-refreshing test webhook requests every 5s" />
        <CreateTestWebhookForm />

        {receivers.map((receiver) => {
          const requestGroup = requestsByReceiver.find((item) => item.receiverId === receiver.id);
          const requests = requestGroup?.requests ?? [];

          return (
            <div key={receiver.id} className="card stack">
              <div className="page-header">
                <h2 className="section-title">{receiver.name}</h2>
                <p>{receiver.url}</p>
              </div>

              {requests.length === 0 ? (
                <p className="muted">No requests received yet.</p>
              ) : (
                requests.map((request) => (
                  <div key={request.id} className="card nested-card">
                    <div className="grid two">
                      <div>
                        <div className="muted">Method</div>
                        <div>{request.method}</div>
                      </div>
                      <div>
                        <div className="muted">Received</div>
                        <div>{request.received_at}</div>
                      </div>
                    </div>
                    <div className="stack">
                      <div>
                        <div className="muted">Headers</div>
                        <pre>{JSON.stringify(request.headers, null, 2)}</pre>
                      </div>
                      <div>
                        <div className="muted">Body</div>
                        <pre>{JSON.stringify(request.body ?? request.raw_body, null, 2)}</pre>
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>
          );
        })}
      </div>
    );
  } catch (error) {
    return (
      <div className="stack">
        <div className="page-header">
          <h1>Test Webhooks</h1>
        </div>
        <div className="error-box">
          {error instanceof Error ? error.message : "Failed to load test webhooks."}
        </div>
      </div>
    );
  }
}
