import Toast, { useToast } from "vue-toastification";
import "vue-toastification/dist/index.css";

export default defineNuxtPlugin((nuxtApp) => {
  nuxtApp.vueApp.use(Toast, {
    position: 'bottom-right',
    hideProgressBar: true,
  });
  return {
    provide: {
      toast: useToast(),
    }
  };
});
