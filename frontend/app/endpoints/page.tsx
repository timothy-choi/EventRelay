import Link from "next/link";
import { DeactivateButton } from "../../components/DeactivateButton";
import { getEndpoints } from "../../lib/api";

export default async function EndpointsPage() {
  try {
    const endpoints = await getEndpoints();

    return (
      <div className="stack">
        <div className="page-header">
          <h1>Endpoints</h1>
          <p>Inspect endpoint state, simulation config, and drill into reliability metrics.</p>
        </div>

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
      </div>
    );
  } catch (error) {
    return (
      <div className="stack">
        <div className="page-header">
          <h1>Endpoints</h1>
        </div>
        <div className="error-box">
          {error instanceof Error ? error.message : "Failed to load endpoints."}
        </div>
      </div>
    );
  }
}
