// frontend/src/app/page.tsx
"use client";

import { useState } from "react";

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";

export default function Home() {
  const [videoA, setVideoA] = useState("");
  const [videoB, setVideoB] = useState("");
  const [response, setResponse] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [chatMessages, setChatMessages] = useState<{ role: "user" | "assistant"; content: string }[]>([]);
  const [chatInput, setChatInput] = useState("");
  const [chatLoading, setChatLoading] = useState(false);
  const [sessionId] = useState<string>(() => crypto.randomUUID());

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setResponse(null);

    try {
      const res = await fetch(`${BACKEND_URL}/api/process_videos`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          video_a_url: videoA,
          video_b_url: videoB,
        }),
      });

      if (!res.ok) {
        throw new Error(`Request failed with status ${res.status}`);
      }

      const data = await res.json();
      setResponse(JSON.stringify(data, null, 2));
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Something went wrong");
    } finally {
      setLoading(false);
    }
  };

  const handleChatSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!chatInput.trim()) return;

    const userMessage = chatInput.trim();
    setChatMessages((prev) => [...prev, { role: "user", content: userMessage }]);
    setChatInput("");
    setChatLoading(true);

    try {
      const res = await fetch(`${BACKEND_URL}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          session_id: sessionId,
          message: userMessage,
          history: chatMessages.map((m) => ({
            role: m.role,
            content: m.content,
          })),
        }),
      });

      if (!res.ok) {
        throw new Error(`Chat request failed: ${res.status}`);
      }

      const data = await res.json();
      setChatMessages((prev) => [...prev, { role: "assistant", content: data.answer }]);
      // You can also store data.citations if you want to render them
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : "Something went wrong";
      setChatMessages((prev) => [
        ...prev,
        { role: "assistant", content: `Error: ${errorMessage}` },
      ]);
    } finally {
      setChatLoading(false);
    }
  };

  return (
    <main className="min-h-screen flex flex-col items-center justify-start p-4 bg-gray-50">
      <h1 className="text-2xl font-bold mb-4">
        RAG Video Engagement Analyzer
      </h1>

      <section className="w-full max-w-xl bg-white shadow-sm rounded p-4 mb-6">
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-1">
              Video A URL (YouTube or Instagram)
            </label>
            <input
              type="url"
              value={videoA}
              onChange={(e) => setVideoA(e.target.value)}
              className="w-full border rounded px-3 py-2"
              placeholder="https://www.youtube.com/watch?v=..."
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">
              Video B URL (YouTube or Instagram)
            </label>
            <input
              type="url"
              value={videoB}
              onChange={(e) => setVideoB(e.target.value)}
              className="w-full border rounded px-3 py-2"
              placeholder="https://www.instagram.com/reel/..."
              required
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-black text-white py-2 rounded disabled:opacity-60"
          >
            {loading ? "Analyzing..." : "Analyze"}
          </button>
        </form>

        {error && (
          <p className="mt-4 text-red-600 text-sm">
            Error: {error}
          </p>
        )}

        {response && (
          <pre className="mt-4 w-full bg-gray-100 p-3 rounded text-xs overflow-auto">
{response}
          </pre>
        )}
      </section>

      <section className="w-full max-w-2xl bg-white shadow-sm rounded p-4">
        <h2 className="text-xl font-semibold mb-2">
          Chat about Videos A &amp; B
        </h2>

        <div className="h-64 border rounded p-2 mb-2 overflow-y-auto bg-white">
          {chatMessages.length === 0 && (
            <p className="text-sm text-gray-500">
              Ask questions like &quot;Why did Video A get more engagement than Video B?&quot;
            </p>
          )}
          {chatMessages.map((m, idx) => (
            <div
              key={idx}
              className={`mb-2 ${m.role === "user" ? "text-right" : "text-left"}`}
            >
              <span
                className={
                  m.role === "user"
                    ? "inline-block bg-blue-600 text-white px-2 py-1 rounded"
                    : "inline-block bg-gray-200 text-black px-2 py-1 rounded"
                }
              >
                {m.content}
              </span>
            </div>
          ))}
        </div>

        <form onSubmit={handleChatSubmit} className="flex gap-2">
          <input
            type="text"
            className="flex-1 border rounded px-3 py-2"
            placeholder="Ask a question about Videos A & B..."
            value={chatInput}
            onChange={(e) => setChatInput(e.target.value)}
          />
          <button
            type="submit"
            disabled={chatLoading}
            className="bg-black text-white px-4 py-2 rounded disabled:opacity-60"
          >
            {chatLoading ? "Thinking..." : "Send"}
          </button>
        </form>
      </section>
    </main>
  );
}