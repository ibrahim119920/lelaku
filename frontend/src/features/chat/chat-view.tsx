"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { type FormEvent, useEffect, useRef, useState } from "react";

import { ErrorNotice } from "@/components/ui/error-notice";
import { ApiError, apiFetch, jsonBody, toApiError } from "@/lib/api/client";
import type { Message } from "@/lib/api/types";
import { formatDateTime } from "@/lib/format";

const POLL_INTERVAL_MS = 4000;

export default function ChatView() {
  const { tripId } = useParams<{ tripId: string }>();
  const [messages, setMessages] = useState<Message[]>([]);
  const [content, setContent] = useState("");
  const [error, setError] = useState<ApiError | null>(null);
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);
  const lastSentAt = useRef<string | null>(null);

  function merge(incoming: Message[]) {
    if (incoming.length === 0) return;
    setMessages((prev) => {
      const seen = new Set(prev.map((m) => m.message_id));
      const fresh = incoming.filter((m) => !seen.has(m.message_id));
      return fresh.length === 0 ? prev : [...prev, ...fresh];
    });
    lastSentAt.current = incoming[incoming.length - 1].sent_at;
  }

  // Polling (bukan WebSocket): muat awal, lalu tiap beberapa detik minta pesan setelah sent_at terakhir.
  useEffect(() => {
    let cancelled = false;
    let timer: ReturnType<typeof setTimeout> | undefined;

    async function poll() {
      try {
        const params = new URLSearchParams();
        if (lastSentAt.current) params.set("after", lastSentAt.current);
        const query = params.toString();
        const incoming = await apiFetch<Message[]>(
          `/trips/${tripId}/messages${query ? `?${query}` : ""}`,
        );
        if (cancelled) return;
        merge(incoming);
        setError(null);
        setLoading(false);
      } catch (err) {
        if (cancelled) return;
        const apiError = toApiError(err);
        setError(apiError);
        setLoading(false);
        // 401/403/404 tidak akan membaik dengan retry; hentikan polling.
        if ([401, 403, 404].includes(apiError.status)) return;
      }
      timer = setTimeout(poll, POLL_INTERVAL_MS);
    }

    poll();
    return () => {
      cancelled = true;
      if (timer) clearTimeout(timer);
    };
  }, [tripId]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ block: "end" });
  }, [messages.length]);

  async function send(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const text = content.trim();
    if (!text) return;
    setSending(true);
    try {
      const created = await apiFetch<Message>(`/trips/${tripId}/messages`, jsonBody({ content: text }));
      merge([created]);
      setContent("");
      setError(null);
    } catch (err) {
      setError(toApiError(err));
    } finally {
      setSending(false);
    }
  }

  const blocked = error !== null && [401, 403, 404].includes(error.status);

  return (
    <main className="page-shell">
      <section className="card stack">
        <p>
          <Link className="text-link" href={`/trips/${tripId}`}>
            ← Kembali ke perjalanan
          </Link>
        </p>
        <h1>Chat perjalanan</h1>

        {error ? <ErrorNotice error={error} /> : null}
        {loading ? <p className="muted">Memuat pesan…</p> : null}

        <div className="chat-log" aria-live="polite">
          {!loading && !blocked && messages.length === 0 ? (
            <p className="muted">Belum ada pesan. Mulai percakapan!</p>
          ) : null}
          {messages.map((message) => (
            <div className="chat-message" key={message.message_id}>
              <div className="row">
                <strong>{message.sender_name}</strong>
                <span className="muted">{formatDateTime(message.sent_at)}</span>
              </div>
              <p>{message.content}</p>
            </div>
          ))}
          <div ref={bottomRef} />
        </div>

        <form className="stack" onSubmit={send}>
          <div className="field">
            <label htmlFor="message">Pesan</label>
            <textarea
              id="message"
              name="message"
              rows={3}
              maxLength={2000}
              placeholder="Tulis pesan..."
              value={content}
              onChange={(event) => setContent(event.target.value)}
              disabled={blocked}
            />
          </div>
          <button className="button" type="submit" disabled={sending || blocked}>
            {sending ? "Mengirim…" : "Kirim pesan"}
          </button>
        </form>
      </section>
    </main>
  );
}
