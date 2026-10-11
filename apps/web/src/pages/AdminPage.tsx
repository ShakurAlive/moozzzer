import { KeyRound, Plus, Upload, X } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { Button } from "@/components/ui/Button";
import { EmptyState } from "@/components/ui/EmptyState";
import { Skeleton } from "@/components/ui/Skeleton";
import { t } from "@/i18n";
import {
  createInvite,
  listInvites,
  revokeInvite,
  uploadTrack,
  type InviteCreatedDto,
  type InviteDto,
} from "@/lib/api";
import { toast } from "@/stores/toast";

export function AdminPage() {
  const [invites, setInvites] = useState<InviteDto[]>([]);
  const [loading, setLoading] = useState(true);
  const [created, setCreated] = useState<InviteCreatedDto | null>(null);
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  useEffect(() => {
    let cancelled = false;
    void listInvites()
      .then((data) => {
        if (!cancelled) setInvites(data);
      })
      .catch(() => {
        if (!cancelled) toast({ title: t("admin.invites.error"), variant: "error" });
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const reloadInvites = () => {
    void listInvites()
      .then(setInvites)
      .catch(() => {
        toast({ title: t("admin.invites.error"), variant: "error" });
      });
  };

  const handleCreate = () => {
    void createInvite()
      .then((invite) => {
        setCreated(invite);
        reloadInvites();
      })
      .catch(() => {
        toast({ title: t("admin.invites.error"), variant: "error" });
      });
  };

  const handleRevoke = (id: string) => {
    void revokeInvite(id)
      .then(reloadInvites)
      .catch(() => {
        toast({ title: t("admin.invites.error"), variant: "error" });
      });
  };

  const handleUpload = () => {
    if (file === null) return;
    setUploading(true);
    void uploadTrack(file)
      .then(() => {
        toast({ title: t("admin.upload.success"), variant: "success" });
        setFile(null);
        if (fileInputRef.current !== null) fileInputRef.current.value = "";
      })
      .catch(() => {
        toast({ title: t("admin.upload.error"), variant: "error" });
      })
      .finally(() => {
        setUploading(false);
      });
  };

  const statusLabel = (invite: InviteDto): string => {
    if (invite.revoked_at !== null) return t("admin.invites.revoked");
    if (invite.used_at !== null) return t("admin.invites.used");
    return t("admin.invites.active");
  };

  return (
    <section className="space-y-8">
      <h1 className="text-2xl font-bold tracking-tight">{t("page.admin.title")}</h1>

      <div className="space-y-3">
        <div className="flex items-center justify-between gap-4">
          <h2 className="text-lg font-semibold">{t("admin.invites.title")}</h2>
          <Button onClick={handleCreate}>
            <Plus className="size-4" aria-hidden />
            {t("admin.invites.create")}
          </Button>
        </div>

        {created !== null ? (
          <div className="glass border-border/50 rounded-md border p-4">
            <p className="text-muted-foreground text-sm">{t("admin.invites.code")}</p>
            <p className="text-foreground mt-1 font-mono text-lg tracking-wider">{created.code}</p>
          </div>
        ) : null}

        {loading ? (
          <Skeleton className="h-10 w-full" />
        ) : invites.length === 0 ? (
          <EmptyState icon={KeyRound} title={t("admin.invites.empty")} className="min-h-[20vh]" />
        ) : (
          <ul className="flex flex-col gap-1">
            {invites.map((invite) => (
              <li
                key={invite.id}
                className="hover:bg-muted flex items-center gap-3 rounded-md px-3 py-2"
              >
                <span className="font-mono text-sm">{invite.id.slice(0, 8)}…</span>
                <span className="text-muted-foreground text-xs">{statusLabel(invite)}</span>
                <span className="text-muted-foreground flex-1 text-right text-xs">
                  {t("admin.invites.expires")}: {new Date(invite.expires_at).toLocaleString()}
                </span>
                <button
                  type="button"
                  onClick={() => {
                    handleRevoke(invite.id);
                  }}
                  disabled={invite.revoked_at !== null || invite.used_at !== null}
                  className="text-muted-foreground hover:text-destructive rounded-md p-1 transition-colors disabled:opacity-40"
                  aria-label={t("admin.invites.revoke")}
                >
                  <X className="size-4" aria-hidden />
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>

      <div className="space-y-3">
        <h2 className="text-lg font-semibold">{t("admin.upload.title")}</h2>
        <input
          ref={fileInputRef}
          type="file"
          accept="audio/*,.mp3,.m4a,.flac,.opus,.ogg,.wav"
          onChange={(event) => {
            setFile(event.target.files?.[0] ?? null);
          }}
          className="hidden"
        />
        <div className="flex items-center gap-3">
          <Button
            onClick={() => {
              if (file === null) {
                fileInputRef.current?.click();
              } else {
                handleUpload();
              }
            }}
            disabled={uploading}
          >
            <Upload className="size-4" aria-hidden />
            {file === null ? t("admin.upload.choose") : t("admin.upload.submit")}
          </Button>
          {file !== null ? (
            <span className="text-muted-foreground truncate text-sm">{file.name}</span>
          ) : null}
        </div>
      </div>
    </section>
  );
}
