import { urlJoin } from "@base/utils/helpers";

export function absoluteApiUrl(url: string): string {
  if (['http', 'data'].some(p => url.startsWith(p))) {
    return url;
  } else {
    return urlJoin(new URL('/', window.location.href).origin, url);
  }
}

export function uniqueName(baseName: string, existingNames: string[]) {
  let i = 1;
  while (true) {
    const name = baseName + i;
    if (!existingNames.includes(name)) {
      return name
    }
    i += 1;
  }
}

export function sanitizeUrl(url?: string | null): string|undefined {
  if (!url) {
    return undefined;
  }
  try {
    const u = new URL(url, window.location.origin);
    if (u.origin === window.location.origin || ['http:', 'https:'].includes(u.protocol)) {
      return url;
    }
  } catch { 
    // Invalid URL
  }
  return undefined;
}
