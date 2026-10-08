// Minimal typed HTTP client for the auth endpoints.
// NOTE: these types mirror the OpenAPI schemas; stage 8.1 replaces them with
// `@moozzzer/api-client`.

export type UserRole = "admin" | "member";

export type UserDto = {
  id: string;
  email: string;
  username: string;
  role: UserRole;
  created_at: string;
};

export type TokenResponse = {
  access_token: string;
  token_type: "bearer";
  expires_in: number;
  refresh_token: string | null;
};

export type RegisterRequest = {
  email: string;
  username: string;
  password: string;
  invite_code: string;
};

export type LoginRequest = {
  email_or_username: string;
  password: string;
};

export type FieldError = {
  field: string;
  message: string;
};

export class ApiError extends Error {
  readonly status: number;
  readonly code: string;
  readonly errors: FieldError[];

  constructor(status: number, code: string, errors: FieldError[] = []) {
    super(code);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
    this.errors = errors;
  }
}

const BASE = "/api/v1/auth";

let accessToken: string | null = null;

export function setAccessToken(token: string | null): void {
  accessToken = token;
}

interface RequestOptions {
  method?: "GET" | "POST";
  body?: unknown;
  auth?: boolean;
}

interface ValidationItem {
  loc: unknown[];
  msg: unknown;
}

function isStringDetail(value: unknown): value is { detail: string } {
  return (
    typeof value === "object" &&
    value !== null &&
    typeof (value as { detail?: unknown }).detail === "string"
  );
}

function isValidationDetail(value: unknown): value is { detail: ValidationItem[] } {
  if (typeof value !== "object" || value === null) return false;
  const detail = (value as { detail?: unknown }).detail;
  return (
    Array.isArray(detail) &&
    detail.every((item) => {
      if (typeof item !== "object" || item === null) return false;
      return Array.isArray((item as { loc?: unknown }).loc);
    })
  );
}

function rawRequest(path: string, options: RequestOptions): Promise<Response> {
  const headers: Record<string, string> = {};
  if (options.body !== undefined) headers["Content-Type"] = "application/json";
  if (options.auth && accessToken) headers.Authorization = `Bearer ${accessToken}`;

  return fetch(`${BASE}${path}`, {
    method: options.method ?? "GET",
    headers,
    credentials: "include",
    body: options.body === undefined ? undefined : JSON.stringify(options.body),
  });
}

async function fetchResponse(path: string, options: RequestOptions): Promise<Response> {
  try {
    return await rawRequest(path, options);
  } catch {
    throw new ApiError(0, "network_error");
  }
}

async function toApiError(response: Response): Promise<ApiError> {
  let payload: unknown = null;
  try {
    payload = await response.json();
  } catch {
    payload = null;
  }

  if (isStringDetail(payload)) {
    return new ApiError(response.status, payload.detail);
  }

  if (isValidationDetail(payload)) {
    const errors: FieldError[] = payload.detail.map((item) => {
      const field = item.loc.filter((part): part is string => typeof part === "string").at(-1);
      return {
        field: field ?? "unknown",
        message: typeof item.msg === "string" ? item.msg : "invalid",
      };
    });
    return new ApiError(response.status, "validation_error", errors);
  }

  return new ApiError(response.status, `http_${String(response.status)}`);
}

async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  let response = await fetchResponse(path, options);

  if (response.status === 401 && options.auth && path !== "/refresh") {
    await refreshAccessToken();
    response = await fetchResponse(path, options);
  }

  if (!response.ok) {
    throw await toApiError(response);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  const data: unknown = await response.json();
  return data as T;
}

let refreshInFlight: Promise<void> | null = null;

async function refreshAccessToken(): Promise<void> {
  if (!refreshInFlight) {
    refreshInFlight = request<TokenResponse>("/refresh", { method: "POST" })
      .then((tokens) => {
        setAccessToken(tokens.access_token);
      })
      .finally(() => {
        refreshInFlight = null;
      });
  }
  await refreshInFlight;
}

export function refresh(): Promise<TokenResponse> {
  return request<TokenResponse>("/refresh", { method: "POST" });
}

export function me(): Promise<UserDto> {
  return request<UserDto>("/me", { auth: true });
}

export function login(input: LoginRequest): Promise<TokenResponse> {
  return request<TokenResponse>("/login", { method: "POST", body: input });
}

export function register(input: RegisterRequest): Promise<TokenResponse> {
  return request<TokenResponse>("/register", { method: "POST", body: input });
}

export async function logout(): Promise<void> {
  await request<unknown>("/logout", { method: "POST" });
}
