import { type ApiSettings, type AuthProvider, type CWE, AuthProviderType } from '#imports';

export const useApiSettings = defineStore('apisettings', {
  state: () => ({
    settings: null as ApiSettings | null,
    getSettingsSync: null as Promise<ApiSettings> | null,
    cwes: null as CWE[]|null,
    getCwesSync: null as Promise<CWE[]>|null,
  }),
  actions: {
    async fetchSettings() : Promise<ApiSettings> {
      this.$patch({
        settings: await $fetch<ApiSettings>('/api/public/utils/settings/', { method: 'GET' }),
      })
      return this.settings!;
    },
    async getSettings() : Promise<ApiSettings> {
      if (this.settings) {
        return this.settings;
      } else if (this.getSettingsSync) {
        return await this.getSettingsSync;
      } else {
        // Use only 1 fetch requests
        // Prevent performing the same requests multiple times when many components want to access data at the same time
        try {
          this.getSettingsSync = this.fetchSettings();
          return await this.getSettingsSync;
        } finally {
          this.getSettingsSync = null;
        }
      }
    },
    async fetchCwes(): Promise<CWE[]> {
      this.cwes = await $fetch<CWE[]>('/api/v1/utils/cwes/', { method: 'GET' });
      return this.cwes;
    },
    async getCwes(): Promise<CWE[]> {
      if (this.cwes) {
        return this.cwes;
      } else if (this.getCwesSync) {
        return await this.getCwesSync;
      } else {
        try {
          this.getCwesSync = this.fetchCwes();
          return await this.getCwesSync;
        } finally {
          this.getCwesSync = null;
        }
      }
    }
  },
  getters: {
    isProfessionalLicense(): boolean {
      return this.settings?.license?.type === LicenseType.professional;
    },
    isLocalUserAuthEnabled(): boolean {
      return this.settings!.auth_providers.some(p => p.type === AuthProviderType.LOCAL);
    },
    oidcAuthProviders(): AuthProvider[] {
      return this.settings!.auth_providers.filter(p => p.type === AuthProviderType.OIDC);
    },
    remoteUserAuthProvider(): AuthProvider|null {
      return this.settings!.auth_providers.find(p => p.type === AuthProviderType.REMOTEUSER) || null;
    },
    ssoAuthProviders(): AuthProvider[] {
      return this.settings!.auth_providers.filter(p => [AuthProviderType.OIDC, AuthProviderType.REMOTEUSER].includes(p.type));
    },
    isSsoEnabled(): boolean {
      return this.ssoAuthProviders.length > 0;
    },
    spellcheckLanguageToolSupported(): boolean {
      return this.settings?.features?.spellcheck || false;
    },
    spellcheckLanguageToolSupportedForLanguage() {
      return (lang?: string|null) => this.spellcheckLanguageToolSupported && 
        (!!this.settings!.languages.find(l => l.code === lang)?.spellcheck || lang === 'auto');
    },
  }
})
