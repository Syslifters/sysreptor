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
        const INTERVAL_TIME = 100;
        const MAX_WAIT_TIME = 10_000;
        let intervalIterationCount = 0;
        const intervalId = setInterval(() => {
          intervalIterationCount += 1;
          if (!this.$auth.$storage.getUniversal(this.REFRESH_IN_PROGRESS_STORAGE_KEY)) {
            clearInterval(intervalId);
            resolve();
          } else if (intervalIterationCount * INTERVAL_TIME >= MAX_WAIT_TIME) {
            clearInterval(intervalId);
            this.$auth.$storage.removeUniversal(this.REFRESH_IN_PROGRESS_STORAGE_KEY);
            reject(new Error('Refresh synchronization took too long'));
          }
        }, INTERVAL_TIME);
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
