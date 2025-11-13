<template>
  <div class="header-logo-text">
    <img v-if="headerLogoUrl && apiSettings.isProfessionalLicense" :src="headerLogoUrl" alt="Logo" />
    <template v-else>
      <svg-logo-text />
      <span class="license-text">{{ licenseText }}</span>
    </template>
  </div>
</template>

<script setup lang="ts">
const apiSettings = useApiSettings();
const theme = useTheme();

const props = withDefaults(defineProps<{
  licenseTextVariant?: 'long' | 'short';
}>(), {
  licenseTextVariant: 'short',
});

const headerLogoUrl = computed(() => theme?.current?.value?.variables['header-logo-url'] as string|undefined);
const licenseText = computed(() => {
  const license = apiSettings.settings?.license?.type || 'community';
  return {
    long: {
      community: '/Community Edition',
      professional: '/PRO',
    },
    short: {
      community: '/CE',
      professional: '/PRO',
    },
  }[props.licenseTextVariant][license] || '';
});
</script>

<style lang="scss" scoped>
.header-logo-text {
  --header-logo-height: 28px;
  width: auto;
  display: flex;
  flex-direction: row;
  align-items: center;
  flex-grow: 0;
  flex-shrink: 0;
  padding-left: 0.7rem;
  padding-right: 0.7rem;

  :deep() {
    svg, img {
      height: var(--header-logo-height);
      width: auto;
      display: block;
    }
  }

  .license-text {
    height: var(--header-logo-height);
    display: flex;
    flex-direction: column-reverse;
    font-weight: 900;
    font-size: 1.3rem;
    line-height: 1;
    color: rgb(var(--v-theme-logo));
  }
}


</style>
