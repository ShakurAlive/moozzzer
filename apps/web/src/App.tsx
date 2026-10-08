import { useEffect } from "react";
import { Navigate, Route, Routes } from "react-router-dom";
import { ProtectedRoute } from "@/components/ProtectedRoute";
import { AppLayout } from "@/components/layout/AppLayout";
import { LibraryPage } from "@/pages/LibraryPage";
import { LoginPage } from "@/pages/LoginPage";
import { PlaylistsPage } from "@/pages/PlaylistsPage";
import { RegisterPage } from "@/pages/RegisterPage";
import { SearchPage } from "@/pages/SearchPage";
import { WavePage } from "@/pages/WavePage";
import { useAuthStore } from "@/stores/auth";

export function App() {
  const init = useAuthStore((state) => state.init);

  useEffect(() => {
    void init();
  }, [init]);

  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />

      <Route
        element={
          <ProtectedRoute>
            <AppLayout />
          </ProtectedRoute>
        }
      >
        <Route index element={<Navigate to="/wave" replace />} />
        <Route path="wave" element={<WavePage />} />
        <Route path="search" element={<SearchPage />} />
        <Route path="library" element={<LibraryPage />} />
        <Route path="playlists" element={<PlaylistsPage />} />
      </Route>

      <Route path="*" element={<Navigate to="/wave" replace />} />
    </Routes>
  );
}
