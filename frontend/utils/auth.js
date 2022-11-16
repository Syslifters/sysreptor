import { RefreshScheme } from "@nuxtjs/auth-next/dist/runtime";

export default class CustomRefreshScheme extends RefreshScheme {
  REFRESH_IN_PROGRESS_STORAGE_KEY = 'refreshRequestInProgress';

  constructor($auth, options) {
    super($auth, options);

    this.pendingRefreshTokensRequest = null;
  }

  async refreshTokens() {
    if (this.pendingRefreshTokensRequest) {
      // Stored promise is used for synchronizing inside the same browser tab
      return await this.pendingRefreshTokensRequest;
    } else if (this.$auth.$storage.getUniversal(this.REFRESH_IN_PROGRESS_STORAGE_KEY)) {
      // Storage is used for synchronizing across multiple tabs
      return await new Promise((resolve, reject) => {
        const intervalId = setInterval(() => {
          if (!this.$auth.$storage.getUniversal(this.REFRESH_IN_PROGRESS_STORAGE_KEY)) {
            clearInterval(intervalId);
            resolve();
          }
        }, 100);
      });
    }
      
    try {
      this.pendingRefreshTokensRequest = super.refreshTokens();
      this.$auth.$storage.setUniversal(this.REFRESH_IN_PROGRESS_STORAGE_KEY, true);
      return await this.pendingRefreshTokensRequest;
    } finally {
      this.pendingRefreshTokensRequest = null;
      this.$auth.$storage.removeUniversal(this.REFRESH_IN_PROGRESS_STORAGE_KEY);
    }
  }
}
