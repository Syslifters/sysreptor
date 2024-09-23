import DOMPurify from 'dompurify';

export const trustedTypes = window.trustedTypes || {
  createPolicy: (_name: string, options: TrustedTypePolicyOptions) => options,
};


export const workerUrlPolicy = trustedTypes.createPolicy('worker-url', {
  createScriptURL: (url: string) => url,
});


export const defaultPolicy = trustedTypes.createPolicy('default', {
  createHTML: (html: string) => DOMPurify.sanitize(html, { RETURN_TRUSTED_TYPE: false }),
  createScript: () => { throw new Error('Script execution is disabled'); },
});


export default defineNuxtPlugin(() => {});
