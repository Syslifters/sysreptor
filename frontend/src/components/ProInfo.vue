<template>
  <a 
    v-if="!apiSettings.isProfessionalLicense" 
    href="https://docs.sysreptor.com/features-and-pricing/"
    target="_blank"
    class="pro-link"
  >
    <slot />
    <span class="pro-badge">/PRO</span>
    <s-tooltip activator="parent" text="Available in SysReptor Professional" />
  </a>
  <span v-else><slot /></span>
</template>

<script setup lang="ts">
const apiSettings = useApiSettings();
</script>

<style lang="scss" scoped>
.pro-link {
  pointer-events: auto;
  text-decoration: none;
  color: inherit;
}
.pro-badge {
  color: rgb(var(--v-theme-primary));
  font-weight: 800;
}
</style>
