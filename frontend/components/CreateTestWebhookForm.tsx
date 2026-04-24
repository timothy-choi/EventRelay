"use client";

import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";
import { notifyDataChanged } from "../lib/refresh";

export function CreateTestWebhookForm() {
  const router = useRouter();
  const [name, setName] = useState("");
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setPending(true);
    setError(null);

    try {
      const response = await fetch("/api/test-webhooks", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ name }),
      });
      if (!response.ok) {
        throw new Error(await response.text());
      }
      setName("");
      notifyDataChanged();
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create test webhook receiver");
    } finally {
      setPending(false);
    }
  }

  return (
    <form className="card stack" onSubmit={handleSubmit}>
      <div className="page-header">
        <h2 className="section-title">Create test receiver</h2>
        <p>Generate a built-in URL you can use as an EventRelay endpoint target.</p>
      </div>
      <input
        className="text-input"
        value={name}
        onChange={(event) => setName(event.target.value)}
        placeholder="My test receiver"
        required
      />
      <div className="action-stack">
        <button className="button" type="submit" disabled={pending}>
          {pending ? "Creating..." : "Create receiver"}
        </button>
        {error ? <p className="inline-error">{error}</p> : null}
      </div>
    </form>
  );
}
