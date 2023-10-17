import urlJoin from "url-join";

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
