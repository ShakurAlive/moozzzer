import { Search } from "lucide-react";
import { useState } from "react";
import { EmptyState } from "@/components/ui/EmptyState";
import { TrackCard } from "@/components/ui/TrackCard";
import { t } from "@/i18n";
import type { Track } from "@/lib/types";
import { toast } from "@/stores/toast";

const MOCK_RESULTS: Track[] = [
  {
    id: "s1",
    title: "Blinding Lights",
    artist: "The Weeknd",
    album: "After Hours",
    duration: 200,
    coverUrl: null,
    explicit: false,
  },
  {
    id: "s2",
    title: "HUMBLE.",
    artist: "Kendrick Lamar",
    album: "DAMN.",
    duration: 177,
    coverUrl: null,
    explicit: true,
  },
  {
    id: "s3",
    title: "Midnight City",
    artist: "M83",
    album: "Hurry Up, We're Dreaming",
    duration: 244,
    coverUrl: null,
    explicit: false,
  },
  {
    id: "s4",
    title: "SICKO MODE",
    artist: "Travis Scott",
    album: "ASTROWORLD",
    duration: 312,
    coverUrl: null,
    explicit: true,
  },
  {
    id: "s5",
    title: "Sweater Weather",
    artist: "The Neighbourhood",
    album: "I Love You.",
    duration: 244,
    coverUrl: null,
    explicit: false,
  },
];

export function SearchPage() {
  const [query, setQuery] = useState("");
  const hasQuery = query.trim() !== "";
  const results = hasQuery ? MOCK_RESULTS : [];

  return (
    <section className="space-y-6">
      <h1 className="text-2xl font-bold tracking-tight">{t("page.search.title")}</h1>

      <div className="relative max-w-xl">
        <Search
          className="text-muted-foreground pointer-events-none absolute top-1/2 left-3 size-5 -translate-y-1/2"
          aria-hidden
        />
        <input
          type="search"
          value={query}
          onChange={(event) => {
            setQuery(event.target.value);
          }}
          placeholder={t("search.placeholder")}
          className="border-input bg-muted text-foreground placeholder-muted-foreground focus:border-ring w-full rounded-md border py-2 pr-3 pl-10 text-sm transition-colors outline-none"
        />
      </div>

      {results.length === 0 ? (
        <EmptyState
          icon={Search}
          title={hasQuery ? t("empty.search.noResults") : t("empty.search.title")}
          description={t("empty.search.description")}
          className="min-h-[40vh] justify-center"
        />
      ) : (
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5">
          {results.map((track) => (
            <TrackCard
              key={track.id}
              track={track}
              onPlay={() => {
                toast({ title: track.title, description: t("toast.comingSoon") });
              }}
            />
          ))}
        </div>
      )}
    </section>
  );
}
