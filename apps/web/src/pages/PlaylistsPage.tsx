import { ListMusic, Plus } from "lucide-react";
import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/Button";
import { EmptyState } from "@/components/ui/EmptyState";
import { PlaylistCard } from "@/components/ui/PlaylistCard";
import { Skeleton } from "@/components/ui/Skeleton";
import { t } from "@/i18n";
import { createPlaylist, listPlaylists, playlistFromDto } from "@/lib/api";
import type { Playlist } from "@/lib/types";
import { toast } from "@/stores/toast";

export function PlaylistsPage() {
  const navigate = useNavigate();
  const [playlists, setPlaylists] = useState<Playlist[]>([]);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [name, setName] = useState("");

  useEffect(() => {
    let cancelled = false;
    void listPlaylists()
      .then((data) => {
        if (!cancelled) setPlaylists(data.map(playlistFromDto));
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
  }, []);

  const handleCreate = () => {
    const trimmed = name.trim();
    if (trimmed === "") return;
    setCreating(true);
    void createPlaylist({ name: trimmed })
      .then((dto) => {
        setPlaylists((prev) => [playlistFromDto(dto), ...prev]);
        setName("");
      })
      .catch(() => {
        toast({ title: t("playlist.error"), variant: "error" });
      })
      .finally(() => {
        setCreating(false);
      });
  };

  return (
    <section className="space-y-6">
      <div className="flex items-center justify-between gap-4">
        <h1 className="text-2xl font-bold tracking-tight">{t("page.playlists.title")}</h1>
      </div>

      <div className="flex max-w-md items-center gap-2">
        <input
          type="text"
          value={name}
          onChange={(event) => {
            setName(event.target.value);
          }}
          onKeyDown={(event) => {
            if (event.key === "Enter") handleCreate();
          }}
          placeholder={t("playlist.namePlaceholder")}
          className="border-input bg-muted text-foreground placeholder-muted-foreground focus:border-ring w-full rounded-md border px-3 py-2 text-sm transition-colors outline-none"
        />
        <Button onClick={handleCreate} disabled={creating || name.trim() === ""}>
          <Plus className="size-4" aria-hidden />
          {t("playlist.create")}
        </Button>
      </div>

      {loading ? (
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5">
          {Array.from({ length: 5 }).map((_, item) => (
            <Skeleton key={item} className="aspect-square w-full rounded-lg" />
          ))}
        </div>
      ) : playlists.length === 0 ? (
        <EmptyState
          icon={ListMusic}
          title={t("empty.playlists.title")}
          description={t("empty.playlists.description")}
          className="min-h-[40vh] justify-center"
        />
      ) : (
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5">
          {playlists.map((playlist) => (
            <PlaylistCard
              key={playlist.id}
              playlist={playlist}
              onClick={() => {
                void navigate(`/playlists/${playlist.id}`);
              }}
            />
          ))}
        </div>
      )}
    </section>
  );
}
