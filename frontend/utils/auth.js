import { CookieScheme } from "@nuxtjs/auth-next/dist/runtime";

export default class CustomCookieScheme extends CookieScheme {
  check() {
    // The sessionid cookie uses httpOnly, we cannot check if it is set or not
    return { valid: true };
  }
}

export function redirectToReAuth({ auth, route }) {
  auth.$storage.setUniversal('redirect', route.path);
  auth.redirect('reauth');
}
