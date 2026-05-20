"use client";

import { useMemo, useState } from "react";
import GenreAIService from "@/lib/api/services/GenreAI.Service";
import type { GenreClassificationResponse } from "@/lib/api/types";

const MAX_FILE_MB = 30;
const ALLOWED_EXTENSIONS = ["mp3", "wav", "ogg", "flac", "m4a"];
const MODEL_OPTIONS = [
  {
    id: "dima806/music_genres_classification",
    label: "HF Base Model",
    enabled: true,
    detail: "dima806/music_genres_classification",
  },
  {
    id: "custom-cnn",
    label: "Custom CNN",
    enabled: false,
    detail: "Unavailable in V2",
  },
  {
    id: "random-forest",
    label: "Random Forest",
    enabled: false,
    detail: "Unavailable in V2",
  },
];

export default function Home() {
  const [selectedModel, setSelectedModel] = useState(MODEL_OPTIONS[0].id);
  const [file, setFile] = useState<File | null>(null);
  const [dragActive, setDragActive] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<GenreClassificationResponse | null>(null);

  const selectedModelLabel = useMemo(() => {
    return MODEL_OPTIONS.find((model) => model.id === selectedModel)?.label ?? "";
  }, [selectedModel]);

  const formatPercent = (value: number) => `${Math.round(value * 1000) / 10}%`;

  const validateFile = (candidate: File): string | null => {
    const extension = candidate.name.split(".").pop()?.toLowerCase() ?? "";
    if (!ALLOWED_EXTENSIONS.includes(extension)) {
      return "Unsupported file type. Please upload mp3, wav, ogg, flac, or m4a.";
    }
    if (candidate.size > MAX_FILE_MB * 1024 * 1024) {
      return "File is too large. Max size is 30MB.";
    }
    return null;
  };

  const handleFilePick = (candidate: File | null) => {
    if (!candidate) {
      return;
    }
    const validationError = validateFile(candidate);
    if (validationError) {
      setError(validationError);
      setFile(null);
      setResult(null);
      return;
    }

    setError(null);
    setFile(candidate);
    setResult(null);
  };

  const handleSubmit = async () => {
    if (!file) {
      setError("Please select an audio file first.");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await GenreAIService.classify(file, selectedModel);
      setResult(response);
    } catch (err: any) {
      setError(err?.message ?? "Something went wrong. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setFile(null);
    setResult(null);
    setError(null);
  };

  return (
    <div className="flex flex-1 flex-col items-center px-6 py-12 md:px-12">
      <div className="w-full max-w-5xl space-y-8 page-intro">
        <header className="flex flex-col gap-4">
          <p className="uppercase tracking-[0.35em] text-xs text-[var(--muted)]">
            Melodii Studio
          </p>
          <h1 className="text-4xl font-semibold text-white md:text-6xl font-display">
            Hear your track. See the genre.
          </h1>
          <p className="max-w-2xl text-base text-[var(--muted)] md:text-lg">
            Upload an audio file and get instant predictions from our best model. V1
            uses a trusted Hugging Face classifier while we train the custom stack.
          </p>
        </header>

        <section className="grid gap-6 lg:grid-cols-[1.2fr_1fr]">
          <div className="glass-panel neon-ring rounded-3xl p-6 md:p-8 space-y-6">
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <h2 className="text-lg font-semibold">Model Selection</h2>
                <span className="text-xs text-[var(--muted)]">V1 only</span>
              </div>
              <div className="grid gap-3">
                {MODEL_OPTIONS.map((model, index) => {
                  const isSelected = model.id === selectedModel;
                  return (
                    <button
                      key={model.id}
                      type="button"
                      title={
                        model.enabled
                          ? "Ready now"
                          : "This model will be available in V2 after training and integration."
                      }
                      onClick={() => model.enabled && setSelectedModel(model.id)}
                      className={`rounded-2xl border px-4 py-3 text-left transition-all ${
                        model.enabled
                          ? "border-white/10 hover:border-[var(--accent)]/60"
                          : "border-white/5 opacity-50 cursor-not-allowed"
                      } ${
                        isSelected
                          ? "bg-white/5 border-[var(--accent)]/70"
                          : "bg-transparent"
                      }`}
                      style={{
                        animationDelay: `${index * 110}ms`,
                      }}
                    >
                      <p className="text-sm font-semibold text-white">{model.label}</p>
                      <p className="text-xs text-[var(--muted)]">{model.detail}</p>
                    </button>
                  );
                })}
              </div>
              <p className="text-xs text-[var(--muted)]">
                Selected: <span className="text-white">{selectedModelLabel}</span>
              </p>
            </div>

            <div className="space-y-4">
              <div
                className={`rounded-2xl border-2 border-dashed px-6 py-10 text-center transition-colors ${
                  dragActive
                    ? "border-[var(--accent)] bg-[var(--accent)]/10"
                    : "border-white/10 bg-white/5"
                }`}
                onDragOver={(event) => {
                  event.preventDefault();
                  setDragActive(true);
                }}
                onDragLeave={() => setDragActive(false)}
                onDrop={(event) => {
                  event.preventDefault();
                  setDragActive(false);
                  handleFilePick(event.dataTransfer.files?.[0] ?? null);
                }}
              >
                <p className="text-base font-semibold text-white">
                  Drag and drop your audio
                </p>
                <p className="mt-2 text-sm text-[var(--muted)]">
                  mp3, wav, ogg, flac, m4a up to 30MB
                </p>
                <label className="mt-5 inline-flex cursor-pointer items-center justify-center rounded-full border border-white/15 px-5 py-2 text-sm font-semibold text-white transition hover:border-[var(--accent)]/70">
                  Browse files
                  <input
                    type="file"
                    accept={ALLOWED_EXTENSIONS.map((ext) => `.${ext}`).join(",")}
                    className="hidden"
                    onChange={(event) => handleFilePick(event.target.files?.[0] ?? null)}
                  />
                </label>
              </div>

              {file && (
                <div className="rounded-2xl border border-white/10 bg-black/40 px-4 py-3 text-sm text-[var(--muted)]">
                  <span className="text-white">{file.name}</span> ·{" "}
                  {Math.round((file.size / 1024 / 1024) * 10) / 10}MB
                </div>
              )}

              {error && (
                <div className="rounded-2xl border border-red-400/30 bg-red-500/10 px-4 py-3 text-sm text-[var(--danger)]">
                  {error}
                </div>
              )}

              <div className="flex flex-col gap-3 md:flex-row">
                <button
                  type="button"
                  onClick={handleSubmit}
                  disabled={loading}
                  className={`flex-1 rounded-full px-6 py-3 text-sm font-semibold text-black transition ${
                    loading
                      ? "bg-[var(--accent)]/60 cursor-wait"
                      : "bg-[var(--accent)] hover:bg-[var(--accent-strong)]"
                  }`}
                >
                  {loading ? "Analyzing..." : "Classify Genre"}
                </button>
                <button
                  type="button"
                  onClick={handleReset}
                  className="rounded-full border border-white/15 px-6 py-3 text-sm font-semibold text-white transition hover:border-white/40"
                >
                  Reset
                </button>
              </div>

              {loading && (
                <div className="loading-bar h-2 w-full rounded-full bg-white/10" />
              )}
            </div>
          </div>

          <div className="glass-panel rounded-3xl p-6 md:p-8 space-y-6">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold">Results</h2>
              <span className="text-xs text-[var(--muted)]">Top 5</span>
            </div>

            {!result && (
              <div className="rounded-2xl border border-white/10 bg-white/5 px-5 py-6 text-sm text-[var(--muted)]">
                Upload a track to see predictions. Results will appear here with
                confidence scores.
              </div>
            )}

            {result && (
              <div className="space-y-6">
                <div className="rounded-3xl bg-gradient-to-br from-[var(--accent)]/15 to-transparent p-6">
                  <p className="text-xs uppercase tracking-[0.3em] text-[var(--muted)]">
                    Top Match
                  </p>
                  <p className="mt-2 text-3xl font-semibold text-white">
                    {result.top_prediction.label}
                  </p>
                  <p className="mt-1 text-lg text-[var(--accent)]">
                    {formatPercent(result.top_prediction.score)} confidence
                  </p>
                </div>

                <div className="space-y-3">
                  {result.predictions.map((prediction, index) => (
                    <div
                      key={`${prediction.label}-${index}`}
                      className="flex items-center justify-between rounded-2xl border border-white/10 bg-black/30 px-4 py-3"
                    >
                      <div>
                        <p className="text-sm font-semibold text-white">
                          {prediction.label}
                        </p>
                        <p className="text-xs text-[var(--muted)]">Rank {index + 1}</p>
                      </div>
                      <div className="text-sm text-[var(--accent)]">
                        {formatPercent(prediction.score)}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </section>
      </div>
    </div>
  );
}
