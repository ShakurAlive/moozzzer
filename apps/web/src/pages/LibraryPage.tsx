import { Library } from "lucide-react";
import { useEffect, useState } from "react";
import { EmptyState } from "@/components/ui/EmptyState";
import { Skeleton } from "@/components/ui/Skeleton";
import { TrackRow } from "@/components/ui/TrackRow";
import { t } from "@/i18n";
import { listLibrary, removeFromLibrary, trackFromDto } from "@/lib/api";
import type { Track } from "@/lib/types";
import { usePlayerStore } from "@/stores/player";
import { toast } from "@/stores/toast";

export function LibraryPage() {
  const [tracks, setTracks] = useState<Track[]>([]);
  const [loading, setLoading] = useState(true);

  const playQueue = usePlayerStore((state) => state.playQueue);
  const queue = usePlayerStore((state) => state.queue);
  const index = usePlayerStore((state) => state.index);
  const isPlaying = usePlayerStore((state) => state.isPlaying);

  useEffect(() => {
    let cancelled = false;
    void listLibrary()
      .then((data) => {
        if (!cancelled) setTracks(data.map(trackFromDto));
      })
      .catch(() => {
        if (!cancelled) toast({ title: t("library.error"), variant: "error" });
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const handlePlay = (trackIndex: number) => {
    playQueue(tracks, trackIndex);
  };

  const handleRemove = (track: Track) => {
    void removeFromLibrary(track.id)
      .then(() => {
        setTracks((prev) => prev.filter((item) => item.id !== track.id));
        toast({ title: t("library.removed") });
      })
      .catch(() => {
        toast({ title: t("library.error"), variant: "error" });
      });
  };

  return (
    <section className="space-y-6">
      <h1 className="text-2xl font-bold tracking-tight">{t("page.library.title")}</h1>

      {loading ? (
        <div className="flex flex-col gap-2">
          {Array.from({ length: 6 }).map((_, item) => (
            <Skeleton key={item} className="h-14 w-full" />
          ))}
        </div>
      ) : tracks.length === 0 ? (
        <EmptyState
          icon={Library}
          title={t("empty.library.title")}
          description={t("empty.library.description")}
          className="min-h-[50vh] justify-center"
        />
      ) : (
        <div className="flex flex-col gap-1">
          {tracks.map((track, trackIndex) => (
            <TrackRow
              key={track.id}
              track={track}
              isActive={queue[index]?.id === track.id}
              isPlaying={isPlaying && queue[index]?.id === track.id}
              onPlay={() => {
                handlePlay(trackIndex);
              }}
              onMenu={() => {
                handleRemove(track);
              }}
            />
          ))}
        </div>
      )}
    </section>
  );
}
