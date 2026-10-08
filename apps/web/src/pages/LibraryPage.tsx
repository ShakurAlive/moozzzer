import { useState } from "react";
import { TrackRow } from "@/components/ui/TrackRow";
import { t } from "@/i18n";
import type { Track } from "@/lib/types";
import { toast } from "@/stores/toast";

const MOCK_TRACKS: Track[] = [
  {
    id: "l1",
    title: "Blinding Lights",
    artist: "The Weeknd",
    album: "After Hours",
    duration: 200,
    coverUrl: null,
    explicit: false,
  },
  {
    id: "l2",
    title: "Sweater Weather",
    artist: "The Neighbourhood",
    album: "I Love You.",
    duration: 244,
    coverUrl: null,
    explicit: false,
  },
  {
    id: "l3",
    title: "HUMBLE.",
    artist: "Kendrick Lamar",
    album: "DAMN.",
    duration: 177,
    coverUrl: null,
    explicit: true,
  },
  {
    id: "l4",
    title: "Midnight City",
    artist: "M83",
    album: "Hurry Up, We're Dreaming",
    duration: 244,
    coverUrl: null,
    explicit: false,
  },
  {
    id: "l5",
    title: "SICKO MODE",
    artist: "Travis Scott",
    album: "ASTROWORLD",
    duration: 312,
    coverUrl: null,
    explicit: true,
  },
];

export function LibraryPage() {
  const [playingId, setPlayingId] = useState<string | null>(null);

  return (
    <section className="space-y-6">
      <h1 className="text-2xl font-bold tracking-tight">{t("page.library.title")}</h1>

      <div className="flex flex-col gap-1">
        {MOCK_TRACKS.map((track) => (
          <TrackRow
            key={track.id}
            track={track}
            isActive={playingId === track.id}
            isPlaying={playingId === track.id}
            onPlay={() => {
              setPlayingId((current) => (current === track.id ? null : track.id));
            }}
            onMenu={() => {
              toast({ title: track.title, description: t("toast.comingSoon") });
            }}
          />
        ))}
      </div>
    </section>
  );
}
