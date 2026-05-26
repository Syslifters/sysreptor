<template>
  <DefaultTheme.Layout>
    <template #layout-bottom>
      <footer class="sysreptor-footer">
        <div class="sysreptor-footer__inner">
          <p class="sysreptor-footer__message">
            <a href="https://www.syslifters.com/" target="_blank" rel="noopener noreferrer">Our Website</a>
            |
            <a href="https://sysleaks.com/" target="_blank" rel="noopener noreferrer">SysLeaks</a>
            |
            <a href="https://www.syslifters.com/impressum" target="_blank" rel="noopener noreferrer">Imprint</a>
            |
            <a href="/data-privacy">Data Privacy</a>
            |
            <a href="/contact-us">Contact</a>
          </p>
          <p class="sysreptor-footer__copyright">
            The FFG is the central national funding organization and strengthens Austria's innovative power.<br />
            This project is funded by the
            <a href="https://www.ffg.at" target="_blank" rel="noopener noreferrer">FFG</a>.
          </p>
        </div>
      </footer>
    </template>
  </DefaultTheme.Layout>
</template>

<script setup lang="ts">
import DefaultTheme from 'vitepress/theme'
</script>

<style scoped>
/* Match default VitePress footer (VPFooter.vue) */
.sysreptor-footer {
  position: relative;
  z-index: var(--vp-z-index-footer);
  border-top: 1px solid var(--vp-c-gutter);
  padding: 32px 24px;
  background-color: var(--vp-c-bg);
}

.sysreptor-footer__inner {
  margin: 0 auto;
  max-width: var(--vp-layout-max-width);
  text-align: center;
}

.sysreptor-footer__message,
.sysreptor-footer__copyright {
  line-height: 24px;
  font-size: 14px;
  font-weight: 500;
  color: var(--vp-c-text-2);
}

.sysreptor-footer :deep(a) {
  text-decoration: none;
  transition: color 0.25s;
}

.sysreptor-footer :deep(a:hover) {
  color: var(--vp-c-text-1);
}

@media (min-width: 768px) {
  .sysreptor-footer {
    padding: 32px;
  }
}
</style>
