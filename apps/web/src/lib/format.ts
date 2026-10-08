export function formatDuration(totalSeconds: number): string {
  const total = Math.max(0, Math.round(totalSeconds));
  const minutes = String(Math.floor(total / 60));
  const seconds = String(total % 60).padStart(2, "0");
  return `${minutes}:${seconds}`;
}

export function formatTrackCount(count: number): string {
  const n = count % 100;
  const m = count % 10;
  const text = String(count);
  if (n >= 11 && n <= 14) return `${text} треков`;
  if (m === 1) return `${text} трек`;
  if (m >= 2 && m <= 4) return `${text} трека`;
  return `${text} треков`;
}
