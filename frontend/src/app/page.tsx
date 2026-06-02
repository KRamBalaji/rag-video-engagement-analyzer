// frontend/src/app/page.tsx
"use client";

import { useState } from "react";

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";

type VideoInfo = {
  url: string;
  platform: string;
  video_id: string | null;
  title: string | null;
  creator: string | null;
  views: number | null;
  likes: number | null;
  comments: number | null;
  engagement_rate: number | null;
  follower_count: number | null;
  hashtags: string[] | null;
  upload_date: string | null;
  duration_seconds: number | null;
  duration: string | null;
  transcript: string | null;
  thumbnail_url: string | null;
};

type ProcessVideosResponse = {
  video_a: VideoInfo;
  video_b: VideoInfo;
  message: string;
};

export default function Home() {
  const [videoAUrl, setVideoAUrl] = useState("");
  const [videoBUrl, setVideoBUrl] = useState("");
  const [videoData, setVideoData] = useState<ProcessVideosResponse | null>(
    null
  );
  const [rawResponse, setRawResponse] = useState<string | null>(null);
  const [loadingAnalyze, setLoadingAnalyze] = useState(false);
  const [analyzeError, setAnalyzeError] = useState<string | null>(null);

  const [chatMessages, setChatMessages] = useState<{ role: "user" | "assistant"; content: string }[]>([]);
  const [chatInput, setChatInput] = useState("");
  const [chatLoading, setChatLoading] = useState(false);
  const [chatError, setChatError] = useState<string | null>(null);
  const [sessionId] = useState<string>(() => crypto.randomUUID());

  const handleAnalyzeSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoadingAnalyze(true);
    setAnalyzeError(null);
    setVideoData(null);

    try {
      const res = await fetch(`${BACKEND_URL}/api/process_videos`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          video_a_url: videoAUrl,
          video_b_url: videoBUrl,
        }),
      });

      if (!res.ok) {
        const text = await res.text();
        throw new Error(
          `Request failed with status ${res.status}: ${text || "no body"}`
        );
      }

      const data = await res.json();
      setVideoData(data);
      setRawResponse(JSON.stringify(data, null, 2));

      // Reset chat when a new pair of videos is analyzed
      setChatMessages([]);
      setChatError(null);
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : "Something went wrong while analyzing.";
      setAnalyzeError(errorMessage);
    } finally {
      setLoadingAnalyze(false);
    }
  };

  const handleChatSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!chatInput.trim()) return;

    const userMessage = chatInput.trim();
    setChatInput("");
    setChatLoading(true);
    setChatError(null);

    setChatMessages((prev) => [...prev, { role: "user", content: userMessage }]);

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
        const text = await res.text();
        throw new Error(
          `Chat request failed: ${res.status} ${text || "no body"}`
        );
      }

      const data = await res.json();
      setChatMessages((prev) => [
        ...prev,
        { role: "assistant", content: data.answer },
      ]);
      // data.citations is available if you want to render them later
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Something went wrong in chat.";
      setChatError(msg);
      setChatMessages((prev) => [
        ...prev,
        { role: "assistant", content: `Error: ${msg}` },
      ]);
    } finally {
      setChatLoading(false);
    }
  };

  const renderVideoCard = (label: "A" | "B", video: VideoInfo) => (
    <div className="border rounded p-3 bg-white">
      <h3 className="font-semibold mb-1">Video {label}</h3>
      {video.thumbnail_url && (
        // eslint-disable-next-line @next/next/no-img-element
        <img
          src={video.thumbnail_url}
          alt={video.title || `Video ${label} thumbnail`}
          className="w-full h-auto mb-2 rounded"
        />
      )}
      <p className="text-sm font-medium">
        {video.title || "Untitled"}
      </p>
      <p className="text-xs text-gray-600">
        {video.creator || "Unknown creator"}
      </p>
      <p className="text-xs mt-1">
        Platform: {video.platform || "N/A"}
      </p>
      <p className="text-xs mt-1">
        Views: {video.views ?? "–"} · Likes: {video.likes ?? "–"} · Comments:{" "}
        {video.comments ?? "–"}
      </p>
      <p className="text-xs">
        Engagement:{" "}
        {video.engagement_rate != null
          ? `${video.engagement_rate.toFixed(2)}%`
          : "N/A"}
      </p>
      <p className="text-xs">
        Duration: {video.duration || "N/A"}
      </p>
      <p className="text-xs">
        Uploaded: {video.upload_date || "N/A"}
      </p>
      {video.hashtags && video.hashtags.length > 0 && (
        <p className="text-xs mt-1">
          Hashtags:{" "}
          {video.hashtags
            .filter(Boolean)
            .slice(0, 5)
            .join(" ")}
        </p>
      )}
    </div>
  );

  return (
    <main className="min-h-screen flex flex-col items-center justify-start p-4 bg-gray-50">
      <h1 className="text-2xl font-bold mb-4">
        RAG Video Engagement Analyzer
      </h1>

      {/* Analyze form */}
      <section className="w-full max-w-xl bg-white shadow-sm rounded p-4 mb-6">
        <form onSubmit={handleAnalyzeSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-1">
              Video A URL (YouTube or Instagram)
            </label>
            <input
              type="url"
              value={videoAUrl}
              onChange={(e) => setVideoAUrl(e.target.value)}
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
              value={videoBUrl}
              onChange={(e) => setVideoBUrl(e.target.value)}
              className="w-full border rounded px-3 py-2"
              placeholder="https://www.instagram.com/reel/..."
              required
            />
          </div>

          <button
            type="submit"
            disabled={loadingAnalyze}
            className="w-full bg-black text-white py-2 rounded disabled:opacity-60"
          >
            {loadingAnalyze ? "Analyzing..." : "Analyze"}
          </button>
        </form>

        {analyzeError && (
          <p className="mt-4 text-red-600 text-sm">
            Error: {analyzeError}
          </p>
        )}

        {rawResponse && (
          <details className="mt-4">
            <summary className="text-sm text-gray-700 cursor-pointer">
              Debug JSON response
            </summary>
            <pre className="mt-2 w-full bg-gray-100 p-3 rounded text-xs overflow-auto">
{rawResponse}
            </pre>
          </details>
        )}
      </section>

      {/* Side-by-side video cards */}
      {videoData && (
        <section className="w-full max-w-4xl grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
          {renderVideoCard("A", videoData.video_a)}
          {renderVideoCard("B", videoData.video_b)}
        </section>
      )}

      {/* Chat panel */}
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
              className={`mb-2 ${
                m.role === "user" ? "text-right" : "text-left"
              }`}
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

        {chatError && (
          <p className="mb-2 text-xs text-red-600">
            Chat error: {chatError}
          </p>
        )}

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