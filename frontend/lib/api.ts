import {
  DeliveryDetail,
  DeliveryListItem,
  Endpoint,
  EndpointStats,
} from "./types";

function getBaseApiUrl(): string {
  if (typeof window === "undefined") {
    return process.env.INTERNAL_API_URL ?? process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
  }
  return process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
}

async function parseResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `Request failed with status ${response.status}`);
  }
  return response.json() as Promise<T>;
}

export async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${getBaseApiUrl()}${path}`, {
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
  return getBaseApiUrl();
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
