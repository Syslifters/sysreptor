export async function uploadFileHelper(axios, url, file, data = {}) {
  const form = new FormData();
  form.append('file', file);
  for (const [k, v] of Object.entries(data)) {
    form.append(k, v);
  }
  return await axios.$post(url, form, {
    headers: {
      'Content-Type': 'multipart/form-data'
    },
  });
}
