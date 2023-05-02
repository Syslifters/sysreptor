export async function uploadFileHelper(axios, url, file) {
  const form = new FormData();
  form.append('file', file);
  return await axios.$post(url, form, {
    headers: {
      'Content-Type': 'multipart/form-data'
    },
  });
}
