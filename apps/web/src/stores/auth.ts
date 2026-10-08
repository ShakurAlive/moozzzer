import { create } from "zustand";
import {
  login as apiLogin,
  logout as apiLogout,
  me as apiMe,
  refresh as apiRefresh,
  register as apiRegister,
  setAccessToken,
  type LoginRequest,
  type RegisterRequest,
  type UserDto,
} from "@/lib/api";

type AuthStatus = "loading" | "authenticated" | "unauthenticated";

interface AuthState {
  user: UserDto | null;
  status: AuthStatus;
  init: () => Promise<void>;
  login: (input: LoginRequest) => Promise<void>;
  register: (input: RegisterRequest) => Promise<void>;
  logout: () => Promise<void>;
}

let refreshTimer: ReturnType<typeof setTimeout> | null = null;
let initialized = false;

function clearRefreshTimer(): void {
  if (refreshTimer !== null) {
    clearTimeout(refreshTimer);
    refreshTimer = null;
  }
}

function scheduleRefresh(expiresIn: number): void {
  clearRefreshTimer();
  const delayMs = Math.max((expiresIn - 60) * 1000, 1000);
  refreshTimer = setTimeout(() => {
    void refreshSilently();
  }, delayMs);
}

export const useAuthStore = create<AuthState>()((set) => ({
  user: null,
  status: "loading",

  async init() {
    if (initialized) return;
    initialized = true;

    set({ status: "loading" });
    try {
      const tokens = await apiRefresh();
      setAccessToken(tokens.access_token);
      const user = await apiMe();
      set({ user, status: "authenticated" });
      scheduleRefresh(tokens.expires_in);
    } catch {
      setAccessToken(null);
      set({ user: null, status: "unauthenticated" });
    }
  },

  async login(input) {
    const tokens = await apiLogin(input);
    setAccessToken(tokens.access_token);
    const user = await apiMe();
    set({ user, status: "authenticated" });
    scheduleRefresh(tokens.expires_in);
  },

  async register(input) {
    const tokens = await apiRegister(input);
    setAccessToken(tokens.access_token);
    const user = await apiMe();
    set({ user, status: "authenticated" });
    scheduleRefresh(tokens.expires_in);
  },

  async logout() {
    clearRefreshTimer();
    try {
      await apiLogout();
    } finally {
      setAccessToken(null);
      set({ user: null, status: "unauthenticated" });
    }
  },
}));

async function refreshSilently(): Promise<void> {
  try {
    const tokens = await apiRefresh();
    setAccessToken(tokens.access_token);
    scheduleRefresh(tokens.expires_in);
  } catch {
    clearRefreshTimer();
    setAccessToken(null);
    useAuthStore.setState({ user: null, status: "unauthenticated" });
  }
}
