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

  return (
    <main className="min-h-screen flex flex-col items-center justify-center p-4">
      <h1 className="text-2xl font-bold mb-4">RAG Video Engagement Analyzer</h1>

      <form onSubmit={handleSubmit} className="w-full max-w-xl space-y-4">
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
          {loading ? "Sending..." : "Analyze"}
        </button>
      </form>

      {error && (
        <p className="mt-4 text-red-600 text-sm">
          Error: {error}
        </p>
      )}

      {response && (
        <pre className="mt-4 w-full max-w-xl bg-gray-100 p-3 rounded text-xs overflow-auto">
{response}
        </pre>
      )}
    </main>
  );
}