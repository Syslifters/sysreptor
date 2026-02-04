import { defineStore } from 'pinia';
import { type ApiSettings, type AuthProvider, type CWE, type LicenseInfoDetails, type ReviewStatusDefinition, AuthProviderType, LicenseType, ReviewStatus } from '#imports';
import { useSingletonFetcher } from './api';

export const useApiSettings = defineStore('apisettings', () => {
  const settings = useSingletonFetcher<ApiSettings>('/api/public/utils/settings/');
  const cwes = useSingletonFetcher<CWE[]>('/api/v1/utils/cwes/');
  const licenseInfo = useSingletonFetcher<LicenseInfoDetails>('/api/v1/utils/license/');

  const isProfessionalLicense = computed<boolean>(() => settings.data.value?.license?.type === LicenseType.professional);

  const isLocalUserAuthEnabled = computed<boolean>(() => {
    return settings.data.value?.auth_providers.some(p => p.type === AuthProviderType.LOCAL) || false;
  });
  const oidcAuthProviders = computed<AuthProvider[]>(() => {
    return settings.data.value?.auth_providers.filter(p => p.type === AuthProviderType.OIDC) || [];
  });
  const remoteUserAuthProvider = computed<AuthProvider|null>(() => {
    return settings.data.value?.auth_providers.find(p => p.type === AuthProviderType.REMOTEUSER) || null;
  });
  const ssoAuthProviders = computed<AuthProvider[]>(() => {
    return settings.data.value?.auth_providers.filter(p => [AuthProviderType.OIDC, AuthProviderType.REMOTEUSER].includes(p.type)) || [];
  });
  const isSsoEnabled = computed<boolean>(() => {
    return ssoAuthProviders.value.length > 0;
  });

  const spellcheckLanguageToolSupported = computed<boolean>(() => {
    return settings.data.value?.features.spellcheck || false;
  });
  const spellcheckLanguageToolSupportedForLanguage = computed(() => {
    return (lang?: string | null) => spellcheckLanguageToolSupported.value && 
      (!!settings.data.value?.languages.find(l => l.code === lang)?.spellcheck || lang === 'auto');
  });

  const getStatusDefinition = computed(() => {
    return (status?: string | null): ReviewStatusDefinition => {
      let out = settings.data.value?.statuses.find(s => s.id === status);
      if (!out && status === ReviewStatus.DEPRECATED) {
        out = {id: ReviewStatus.DEPRECATED, label: 'Deprecated', icon: 'mdi-close-octagon-outline'};
      }
      return out || {id: status || 'unknown', label: status || 'Unknown'};
    }
  });
  
  return {
    settings: settings.data,
    getSettings: settings.getData,
    fetchSettings: settings.fetchData,
    cwes: cwes.data,
    getCwes: cwes.getData,
    licenseInfo: licenseInfo.data,
    getLicenseInfo: licenseInfo.getData,
    isProfessionalLicense,
    isLocalUserAuthEnabled,
    oidcAuthProviders,
    remoteUserAuthProvider,
    ssoAuthProviders,
    isSsoEnabled,
    spellcheckLanguageToolSupported,
    spellcheckLanguageToolSupportedForLanguage,
    getStatusDefinition,
  }
});
