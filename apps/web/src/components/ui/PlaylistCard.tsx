import { ListMusic } from "lucide-react";
import { formatTrackCount } from "@/lib/format";
import type { Playlist } from "@/lib/types";

export interface PlaylistCardProps {
  playlist: Playlist;
  onClick?: () => void;
}

export function PlaylistCard({ playlist, onClick }: PlaylistCardProps) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="group hover:bg-muted w-full rounded-lg p-2 text-left transition-colors"
    >
      <div className="bg-card relative aspect-square overflow-hidden rounded-md">
        {playlist.coverUrl ? (
          <img src={playlist.coverUrl} alt="" className="size-full object-cover" />
        ) : (
          <div className="flex size-full items-center justify-center">
            <ListMusic className="text-muted-foreground size-8" aria-hidden />
          </div>
        )}
      </div>
      <div className="mt-2 space-y-0.5">
        <p className="truncate text-sm font-medium">{playlist.name}</p>
        <p className="text-muted-foreground text-xs">{formatTrackCount(playlist.trackCount)}</p>
      </div>
    </button>
  );
}
