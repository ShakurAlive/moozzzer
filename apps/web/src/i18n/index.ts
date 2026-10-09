const ru = {
  "app.title": "Moozzzer",

  // Navigation
  "nav.wave": "Моя волна",
  "nav.search": "Поиск",
  "nav.library": "Медиатека",
  "nav.playlists": "Плейлисты",

  // Pages
  "page.wave.title": "Моя волна",
  "page.search.title": "Поиск",
  "page.library.title": "Медиатека",
  "page.playlists.title": "Плейлисты",

  // Empty states
  "empty.wave.title": "Моя волна скоро появится",
  "empty.wave.description": "Персональные рекомендации на основе ваших вкусов будут здесь.",
  "empty.search.title": "Ищите музыку",
  "empty.search.description": "Введите запрос, чтобы найти треки на внешних площадках.",
  "empty.search.noResults": "Ничего не найдено",

  // Player
  "player.nothingPlaying": "Ничего не играет",

  // Search
  "search.placeholder": "Что хотите послушать?",
  "search.error": "Не удалось выполнить поиск",
  "search.previewFailed": "Не удалось воспроизвести",
  "search.like": "Нравится",
  "search.addToPlaylist": "В плейлист",

  // Sources
  "source.youtube_music": "YouTube Music",
  "source.soundcloud": "SoundCloud",

  // Playlists
  "playlist.create": "Создать плейлист",

  // Toasts
  "toast.comingSoon": "Скоро появится",

  // Common (aria-labels)
  "common.play": "Воспроизвести",
  "common.pause": "Пауза",
  "common.more": "Ещё",
  "common.dismiss": "Закрыть",
  "common.next": "Следующий трек",
  "common.prev": "Предыдущий трек",
  "common.shuffle": "Перемешать",
  "common.repeat": "Повторять",

  // Auth
  "auth.title.login": "Вход",
  "auth.title.register": "Регистрация",
  "auth.label.emailOrUsername": "Email или имя пользователя",
  "auth.label.email": "Email",
  "auth.label.username": "Имя пользователя",
  "auth.label.password": "Пароль",
  "auth.label.inviteCode": "Код приглашения",
  "auth.button.login": "Войти",
  "auth.button.register": "Создать аккаунт",
  "auth.button.logout": "Выйти",
  "auth.button.submitting": "Отправка…",
  "auth.link.noAccount": "Нет аккаунта?",
  "auth.link.toRegister": "Зарегистрироваться",
  "auth.link.haveAccount": "Уже есть аккаунт?",
  "auth.link.toLogin": "Войти",
  "auth.validation.required": "Заполните все поля",
  "auth.validation.email": "Некорректный email",
  "auth.validation.username":
    "Имя пользователя: 3–32 символа (буквы, цифры, точка, дефис, подчёркивание)",
  "auth.validation.password": "Пароль должен быть не короче 8 символов",
  "auth.errors.invalid_credentials": "Неверный email/имя или пароль",
  "auth.errors.invite_invalid": "Недействительный или просроченный код приглашения",
  "auth.errors.account_disabled": "Аккаунт отключён",
  "auth.errors.rate_limited": "Слишком много попыток, попробуйте позже",
  "auth.errors.network_error": "Сеть недоступна",
  "auth.errors.validation": "Проверьте правильность заполнения формы",
  "auth.errors.generic": "Что-то пошло не так",
} as const;

export type MessageKey = keyof typeof ru;

// Minimal placeholder until a full i18n library is introduced.
export function t(key: MessageKey): string {
  return ru[key];
}
