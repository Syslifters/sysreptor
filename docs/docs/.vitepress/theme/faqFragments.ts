import { onMounted, watch } from 'vue'
import { onContentUpdated, useRoute } from 'vitepress'
import { hashId, setHash, slugifyFragment, uniqueSlug } from './fragments'

const BOUND = 'data-faq-fragment'

let suppressHash = false

/** VitePress/GitHub-style slug so fragments stay stable and readable. */
export function slugifyFaqTitle(text: string): string {
  return slugifyFragment(text)
}

function summaryTitle(summary: HTMLElement): string {
  return (summary.textContent || '').replace(/\s+/g, ' ').trim()
}

export function faqItemWrappers(): HTMLElement[] {
  return [...document.querySelectorAll<HTMLElement>('.vp-doc .faq-item')]
}

export function faqDetails(): HTMLDetailsElement[] {
  return faqItemWrappers()
    .map((wrapper) => wrapper.querySelector('details'))
    .filter((el): el is HTMLDetailsElement => el != null)
}

export function allFaqOpen(): boolean {
  const items = faqDetails()
  return items.length > 0 && items.every((details) => details.open)
}

export function setAllFaqOpen(open: boolean) {
  suppressHash = true
  try {
    for (const details of faqDetails()) {
      details.open = open
    }
  } finally {
    suppressHash = false
  }
  if (!open) {
    const current = hashId()
    if (current && document.getElementById(current)?.classList.contains('faq-item')) {
      setHash(null)
    }
  }
}

function expandFromHash() {
  const id = hashId()
  if (!id) return
  const wrapper = document.getElementById(id)
  if (!wrapper?.classList.contains('faq-item')) return
  const details = wrapper.querySelector('details')
  if (!details) return
  suppressHash = true
  try {
    details.open = true
  } finally {
    suppressHash = false
  }
  requestAnimationFrame(() => {
    wrapper.scrollIntoView({ block: 'start' })
  })
}

function bindFaqItems() {
  const used = new Set<string>()
  faqItemWrappers().forEach((wrapper) => {
    const details = wrapper.querySelector('details')
    const summary = details?.querySelector('summary')
    if (!details || !summary) return

    let id = wrapper.id.trim()
    if (id) {
      used.add(id)
    } else {
      id = uniqueSlug(slugifyFaqTitle(summaryTitle(summary)), used, 'faq')
      wrapper.id = id
    }

    if (details.getAttribute(BOUND) === 'true') return
    details.setAttribute(BOUND, 'true')
    details.addEventListener('toggle', () => {
      if (suppressHash) return
      const currentId = wrapper.id
      if (details.open) {
        setHash(currentId)
      } else if (hashId() === currentId) {
        setHash(null)
      }
    })
  })
}

export function setupFaqFragments() {
  const route = useRoute()

  const sync = () => {
    bindFaqItems()
    expandFromHash()
  }

  onMounted(sync)
  onContentUpdated(sync)
  watch(() => route.hash, expandFromHash)
}
