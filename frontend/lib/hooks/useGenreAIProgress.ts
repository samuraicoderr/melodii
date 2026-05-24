import { useEffect, useRef, useState } from "react";

type TerminalLine = {
  id: string;
  timestamp: string;
  level: string;
  message: string;
};

type ProgressCheckpoint = {
  pattern: RegExp;
  progressPercent: number;
  label: string;
  // Approximate real-world duration to reach the NEXT checkpoint (ms).
  // Used to pace the fake crawl so it feels proportionally realistic.
  durationToNextMs: number;
};

// Timing reference (from real run):
//   0s  → Uploading (0%)
//   8s  → Job queued (16.67%)
//   8s  → Live log stream connected  (same moment, skip — subsumed)
//   8s  → Loading model (16.67%)
//  34s  → Running genre classification (70.83%)
//  48s  → Top prediction / Complete (100%)
//
// durationToNextMs encodes how long the *real* gap to the next step takes so
// the fake crawl speed is proportional rather than always the same pace.
const PROGRESS_CHECKPOINTS: ProgressCheckpoint[] = [
  {
    pattern: /uploading audio and starting job/i,
    progressPercent: 0,
    label: "Uploading…",
    durationToNextMs: 8_000,
  },
  {
    // UUID is hex, not purely numeric — use a broad word-boundary match.
    pattern: /job\s+\S+\s+queued/i,
    progressPercent: 0.1667,
    label: "Job queued",
    durationToNextMs: 1_000, // live log connects almost instantly after
  },
  {
    pattern: /live log stream connected/i,
    progressPercent: 0.1667,
    label: "Loading model…",
    durationToNextMs: 26_000, // ~26 s until classification starts
  },
  {
    pattern: /loading model/i,
    progressPercent: 0.1667,
    label: "Loading model…",
    durationToNextMs: 26_000,
  },
  {
    pattern: /running genre classification/i,
    progressPercent: 0.7083,
    label: "Classifying…",
    durationToNextMs: 14_000, // ~14 s until top prediction
  },
  {
    pattern: /top prediction/i,
    progressPercent: 1,
    label: "Complete ✓",
    durationToNextMs: 0,
  },
];

/** Return the index of the latest checkpoint whose pattern appears in logs. */
function latestCheckpointIndex(lines: TerminalLine[]): number {
  const messages = lines.map((l) => l.message);
  for (let i = PROGRESS_CHECKPOINTS.length - 1; i >= 0; i--) {
    if (messages.some((m) => PROGRESS_CHECKPOINTS[i].pattern.test(m))) {
      return i;
    }
  }
  return -1;
}

export function useGenreAIProgress(
  terminalLines: TerminalLine[],
  /** How far into the gap to the NEXT checkpoint to crawl before pausing. 0.5 = halfway. */
  stopPercentage: number = 0.5
) {
  // The actual displayed progress (0–1), animated every rAF tick.
  const [displayProgress, setDisplayProgress] = useState(0);
  const [checkpointLabel, setCheckpointLabel] = useState<string | null>(null);

  // We drive everything through a ref-based "crawl state" so the rAF loop
  // always reads fresh values without needing to be re-created.
  const crawlRef = useRef<{
    // Where the bar currently is (mirrored from state for rAF reads).
    current: number;
    // The hard floor: never go below this (the last confirmed checkpoint).
    floor: number;
    // The soft ceiling: crawl stops here unless a new checkpoint unlocks more.
    ceiling: number;
    // Speed: progress-units per millisecond for the fake crawl phase.
    crawlSpeed: number;
    // Timestamp of the last rAF call (for delta-time animation).
    lastTs: number | null;
  }>({
    current: 0,
    floor: 0,
    ceiling: 0,
    crawlSpeed: 0,
    lastTs: null,
  });

  // Re-evaluate whenever terminal lines change.
  useEffect(() => {
    const idx = latestCheckpointIndex(terminalLines);

    if (idx === -1) {
      // Nothing matched yet — reset quietly.
      crawlRef.current.floor = 0;
      crawlRef.current.ceiling = 0;
      crawlRef.current.crawlSpeed = 0;
      setCheckpointLabel(null);
      return;
    }

    const cp = PROGRESS_CHECKPOINTS[idx];
    const nextCp =
      idx < PROGRESS_CHECKPOINTS.length - 1
        ? PROGRESS_CHECKPOINTS[idx + 1]
        : null;

    // The new floor is the checkpoint we just hit.
    const floor = cp.progressPercent;

    // If we're at the final checkpoint snap to 100 % immediately.
    if (!nextCp) {
      crawlRef.current.floor = 1;
      crawlRef.current.ceiling = 1;
      crawlRef.current.crawlSpeed = 0;
      setCheckpointLabel(cp.label);
      return;
    }

    // Soft ceiling = floor + stopPercentage * gap_to_next
    const gap = nextCp.progressPercent - floor;
    const ceiling = floor + gap * stopPercentage;

    // Speed: we want to travel from `floor` to `ceiling` in
    // `durationToNextMs * stopPercentage` ms — i.e., at a pace that looks
    // realistic relative to the known real-world duration of this step.
    const travelMs = cp.durationToNextMs * stopPercentage;
    const crawlSpeed = travelMs > 0 ? (ceiling - floor) / travelMs : 0;

    // Only advance the floor; never allow it to go backwards.
    if (floor > crawlRef.current.floor) {
      crawlRef.current.floor = floor;
      // If the bar is behind the new floor, snap it up instantly.
      if (crawlRef.current.current < floor) {
        crawlRef.current.current = floor;
        setDisplayProgress(floor);
      }
    }

    // Raise the ceiling (never lower it — prevents stuttering).
    if (ceiling > crawlRef.current.ceiling) {
      crawlRef.current.ceiling = ceiling;
    }

    crawlRef.current.crawlSpeed = crawlSpeed;
    setCheckpointLabel(cp.label);
  }, [terminalLines, stopPercentage]);

  // rAF loop — runs continuously, drives the smooth crawl.
  useEffect(() => {
    let rafId: number;

    const tick = (ts: number) => {
      const state = crawlRef.current;
      const dt = state.lastTs !== null ? ts - state.lastTs : 0;
      state.lastTs = ts;

      const { current, ceiling, crawlSpeed } = state;

      if (current < ceiling && crawlSpeed > 0) {
        const next = Math.min(current + crawlSpeed * dt, ceiling);
        state.current = next;
        setDisplayProgress(next);
      } else if (current < state.floor) {
        // Snap-up for checkpoint jumps (already handled above, but safety net).
        state.current = state.floor;
        setDisplayProgress(state.floor);
      }

      rafId = requestAnimationFrame(tick);
    };

    rafId = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(rafId);
  }, []); // intentionally empty — the loop runs for the component lifetime

  return {
    currentProgress: displayProgress,
    checkpointReached: checkpointLabel,
  };
}