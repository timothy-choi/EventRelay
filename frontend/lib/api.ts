import {
  DeliveryDetail,
  DeliveryListItem,
  Endpoint,
  EndpointStats,
  TestWebhookReceiver,
  TestWebhookRequest,
} from "./types";

export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

export default API_BASE_URL;

export function apiUrl(path: string): string {
  const normalizedPath = path.startsWith("/") ? path : `/${path}`;
  return `${API_BASE_URL}${normalizedPath}`;
}

async function parseResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `Request failed with status ${response.status}`);
  }
  return response.json() as Promise<T>;
}

export async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(apiUrl(path), {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
    cache: "no-store",
  });
  return parseResponse<T>(response);
}

export function getApiUrl(): string {
  return API_BASE_URL;
}

export async function getEndpoints(): Promise<Endpoint[]> {
  return apiFetch<Endpoint[]>("/endpoints");
}

export async function getEndpointStats(endpointId: string): Promise<EndpointStats> {
  return apiFetch<EndpointStats>(`/endpoints/${endpointId}/stats`);
}

export async function getDeliveries(): Promise<DeliveryListItem[]> {
  return apiFetch<DeliveryListItem[]>("/deliveries");
}

export async function getDelivery(deliveryId: string): Promise<DeliveryDetail> {
  return apiFetch<DeliveryDetail>(`/deliveries/${deliveryId}`);
}

export async function getTestWebhookReceivers(): Promise<TestWebhookReceiver[]> {
  return apiFetch<TestWebhookReceiver[]>("/test-webhooks");
}

export async function getTestWebhookRequests(receiverId: string): Promise<TestWebhookRequest[]> {
  return apiFetch<TestWebhookRequest[]>(`/test-webhooks/${receiverId}/requests`);
}
