export async function uploadFileHelper<T>(url: string, file: File, data: object = {}, fetchOptions?: object) {
  const form = new FormData();
  form.append('file', file);
  for (const [k, v] of Object.entries(data)) {
    form.append(k, v);
  }

  return await $fetch<T>(url, {
    method: 'POST',
    body: form,
    ...fetchOptions,
  });
}
