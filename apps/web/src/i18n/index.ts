const ru = {
  "app.title": "Moozzzer",

  "home.loggedInAs": "Вы вошли как",

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
