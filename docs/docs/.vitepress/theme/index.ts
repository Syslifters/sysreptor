import type { Theme } from 'vitepress/client'
import type { App } from 'vue'
import { h } from 'vue'
import DefaultTheme from 'vitepress/theme'
import { Icon } from '@iconify/vue/offline'
import './register-icons'
import { enhanceAppWithTabs } from 'vitepress-plugin-tabs/client'
import DocBadge from './components/DocBadge.vue'
import Layout from './Layout.vue'
import './style.css'

/** AnythingLLM always renders sponsor text as a link; replace with plain text. */
function plainTextAnythingllmSponsor() {
  for (const link of Array.from(
    document.querySelectorAll<HTMLAnchorElement>(
      'a.allm-text-xs.allm-font-sans:not([data-plain-sponsor])'
    )
  )) {
    if (!link.closest('[class*="allm-"]')) continue

    const span = document.createElement('span')
    span.className = link.className.replace(/\bhover:allm-underline\b/g, '').trim()
    span.style.color = 'rgb(122, 125, 126)'
    span.textContent = link.textContent
    span.dataset.plainSponsor = 'true'
    link.replaceWith(span)
  }
}

export default {
  extends: DefaultTheme,
  Layout,
  enhanceApp({ app }) {
    app.component('Icon', Icon)
    enhanceAppWithTabs(app)
    registerDocBadges(app)

    if (typeof window !== 'undefined') {
      plainTextAnythingllmSponsor()
      window.addEventListener('load', plainTextAnythingllmSponsor, { once: true })
      const anythingllmSponsorObserver = new MutationObserver(plainTextAnythingllmSponsor)
      anythingllmSponsorObserver.observe(document.body, { childList: true, subtree: true })
    }
  },
} satisfies Theme

function registerDocBadges(app: App) {
  app.component('DocBadge', DocBadge)
  const shortcuts = [
    ['BadgePro', 'pro'],
    ['BadgeSelfHosted', 'self-hosted'],
    ['BadgeCloud', 'cloud'],
    ['BadgeExperimental', 'experimental'],
  ] as const
  for (const [name, variant] of shortcuts) {
    app.component(name, {
      setup(_, { attrs }) {
        return () => h(DocBadge, { variant, ...attrs })
      },
    })
  }
}
