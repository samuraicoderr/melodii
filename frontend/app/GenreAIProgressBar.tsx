import { useGenreAIProgress } from "@/lib/hooks/useGenreAIProgress";

type TerminalLine = {
  id: string;
  timestamp: string;
  level: string;
  message: string;
};

interface GenreAIProgressBarProps {
  terminalLines: TerminalLine[];
  loading: boolean;
  stopPercentage?: number;
}

export function GenreAIProgressBar({
  terminalLines,
  loading,
  stopPercentage = 0.5,
}: GenreAIProgressBarProps) {
  const { currentProgress, checkpointReached } = useGenreAIProgress(
    terminalLines,
    stopPercentage
  );

  if (!loading && terminalLines.length === 0) {
    return null;
  }

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between text-xs">
        <span className="text-[var(--muted)]">Progress</span>
        <span className="text-[var(--accent)]">
          {checkpointReached ?? "Starting…"}
        </span>
      </div>
      <div className="h-1 w-full rounded-full bg-white/10 overflow-hidden">
        <div
          className="h-full rounded-full bg-gradient-to-r from-[var(--accent)] to-[var(--accent-strong)]"
          style={{
            width: `${Math.min(currentProgress * 100, 100)}%`,
            // No CSS transition — animation is driven entirely by rAF in the
            // hook for smooth, consistent motion regardless of frame rate.
            transition: "none",
          }}
        />
      </div>
      <div className="text-xs text-[var(--muted)]">
        {Math.round(currentProgress * 1000) / 10}% complete
      </div>
    </div>
  );
}