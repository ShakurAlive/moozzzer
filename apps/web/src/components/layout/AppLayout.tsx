import { Outlet } from "react-router-dom";
import { Background } from "@/components/Background";
import { PlayerBar } from "@/components/layout/PlayerBar";
import { Sidebar } from "@/components/layout/Sidebar";
import { ToastViewport } from "@/components/ui/Toast";

export function AppLayout() {
  return (
    <>
      <div className="relative flex h-full overflow-hidden">
        <Background />
        <div className="relative z-10 flex w-full">
          <Sidebar />
          <div className="flex min-w-0 flex-1 flex-col">
            <main className="flex-1 overflow-y-auto px-8 py-6">
              <Outlet />
            </main>
            <PlayerBar />
          </div>
        </div>
      </div>
      <ToastViewport />
    </>
  );
}
