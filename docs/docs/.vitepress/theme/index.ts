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

export default {
  extends: DefaultTheme,
  Layout,
  enhanceApp({ app }) {
    app.component('Icon', Icon)
    enhanceAppWithTabs(app)
    registerDocBadges(app)
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
