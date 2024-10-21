export const trustedTypes = (window as any).trustedTypes || {
  createPolicy: (_name: string, options: any) => options,
};


export const workerUrlPolicy = trustedTypes.createPolicy('worker-url', {
  createScriptURL: (url: string) => url,
});


// export const defaultPolicy = trustedTypes.createPolicy('default', {
//   createHTML: (html: string) => DOMPurify.sanitize(html, { RETURN_TRUSTED_TYPE: false }),
//   createScript: () => { throw new Error('Script execution is disabled'); },
// });


export default defineNuxtPlugin(() => {});
