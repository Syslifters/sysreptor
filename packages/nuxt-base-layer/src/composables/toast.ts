import { isObject } from "lodash-es";

export type ToastType = "success" | "error" | "warning" | "info";

const TOAST_TYPE_ICONS: Record<ToastType, string> = {
  success: "mdi-check-circle",
  error: "mdi-alert",
  warning: "mdi-alert",
  info: "mdi-information",
};

export interface ToastMessage {
  text: string;
  color: ToastType;
  prependIcon?: string;
}

export interface ToastConfirmState {
  message: string;
  buttonText: string;
  resolve: (value: boolean) => void;
}

// Module-level state (singleton, shared across all callers)
const toastQueue = ref<ToastMessage[]>([]);
const confirmState = ref<ToastConfirmState | null>(null);

function push(message: { text: string; type: ToastType; }) {
  toastQueue.value = [...toastQueue.value, { 
    ...message, 
    color: message.type,
    prependIcon: TOAST_TYPE_ICONS[message.type],
  }];
}

function showConfirm(options: { message: string; buttonText: string }): Promise<boolean> {
  return new Promise((resolve) => {
    confirmState.value = {
      message: options.message,
      buttonText: options.buttonText,
      resolve: (value: boolean) => {
        confirmState.value = null;
        resolve(value);
      },
    };
  });
}

export function useToast() {
  return {
    toastQueue: toastQueue,
    confirmState: confirmState,
    push,
    showConfirm,
  };
}

// Helper functions (use module-level state so they work from anywhere)

export function requestErrorToast({ error, message }: { error: any; message?: string }) {
  // eslint-disable-next-line no-console
  console.log("Request error", { error, message }, error?.data);

  if (!message) {
    if (error.reason) {
      message = error.reason as string;
    } else if (error?.options?.method === "GET") {
      message = "Failed to load data";
    } else if (["POST", "PUT", "PATCH"].includes(error?.options?.method)) {
      message = "Failed to save data";
    } else if (error?.options?.method === "DELETE") {
      message = "Failed to delete data";
    } else {
      message = "Request error";
    }
  }
  if (error?.data?.detail) {
    message += ": " + error?.data?.detail;
  } else if (Array.isArray(error?.data)) {
    message += ": " + error.data.join(", ");
  } else if (error?.data?.non_field_errors) {
    message += ": " + error.data.non_field_errors.join(", ");
  } else if (error?.status === 429) {
    message += ": Exceeded rate limit. Try again later.";
  } else if (isObject(error?.data)) {
    const entries = Object.values(error.data)
      .filter((v) => Array.isArray(v))
      .flat();
    message += ": " + entries.join(", ");
  } else if (error?.options?.signal?.aborted) {
    return; // Do not show toast for aborted requests
  }
  errorToast(message);
}

export function successToast(message: string) {
  push({ text: message, type: "success" });
}

export function errorToast(message: string) {
  push({ text: message, type: "error" });
}

export function warningToast(message: string) {
  push({ text: message, type: "warning" });
}

export function collabConfirmToast(message?: string) {
  return showConfirm({
    message:
      message ||
      "Other users are editing this list. This operation might result in conflicts.",
    buttonText: "Force change",
  });
}
