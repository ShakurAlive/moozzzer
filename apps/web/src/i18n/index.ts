const ru = {
  "app.title": "Moozzzer",
  "health.label": "API",
  "health.loading": "проверка…",
  "health.ok": "ok",
  "health.error": "недоступен",
} as const;

export type MessageKey = keyof typeof ru;

// Minimal placeholder until a full i18n library is introduced.
export function t(key: MessageKey): string {
  return ru[key];
}
