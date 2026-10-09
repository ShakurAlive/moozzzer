import { Search } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { EmptyState } from "@/components/ui/EmptyState";
import { SearchResultRow } from "@/components/ui/SearchResultRow";
import { Skeleton } from "@/components/ui/Skeleton";
import { t } from "@/i18n";
import { fetchPreview, searchTracks, type SearchResult } from "@/lib/api";
import { toast } from "@/stores/toast";

export function SearchPage() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<SearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(false);
  const [playingKey, setPlayingKey] = useState<string | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  const hasQuery = query.trim() !== "";

  useEffect(() => {
    const q = query.trim();
    if (q === "") return;

    let cancelled = false;
    const timer = setTimeout(() => {
      void (async () => {
        try {
          const data = await searchTracks(q);
          if (!cancelled) {
            setResults(data);
            setError(false);
            setLoading(false);
          }
        } catch {
          if (!cancelled) {
            setError(true);
            setLoading(false);
          }
        }
      })();
    }, 350);

    return () => {
      cancelled = true;
      clearTimeout(timer);
    };
  }, [query]);

  useEffect(() => {
    return () => {
      audioRef.current?.pause();
    };
  }, []);

  const togglePlay = (result: SearchResult) => {
    void playPreview(result);
  };

  async function playPreview(result: SearchResult): Promise<void> {
    const key = `${result.provider}:${result.source_id}`;
    if (playingKey === key) {
      audioRef.current?.pause();
      setPlayingKey(null);
      return;
    }

    audioRef.current?.pause();
    setPlayingKey(key);

    try {
      const blob = await fetchPreview(result.provider, result.source_id);
      const url = URL.createObjectURL(blob);
      const audio = new Audio(url);
      audioRef.current = audio;
      audio.onended = () => {
        setPlayingKey(null);
        URL.revokeObjectURL(url);
      };
      await audio.play();
    } catch {
      setPlayingKey(null);
      toast({ title: t("search.previewFailed"), variant: "error" });
    }
  }

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
            const value = event.target.value;
            setQuery(value);
            if (value.trim() === "") {
              setResults([]);
              setLoading(false);
              setError(false);
            } else {
              setLoading(true);
              setError(false);
            }
          }}
          placeholder={t("search.placeholder")}
          className="border-input bg-muted text-foreground placeholder-muted-foreground focus:border-ring w-full rounded-md border py-2 pr-3 pl-10 text-sm transition-colors outline-none"
        />
      </div>

      {loading ? (
        <div className="flex flex-col gap-2">
          {Array.from({ length: 5 }).map((_, index) => (
            <Skeleton key={index} className="h-14 w-full" />
          ))}
        </div>
      ) : error ? (
        <EmptyState
          icon={Search}
          title={t("search.error")}
          className="min-h-[40vh] justify-center"
        />
      ) : results.length === 0 ? (
        <EmptyState
          icon={Search}
          title={hasQuery ? t("empty.search.noResults") : t("empty.search.title")}
          description={t("empty.search.description")}
          className="min-h-[40vh] justify-center"
        />
      ) : (
        <div className="flex flex-col gap-1">
          {results.map((result) => {
            const key = `${result.provider}:${result.source_id}`;
            return (
              <SearchResultRow
                key={key}
                result={result}
                isPlaying={playingKey === key}
                onPlay={() => {
                  togglePlay(result);
                }}
                onLike={() => {
                  toast({ title: t("search.like"), description: t("toast.comingSoon") });
                }}
                onMenu={() => {
                  toast({ title: t("search.addToPlaylist"), description: t("toast.comingSoon") });
                }}
              />
            );
          })}
        </div>
      )}
    </section>
  );
}
