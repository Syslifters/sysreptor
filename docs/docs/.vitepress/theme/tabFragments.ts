import { nextTick, onMounted, watch } from 'vue'
import { onContentUpdated, useRoute } from 'vitepress'
import { hashId, setHash, slugifyFragment, uniqueSlug } from './fragments'

const BOUND = 'data-tab-fragment-bound'
const TAB_ID = 'data-tab-fragment'

let suppressHash = false

function tabLabel(button: HTMLElement): string {
  return (button.textContent || '').replace(/\s+/g, ' ').trim()
}

function tabGroups(): HTMLElement[] {
  return [...document.querySelectorAll<HTMLElement>('.vp-doc .plugin-tabs')]
}

function usedFragmentIds(): Set<string> {
  const used = new Set<string>()
  document.querySelectorAll('[id]').forEach((el) => {
    if (el.id) used.add(el.id)
  })
  document.querySelectorAll(`[${TAB_ID}]`).forEach((el) => {
    const id = el.getAttribute(TAB_ID)?.trim()
    if (id) used.add(id)
  })
  return used
}

function assignTabSlugs(group: HTMLElement, used: Set<string>) {
  group.querySelectorAll<HTMLElement>('.plugin-tabs--tab').forEach((button) => {
    let id = button.getAttribute(TAB_ID)?.trim() || ''
    if (id) {
      used.add(id)
      return
    }
    id = uniqueSlug(slugifyFragment(tabLabel(button)), used, 'tab')
    button.setAttribute(TAB_ID, id)
  })
}

function selectedTab(group: HTMLElement): HTMLElement | null {
  return group.querySelector<HTMLElement>('.plugin-tabs--tab[aria-selected="true"]')
}

function syncHashFromGroup(group: HTMLElement) {
  if (suppressHash) return
  const id = selectedTab(group)?.getAttribute(TAB_ID)
  if (id) setHash(id)
}

function bindTabs() {
  const used = usedFragmentIds()
  tabGroups().forEach((group) => {
    assignTabSlugs(group, used)
    if (group.getAttribute(BOUND) === 'true') return
    group.setAttribute(BOUND, 'true')

    const tablist = group.querySelector('.plugin-tabs--tab-list')
    if (!tablist) return

    tablist.addEventListener('click', (event) => {
      const button = (event.target as HTMLElement | null)?.closest<HTMLElement>('.plugin-tabs--tab')
      if (!button || !group.contains(button)) return
      if (suppressHash) return
      const id = button.getAttribute(TAB_ID)
      if (id) setHash(id)
    })
    tablist.addEventListener('keydown', (event) => {
      if (event.key !== 'ArrowLeft' && event.key !== 'ArrowRight') return
      requestAnimationFrame(() => syncHashFromGroup(group))
    })
  })
}

function selectFromHash() {
  const id = hashId()
  if (!id) return
  const button = document.querySelector<HTMLElement>(`.plugin-tabs--tab[${TAB_ID}="${CSS.escape(id)}"]`)
  if (!button) return
  const group = button.closest<HTMLElement>('.plugin-tabs')
  if (!group) return

  suppressHash = true
  try {
    if (button.getAttribute('aria-selected') !== 'true') {
      button.click()
    }
  } finally {
    suppressHash = false
  }

  requestAnimationFrame(() => {
    group.scrollIntoView({ block: 'start' })
  })
}

export function setupTabFragments() {
  const route = useRoute()

  const sync = () => {
    nextTick(() => {
      bindTabs()
      selectFromHash()
    })
  }

  onMounted(sync)
  onContentUpdated(sync)
  watch(() => route.hash, () => {
    nextTick(selectFromHash)
  })
}
