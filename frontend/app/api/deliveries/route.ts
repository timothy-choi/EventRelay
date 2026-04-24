import { getApiUrl } from "../../../lib/api";

export async function GET() {
  const response = await fetch(`${getApiUrl()}/deliveries`, {
    cache: "no-store",
  });

  const text = await response.text();
  return new Response(text, {
    status: response.status,
    headers: {
      "Content-Type": response.headers.get("Content-Type") ?? "application/json",
      "Cache-Control": "no-store",
    },
  });
}
