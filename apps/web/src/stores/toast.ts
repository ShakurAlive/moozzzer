import { create } from "zustand";

export type ToastVariant = "default" | "success" | "error";

export type ToastInput = {
  title: string;
  description?: string;
  variant?: ToastVariant;
};

export type Toast = ToastInput & { id: string };

interface ToastState {
  toasts: Toast[];
  push: (input: ToastInput) => void;
  dismiss: (id: string) => void;
}

let counter = 0;

export const useToastStore = create<ToastState>()((set) => ({
  toasts: [],

  push(input) {
    counter += 1;
    const id = `toast-${String(counter)}`;
    set((state) => ({ toasts: [...state.toasts, { id, ...input }] }));
  },

  dismiss(id) {
    set((state) => ({ toasts: state.toasts.filter((toast) => toast.id !== id) }));
  },
}));

export function toast(input: ToastInput): void {
  useToastStore.getState().push(input);
}
