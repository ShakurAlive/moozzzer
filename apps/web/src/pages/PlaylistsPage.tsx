import { Plus } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { PlaylistCard } from "@/components/ui/PlaylistCard";
import { t } from "@/i18n";
import type { Playlist } from "@/lib/types";
import { toast } from "@/stores/toast";

const MOCK_PLAYLISTS: Playlist[] = [
  { id: "p1", name: "Для фокуса", trackCount: 24, coverUrl: null },
  { id: "p2", name: "Вечерний вайб", trackCount: 41, coverUrl: null },
  { id: "p3", name: "Тренировка", trackCount: 17, coverUrl: null },
  { id: "p4", name: "Дорога", trackCount: 33, coverUrl: null },
  { id: "p5", name: "Старые хиты", trackCount: 12, coverUrl: null },
];

export function PlaylistsPage() {
  return (
    <section className="space-y-6">
      <div className="flex items-center justify-between gap-4">
        <h1 className="text-2xl font-bold tracking-tight">{t("page.playlists.title")}</h1>
        <Button
          variant="outline"
          onClick={() => {
            toast({ title: t("playlist.create"), description: t("toast.comingSoon") });
          }}
        >
          <Plus className="size-4" aria-hidden />
          {t("playlist.create")}
        </Button>
      </div>

      <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5">
        {MOCK_PLAYLISTS.map((playlist) => (
          <PlaylistCard
            key={playlist.id}
            playlist={playlist}
            onClick={() => {
              toast({ title: playlist.name, description: t("toast.comingSoon") });
            }}
          />
        ))}
      </div>
    </section>
  );
}
