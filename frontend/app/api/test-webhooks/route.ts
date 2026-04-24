import { getApiUrl } from "../../../lib/api";

export async function POST(request: Request) {
  const body = await request.text()
  const response = await fetch(`${getApiUrl()}/test-webhooks`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body,
    cache: "no-store",
  });

  const text = await response.text();
  return new Response(text, {
    status: response.status,
    headers: {
      "Content-Type": response.headers.get("Content-Type") ?? "application/json",
    },
  });
}
