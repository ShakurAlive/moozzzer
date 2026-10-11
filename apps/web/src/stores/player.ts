// Player store (stage 3.3): a single <audio> element drives queue playback,
// play/pause/next/prev, seek, volume, shuffle/repeat and the Media Session API
// (lock-screen / headset controls).

import { create } from "zustand";
import type { Track } from "@/lib/types";

type RepeatMode = "off" | "all" | "one";

interface PlayerState {
  queue: Track[];
  index: number;
  isPlaying: boolean;
  shuffle: boolean;
  repeat: RepeatMode;
  volume: number;
  muted: boolean;
  currentTime: number;
  duration: number;

  playTrack: (track: Track) => void;
  playQueue: (tracks: Track[], startIndex: number) => void;
  togglePlay: () => void;
  next: () => void;
  prev: () => void;
  seek: (seconds: number) => void;
  setVolume: (volume: number) => void;
  toggleMute: () => void;
  toggleShuffle: () => void;
  cycleRepeat: () => void;
}

let audio: HTMLAudioElement | null = null;

function getAudio(): HTMLAudioElement {
  if (audio !== null) return audio;
  const el = new Audio();
  el.preload = "metadata";

  el.addEventListener("timeupdate", () => {
    usePlayerStore.setState({ currentTime: el.currentTime });
  });
  el.addEventListener("durationchange", () => {
    usePlayerStore.setState({ duration: Number.isFinite(el.duration) ? el.duration : 0 });
  });
  el.addEventListener("play", () => {
    usePlayerStore.setState({ isPlaying: true });
  });
  el.addEventListener("pause", () => {
    usePlayerStore.setState({ isPlaying: false });
  });
  el.addEventListener("ended", () => {
    if (usePlayerStore.getState().repeat === "one") {
      void el.play().catch(() => {});
    } else {
      usePlayerStore.getState().next();
    }
  });

  audio = el;
  return el;
}

function updateMediaSession(track: Track | null): void {
  if (!("mediaSession" in navigator)) return;
  const session = navigator.mediaSession;

  if (track === null) {
    session.metadata = null;
    return;
  }

  session.metadata = new MediaMetadata({
    title: track.title,
    artist: track.artist,
    album: track.album ?? "",
    artwork: track.coverUrl
      ? [{ src: new URL(track.coverUrl, window.location.origin).href, sizes: "512x512" }]
      : [],
  });

  session.setActionHandler("play", () => {
    usePlayerStore.getState().togglePlay();
  });
  session.setActionHandler("pause", () => {
    usePlayerStore.getState().togglePlay();
  });
  session.setActionHandler("previoustrack", () => {
    usePlayerStore.getState().prev();
  });
  session.setActionHandler("nexttrack", () => {
    usePlayerStore.getState().next();
  });
  session.setActionHandler("seekto", (details) => {
    if (typeof details.seekTime === "number") usePlayerStore.getState().seek(details.seekTime);
  });
}

function loadTrack(track: Track): void {
  const el = getAudio();
  el.src = track.mediaUrl ?? "";
  el.currentTime = 0;
  usePlayerStore.setState({ currentTime: 0, duration: 0 });
  updateMediaSession(track);
  if (track.mediaUrl !== null) {
    void el.play().catch(() => {});
  }
}

export const usePlayerStore = create<PlayerState>()((set, get) => ({
  queue: [],
  index: -1,
  isPlaying: false,
  shuffle: false,
  repeat: "off",
  volume: 1,
  muted: false,
  currentTime: 0,
  duration: 0,

  playTrack(track) {
    set({ queue: [track], index: 0 });
    loadTrack(track);
  },

  playQueue(tracks, startIndex) {
    if (tracks.length === 0) return;
    const safeIndex = Math.min(Math.max(startIndex, 0), tracks.length - 1);
    const current = tracks[safeIndex];
    set({ queue: tracks, index: safeIndex });
    if (current !== undefined) loadTrack(current);
  },

  togglePlay() {
    const el = getAudio();
    if (!el.paused) {
      el.pause();
      return;
    }
    const { queue, index } = get();
    const current = queue[index];
    if (current !== undefined && el.readyState === 0) {
      loadTrack(current);
      return;
    }
    void el.play().catch(() => {});
  },

  next() {
    const { queue, index, shuffle, repeat } = get();
    if (queue.length === 0) return;

    let nextIndex = index + 1;
    if (shuffle && queue.length > 1) {
      let candidate = Math.floor(Math.random() * queue.length);
      while (candidate === index) candidate = Math.floor(Math.random() * queue.length);
      nextIndex = candidate;
    } else if (nextIndex >= queue.length) {
      if (repeat !== "all") return;
      nextIndex = 0;
    }

    const next = queue[nextIndex];
    if (next === undefined) return;
    set({ index: nextIndex });
    loadTrack(next);
  },

  prev() {
    const { queue, index, repeat } = get();
    if (queue.length === 0) return;

    const el = getAudio();
    if (el.currentTime > 3) {
      el.currentTime = 0;
      return;
    }

    let prevIndex = index - 1;
    if (prevIndex < 0) {
      if (repeat !== "all") return;
      prevIndex = queue.length - 1;
    }

    const prev = queue[prevIndex];
    if (prev === undefined) return;
    set({ index: prevIndex });
    loadTrack(prev);
  },

  seek(seconds) {
    if (!Number.isFinite(seconds)) return;
    const el = getAudio();
    const max = get().duration > 0 ? get().duration : Number.POSITIVE_INFINITY;
    el.currentTime = Math.max(0, Math.min(seconds, max));
  },

  setVolume(volume) {
    const clamped = Math.max(0, Math.min(volume, 1));
    getAudio().volume = clamped;
    set({ volume: clamped, muted: clamped === 0 });
  },

  toggleMute() {
    const muted = !get().muted;
    getAudio().muted = muted;
    set({ muted });
  },

  toggleShuffle() {
    set({ shuffle: !get().shuffle });
  },

  cycleRepeat() {
    const order: RepeatMode[] = ["off", "all", "one"];
    const current = get().repeat;
    const next = order[(order.indexOf(current) + 1) % order.length];
    set({ repeat: next });
  },
}));
