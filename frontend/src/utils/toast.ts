import { useToast } from "vue-toastification";

export function requestErrorToast({ error, message }: { error: any, message?: string}) {
  // eslint-disable-next-line no-console
  console.log('Request error', { error, message }, error?.data);

  if (!message) {
    if (error?.options?.method === 'GET') {
      message = 'Failed to load data';
    } else if (['POST', 'PUT', 'PATCH'].includes(error?.options?.method)) {
      message = 'Failed to save data';
    } else if (error?.options?.method === 'DELETE') {
      message = 'Failed to delete data';
    } else {
      message = 'Request error';
    }
  }
  if (error?.data?.detail) {
    message += ': ' + error?.data?.detail;
  } else if (Array.isArray(error?.data) && error?.data?.length === 1) {
    message += ': ' + error?.data[0];
  } else if (error?.status === 429) {
    message += ': Exceeded rate limit. Try again later.';
  }

  errorToast(message);
}

export function successToast(message: string) {
  const toast = useToast();
  toast.success(message);
}

export function errorToast(message: string) {
  const toast = useToast();
  toast.error(message);
}

export function warningToast(message: string) {
  const toast = useToast();
  toast.warning(message);
}
