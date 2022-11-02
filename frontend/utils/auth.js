import { RefreshScheme } from "@nuxtjs/auth-next/dist/runtime";

export default class CustomRefreshScheme extends RefreshScheme {
  constructor($auth, options) {
    super($auth, options);

    this.pendingRefreshTokensRequest = null;
  }

  async refreshTokens() {
    if (this.pendingRefreshTokensRequest) {
      return await this.pendingRefreshTokensRequest;
    }
      
    try {
      this.pendingRefreshTokensRequest = super.refreshTokens();
      return await this.pendingRefreshTokensRequest;
    } finally {
      this.pendingRefreshTokensRequest = null;
    }
  }
}
