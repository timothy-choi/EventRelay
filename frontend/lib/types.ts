export type Endpoint = {
  id: string;
  name: string;
  target_url: string;
  is_active: boolean;
  simulation_latency_ms: number;
  simulation_failure_rate: number;
  simulation_timeout_rate: number;
  created_at: string;
};

export type EndpointStats = {
  endpoint_id: string;
  endpoint_name: string;
  total_deliveries: number;
  succeeded: number;
  failed: number;
  retrying: number;
  pending: number;
  success_rate: number;
  avg_latency_ms: number | null;
  p95_latency_ms: number | null;
  total_attempts: number;
  timeout_count: number;
  connection_error_count: number;
  http_4xx_count: number;
  http_5xx_count: number;
};

export type DeliveryListItem = {
  id: string;
  status: string;
  total_attempts: number;
  next_retry_at: string | null;
  last_error: string | null;
  created_at: string;
  updated_at: string;
  endpoint_id: string;
  endpoint_name: string;
  endpoint_target_url: string;
  event_id: string;
  event_type: string;
};

export type DeliveryAttempt = {
  id: string;
  attempt_number: number;
  status: string;
  response_code: number | null;
  latency_ms: number | null;
  failure_type: string | null;
  error_message: string | null;
  started_at: string;
  completed_at: string | null;
};

export type DeliveryDetail = {
  id: string;
  status: string;
  total_attempts: number;
  next_retry_at: string | null;
  last_error: string | null;
  created_at: string;
  updated_at: string;
  endpoint_id: string;
  endpoint_name: string;
  endpoint_target_url: string;
  event_id: string;
  event_type: string;
  event_payload: Record<string, unknown>;
  event_created_at: string;
  attempts: DeliveryAttempt[];
};
