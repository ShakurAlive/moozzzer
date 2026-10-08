// UI-level types for the shell. Real API DTOs arrive with the library/player
// stages; these mirror the expected shape so components don't churn later.

export type Track = {
  id: string;
  title: string;
  artist: string;
  album: string | null;
  duration: number; // seconds
  coverUrl: string | null;
  explicit: boolean;
};

export type Playlist = {
  id: string;
  name: string;
  trackCount: number;
  coverUrl: string | null;
};
