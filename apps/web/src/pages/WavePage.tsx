import { AudioWaveform } from "lucide-react";
import { EmptyState } from "@/components/ui/EmptyState";
import { t } from "@/i18n";

export function WavePage() {
  return (
    <section className="space-y-6">
      <h1 className="text-2xl font-bold tracking-tight">{t("page.wave.title")}</h1>
      <EmptyState
        icon={AudioWaveform}
        title={t("empty.wave.title")}
        description={t("empty.wave.description")}
        className="min-h-[60vh] justify-center"
      />
    </section>
  );
}
