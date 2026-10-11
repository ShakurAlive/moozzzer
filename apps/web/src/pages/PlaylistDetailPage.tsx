import { GripVertical, ListMusic, Plus, Trash2 } from "lucide-react";
import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { EmptyState } from "@/components/ui/EmptyState";
import { IconButton } from "@/components/ui/IconButton";
import { Skeleton } from "@/components/ui/Skeleton";
import { TrackRow } from "@/components/ui/TrackRow";
import { t } from "@/i18n";
import {
  addPlaylistTrack,
  deletePlaylist,
  getPlaylist,
  listLibrary,
  removePlaylistTrack,
  reorderPlaylist,
  trackFromDto,
} from "@/lib/api";
import { cn } from "@/lib/cn";
import type { Track } from "@/lib/types";
import { usePlayerStore } from "@/stores/player";
import { toast } from "@/stores/toast";

export function PlaylistDetailPage() {
  const { playlistId } = useParams<{ playlistId: string }>();
  const navigate = useNavigate();

  const [name, setName] = useState("");
  const [tracks, setTracks] = useState<Track[]>([]);
  const [library, setLibrary] = useState<Track[]>([]);
  const [loading, setLoading] = useState(true);
  const [draggedId, setDraggedId] = useState<string | null>(null);
  const [dragOverId, setDragOverId] = useState<string | null>(null);

  const playQueue = usePlayerStore((state) => state.playQueue);
  const queue = usePlayerStore((state) => state.queue);
  const index = usePlayerStore((state) => state.index);
  const isPlaying = usePlayerStore((state) => state.isPlaying);

  useEffect(() => {
    if (playlistId === undefined) return;
    let cancelled = false;

    void Promise.all([getPlaylist(playlistId), listLibrary()])
      .then(([playlist, lib]) => {
        if (cancelled) return;
        setName(playlist.name);
        setTracks(playlist.tracks.map(trackFromDto));
        setLibrary(lib.map(trackFromDto));
      })
      .catch(() => {
        if (!cancelled) toast({ title: t("playlist.error"), variant: "error" });
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [playlistId]);

  const available = library.filter((libTrack) => !tracks.some((item) => item.id === libTrack.id));

  const handlePlay = (trackIndex: number) => {
    playQueue(tracks, trackIndex);
  };

  const handleRemove = (track: Track) => {
    if (playlistId === undefined) return;
    void removePlaylistTrack(playlistId, track.id)
      .then(() => {
        setTracks((prev) => prev.filter((item) => item.id !== track.id));
        toast({ title: t("playlist.removed") });
      })
      .catch(() => {
        toast({ title: t("playlist.error"), variant: "error" });
      });
  };

  const handleAdd = (track: Track) => {
    if (playlistId === undefined) return;
    void addPlaylistTrack(playlistId, track.id)
      .then(() => {
        setTracks((prev) => [...prev, track]);
      })
      .catch(() => {
        toast({ title: t("playlist.error"), variant: "error" });
      });
  };

  const handleDrop = (targetId: string) => {
    if (draggedId === null || draggedId === targetId || playlistId === undefined) return;
    const fromIndex = tracks.findIndex((item) => item.id === draggedId);
    const toIndex = tracks.findIndex((item) => item.id === targetId);
    if (fromIndex === -1 || toIndex === -1) return;

    const next = [...tracks];
    const [moved] = next.splice(fromIndex, 1);
    if (moved === undefined) return;
    next.splice(toIndex, 0, moved);
    setTracks(next);

    void reorderPlaylist(
      playlistId,
      next.map((item) => item.id),
    ).catch(() => {
      toast({ title: t("playlist.error"), variant: "error" });
    });
  };

  const handleDelete = () => {
    if (playlistId === undefined) return;
    void deletePlaylist(playlistId)
      .then(() => {
        void navigate("/playlists", { replace: true });
      })
      .catch(() => {
        toast({ title: t("playlist.error"), variant: "error" });
      });
  };

  if (loading) {
    return (
      <section className="space-y-6">
        <Skeleton className="h-8 w-48" />
        <div className="flex flex-col gap-2">
          {Array.from({ length: 5 }).map((_, item) => (
            <Skeleton key={item} className="h-14 w-full" />
          ))}
        </div>
      </section>
    );
  }

  return (
    <section className="space-y-6">
      <div className="flex items-center gap-3">
        <IconButton
          label={t("nav.playlists")}
          onClick={() => {
            void navigate("/playlists");
          }}
        >
          <ListMusic className="size-5" aria-hidden />
        </IconButton>
        <h1 className="min-w-0 flex-1 truncate text-2xl font-bold tracking-tight">{name}</h1>
        <IconButton label={t("playlist.delete")} onClick={handleDelete}>
          <Trash2 className="size-5" aria-hidden />
        </IconButton>
      </div>

      {tracks.length === 0 ? (
        <EmptyState
          icon={ListMusic}
          title={t("empty.playlist.title")}
          description={t("empty.playlist.description")}
          className="min-h-[30vh] justify-center"
        />
      ) : (
        <div className="flex flex-col">
          {tracks.map((track, trackIndex) => (
            <div
              key={track.id}
              className={cn(
                "flex items-center gap-1",
                dragOverId === track.id && draggedId !== track.id && "border-primary border-t-2",
              )}
              onDragOver={(event) => {
                event.preventDefault();
                setDragOverId(track.id);
              }}
              onDragLeave={() => {
                setDragOverId((current) => (current === track.id ? null : current));
              }}
              onDrop={(event) => {
                event.preventDefault();
                handleDrop(track.id);
                setDragOverId(null);
              }}
            >
              <button
                type="button"
                draggable
                aria-label={t("playlist.reorder")}
                onDragStart={(event) => {
                  event.dataTransfer.effectAllowed = "move";
                  setDraggedId(track.id);
                }}
                onDragEnd={() => {
                  setDraggedId(null);
                  setDragOverId(null);
                }}
                className="text-muted-foreground hover:text-foreground cursor-grab rounded-md p-1 transition-colors active:cursor-grabbing"
              >
                <GripVertical className="size-4" aria-hidden />
              </button>
              <div className="min-w-0 flex-1">
                <TrackRow
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
              </div>
            </div>
          ))}
        </div>
      )}

      {available.length > 0 ? (
        <div className="space-y-2">
          <h2 className="text-muted-foreground text-sm font-medium">
            {t("playlist.addFromLibrary")}
          </h2>
          <div className="flex flex-col gap-1">
            {available.map((track) => (
              <div key={track.id} className="group flex items-center gap-3 rounded-md px-2 py-1">
                <div className="min-w-0 flex-1 truncate text-sm">
                  <span className="font-medium">{track.title}</span>
                  <span className="text-muted-foreground"> — {track.artist}</span>
                </div>
                <IconButton
                  label={t("search.addToPlaylist")}
                  onClick={() => {
                    handleAdd(track);
                  }}
                >
                  <Plus className="size-5" aria-hidden />
                </IconButton>
              </div>
            ))}
          </div>
        </div>
      ) : null}
    </section>
  );
}
