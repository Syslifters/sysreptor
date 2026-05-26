<script setup lang="ts">
import { computed } from 'vue'

export type DocBadgeVariant = 'pro' | 'self-hosted' | 'cloud' | 'experimental'

const props = defineProps<{
  variant?: DocBadgeVariant;
  /** Overrides the default label for this variant */
  label?: string;
  icon?: string;
  tone?: string;
}>()

const DEFINITIONS: Record<
  DocBadgeVariant,
  { icon: string; defaultLabel: string; tone: 'danger' | 'warning' | 'muted' }
> = {
  pro: {
    icon: 'octicon:heart-fill-24',
    defaultLabel: 'Pro only',
    tone: 'danger',
  },
  'self-hosted': {
    icon: 'octicon:server-24',
    defaultLabel: 'Self-Hosted',
    tone: 'muted',
  },
  cloud: {
    icon: 'octicon:cloud-24',
    defaultLabel: 'Cloud',
    tone: 'muted',
  },
  experimental: {
    icon: 'octicon:alert-fill-24',
    defaultLabel: 'Experimental. Expect breaking changes.',
    tone: 'warning',
  },
}

const def = computed(() => DEFINITIONS[props.variant!])
const icon = computed(() => props.icon ?? def.value?.icon ?? '')
const displayLabel = computed(() => props.label ?? def.value?.defaultLabel ?? '')
const toneClass = computed(() => `doc-badge--${props.tone ?? def.value?.tone ?? 'muted'}`)
</script>

<template>
  <span class="doc-badge" :class="toneClass">
    <Icon
      class="doc-badge__icon"
      :icon="icon"
      inline
      width="1.15em"
      height="1.15em"
    />
    <span class="doc-badge__label">{{ displayLabel }}</span>
  </span>
</template>

<style scoped>
.doc-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.35em;
  vertical-align: middle;
  font-weight: 500;
  font-size: inherit;
  line-height: 1.25;
}

.doc-badge__icon {
  flex-shrink: 0;
  vertical-align: -0.125em;
}

.doc-badge--danger {
  color: var(--vp-c-danger-1);
}

.doc-badge--warning {
  color: var(--vp-c-warning-1);
}

.doc-badge--muted {
  color: var(--vp-c-text-2);
}
</style>
