import { ApiError } from "@/lib/api";
import { t, type MessageKey } from "@/i18n";

function errorKey(code: string): MessageKey {
  switch (code) {
    case "invalid_credentials":
      return "auth.errors.invalid_credentials";
    case "invite_invalid":
      return "auth.errors.invite_invalid";
    case "account_disabled":
      return "auth.errors.account_disabled";
    case "rate_limited":
      return "auth.errors.rate_limited";
    case "network_error":
      return "auth.errors.network_error";
    case "validation_error":
      return "auth.errors.validation";
    default:
      return "auth.errors.generic";
  }
}

export function authErrorMessage(err: unknown): string {
  if (err instanceof ApiError) {
    return t(errorKey(err.code));
  }
  return t("auth.errors.generic");
}
