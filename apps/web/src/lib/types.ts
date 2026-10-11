// UI-level types for the shell and player. These mirror the API DTOs (see
// `lib/api.ts` -> `trackFromDto` / `playlistFromDto`); components consume these
// instead of the raw wire types.

export type Track = {
  id: string;
  title: string;
  artist: string;
  album: string | null;
  durationMs: number | null;
  coverUrl: string | null;
  mediaUrl: string | null;
  explicit: boolean;
};

export type Playlist = {
  id: string;
  name: string;
  description: string | null;
  trackCount: number;
  coverUrl: string | null;
};
