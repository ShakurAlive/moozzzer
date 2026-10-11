// Minimal typed HTTP client for the auth endpoints.
// NOTE: these types mirror the OpenAPI schemas; stage 8.1 replaces them with
// `@moozzzer/api-client`.

import type { Playlist, Track } from "@/lib/types";

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

export type SearchResult = {
  provider: string;
  source_id: string;
  title: string;
  artist: string;
  album: string | null;
  duration_ms: number | null;
  cover_url: string | null;
  isrc: string | null;
  explicit: boolean;
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

let accessToken: string | null = null;

export function setAccessToken(token: string | null): void {
  accessToken = token;
}

interface RequestOptions {
  method?: "GET" | "POST" | "PUT" | "PATCH" | "DELETE";
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

  return fetch(path, {
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

  if (response.status === 401 && options.auth) {
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
    refreshInFlight = request<TokenResponse>("/api/v1/auth/refresh", { method: "POST" })
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
  return request<TokenResponse>("/api/v1/auth/refresh", { method: "POST" });
}

export function me(): Promise<UserDto> {
  return request<UserDto>("/api/v1/auth/me", { auth: true });
}

export function login(input: LoginRequest): Promise<TokenResponse> {
  return request<TokenResponse>("/api/v1/auth/login", { method: "POST", body: input });
}

export function register(input: RegisterRequest): Promise<TokenResponse> {
  return request<TokenResponse>("/api/v1/auth/register", { method: "POST", body: input });
}

export async function logout(): Promise<void> {
  await request<unknown>("/api/v1/auth/logout", { method: "POST" });
}

export function searchTracks(query: string): Promise<SearchResult[]> {
  return request<SearchResult[]>(`/api/v1/search?q=${encodeURIComponent(query)}`, {
    auth: true,
  });
}

export function previewUrl(provider: string, sourceId: string): string {
  return `/api/v1/preview/${provider}/${encodeURIComponent(sourceId)}`;
}

export async function fetchPreview(provider: string, sourceId: string): Promise<Blob> {
  let response = await fetchResponse(previewUrl(provider, sourceId), { auth: true });

  if (response.status === 401) {
    await refreshAccessToken();
    response = await fetchResponse(previewUrl(provider, sourceId), { auth: true });
  }

  if (!response.ok) {
    throw await toApiError(response);
  }

  return response.blob();
}

// --- library / playlists (stage 3) ---

export type TrackDto = {
  id: string;
  title: string;
  artist: string;
  album: string | null;
  duration_ms: number | null;
  explicit: boolean;
  cover_url: string | null;
  media_url: string | null;
};

export type PlaylistDto = {
  id: string;
  name: string;
  description: string | null;
  cover_url: string | null;
  track_count: number;
};

export type PlaylistDetailDto = PlaylistDto & { tracks: TrackDto[] };

export function trackFromDto(dto: TrackDto): Track {
  return {
    id: dto.id,
    title: dto.title,
    artist: dto.artist,
    album: dto.album,
    durationMs: dto.duration_ms,
    coverUrl: dto.cover_url,
    mediaUrl: dto.media_url,
    explicit: dto.explicit,
  };
}

export function playlistFromDto(dto: PlaylistDto): Playlist {
  return {
    id: dto.id,
    name: dto.name,
    description: dto.description,
    trackCount: dto.track_count,
    coverUrl: dto.cover_url,
  };
}

export function listLibrary(): Promise<TrackDto[]> {
  return request<TrackDto[]>("/api/v1/library", { auth: true });
}

async function requestNoContent(path: string, options: RequestOptions = {}): Promise<void> {
  await request<unknown>(path, options);
}

export function addToLibrary(trackId: string): Promise<void> {
  return requestNoContent(`/api/v1/library/${trackId}`, { method: "PUT", auth: true });
}

export function removeFromLibrary(trackId: string): Promise<void> {
  return requestNoContent(`/api/v1/library/${trackId}`, { method: "DELETE", auth: true });
}

export function listPlaylists(): Promise<PlaylistDto[]> {
  return request<PlaylistDto[]>("/api/v1/playlists", { auth: true });
}

export function createPlaylist(input: {
  name: string;
  description?: string;
}): Promise<PlaylistDto> {
  return request<PlaylistDto>("/api/v1/playlists", { method: "POST", body: input, auth: true });
}

export function getPlaylist(id: string): Promise<PlaylistDetailDto> {
  return request<PlaylistDetailDto>(`/api/v1/playlists/${id}`, { auth: true });
}

export function updatePlaylist(
  id: string,
  input: { name?: string; description?: string },
): Promise<PlaylistDto> {
  return request<PlaylistDto>(`/api/v1/playlists/${id}`, {
    method: "PATCH",
    body: input,
    auth: true,
  });
}

export function deletePlaylist(id: string): Promise<void> {
  return requestNoContent(`/api/v1/playlists/${id}`, { method: "DELETE", auth: true });
}

export function addPlaylistTrack(playlistId: string, trackId: string): Promise<void> {
  return requestNoContent(`/api/v1/playlists/${playlistId}/tracks/${trackId}`, {
    method: "PUT",
    auth: true,
  });
}

export function removePlaylistTrack(playlistId: string, trackId: string): Promise<void> {
  return requestNoContent(`/api/v1/playlists/${playlistId}/tracks/${trackId}`, {
    method: "DELETE",
    auth: true,
  });
}

export function reorderPlaylist(playlistId: string, trackIds: string[]): Promise<void> {
  return requestNoContent(`/api/v1/playlists/${playlistId}/tracks`, {
    method: "PUT",
    body: { track_ids: trackIds },
    auth: true,
  });
}

// --- invites (admin) ---

export type InviteDto = {
  id: string;
  created_at: string;
  expires_at: string;
  used_at: string | null;
  revoked_at: string | null;
};

export type InviteCreatedDto = {
  id: string;
  code: string;
  expires_at: string;
};

export function listInvites(): Promise<InviteDto[]> {
  return request<InviteDto[]>("/api/v1/invites", { auth: true });
}

export function createInvite(): Promise<InviteCreatedDto> {
  return request<InviteCreatedDto>("/api/v1/invites", { method: "POST", auth: true });
}

export function revokeInvite(id: string): Promise<void> {
  return requestNoContent(`/api/v1/invites/${id}`, { method: "DELETE", auth: true });
}

// --- admin manual upload (multipart, so it bypasses the JSON `request` helper) ---

export async function uploadTrack(file: File): Promise<TrackDto> {
  const formData = new FormData();
  formData.append("file", file);

  const authHeaders = (): Record<string, string> =>
    accessToken ? { Authorization: `Bearer ${accessToken}` } : {};

  let response = await fetch("/api/v1/admin/tracks/upload", {
    method: "POST",
    headers: authHeaders(),
    credentials: "include",
    body: formData,
  });

  if (response.status === 401) {
    await refreshAccessToken();
    response = await fetch("/api/v1/admin/tracks/upload", {
      method: "POST",
      headers: authHeaders(),
      credentials: "include",
      body: formData,
    });
  }

  if (!response.ok) {
    throw await toApiError(response);
  }
  return (await response.json()) as TrackDto;
}
