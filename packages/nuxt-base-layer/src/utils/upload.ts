export async function uploadFileHelper<T>(url: string, file: File|File[], data: object = {}, fetchOptions?: object) {
  const form = new FormData();
  if (Array.isArray(file)) {
    for (const f of file) {
      form.append('file', f, f.name);
    }
  } else {
    form.append('file', file, file.name);
  }
  for (const [k, v] of Object.entries(data)) {
    form.append(k, v);
  }

  return await $fetch<T>(url, {
    method: 'POST',
    body: form,
    ...fetchOptions,
  });
}
