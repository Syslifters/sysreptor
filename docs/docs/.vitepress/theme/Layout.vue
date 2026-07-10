<template>
  <AskAiButton />
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
import { onMounted, watch } from 'vue'
import { useData, withBase } from 'vitepress'
import DefaultTheme from 'vitepress/theme'
import AskAiButton from './components/AskAiButton.vue'
import { matchRedirect } from '../redirects/redirectRules'
import rules from 'virtual:vitepress-redirects'

const { page } = useData()

function maybeRedirectNotFound() {
  if (!page.value.isNotFound) return
  const { pathname, search, hash } = window.location
  const target = matchRedirect(pathname, rules)
  if (!target) return
  const next = target.startsWith('http://') || target.startsWith('https://')
    ? target
    : withBase(target) + search + hash
  if (next === window.location.href) return
  window.location.replace(next)
}

onMounted(maybeRedirectNotFound)
watch(() => page.value.relativePath, maybeRedirectNotFound)
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
