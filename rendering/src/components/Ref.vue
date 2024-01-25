<template>
  <a :href="'#' + (refEl?.id || toId)"  :class="refClasses">
    <span class="ref-title">
      <slot name="default">
        <template v-if="refEl && !error">
          {{ refEl.getAttribute('data-toc-title') || refEl.textContent }}
        </template>
      </slot>
    </span>
  </a>
</template>

<script setup>
import { v4 as uuidv4 } from "uuid";
import { computed, defineProps, onMounted, ref, useSlots } from "vue";
import { callForTicks } from "@/utils";


const props = defineProps({
  to: {
    type: String,
    required: true
  },
});

const slots = useSlots();

const refEl = ref(null);
const error = ref(null);

const toId = computed(() => {
  const toStr = props.to || '';
  return toStr.startsWith('#') ? toStr.substring(1) : toStr;
});
const refClasses = computed(() => {
  const out = ['ref'];
  if (!slots.default && refEl.value) {
    if (['H1', 'H2', 'H3', 'H4', 'H5', 'H6'].includes(refEl.value.tagName)) {
      const level = Number.parseInt(refEl.value.tagName.slice(1)) || 1;

      if (refEl.value.closest('.appendix')) {
        out.push('ref-heading', 'ref-appendix');
        if (refEl.value.classList.contains('numbered')) {
          out.push('ref-appendix-level' + level);
        }
      } else if (refEl.value.classList.contains('numbered')) {
        out.push('ref-heading', 'ref-heading-level' + level);
      } else {
        out.push('ref-heading');
      }
    } else if (refEl.value.tagName === 'FIGCAPTION') {
      out.push('ref-figure');
    } else if (refEl.value.tagName === 'CAPTION') {
      out.push('ref-table');
    }
  }
  return out;
});


function updateReference() {
  error.value = null;
  refEl.value = document.getElementById(toId.value);
  if (!refEl.value) {
    error.value = {
      message: 'Invalid reference',
      details: `Referenced element with id="${toId.value}" not found.`,
    };
    return;
  }

  // Check figure reference
  if (refEl.value.tagName === 'IMG') {
    refEl.value = refEl.value.closest('figure')?.querySelector('figcaption');
    if (!refEl.value) {
      error.value = {
        message: 'Invalid reference',
        details: `IMG element with id="${toId.value}" cannot be referenced, because it does not have a FIGCAPTION.`
      };
      return;
    }
  } else if (refEl.value.tagName === 'FIGURE') {
    refEl.value = refEl.value.querySelector('figcaption');
    if (!refEl.value) {
      error.value = {
        message: 'Invalid reference',
        details: `FIGURE element with id="${toId.value}" cannot be referenced, because it does not have a FIGCAPTION.`
      };
      return;
    }
  }
  if (refEl.value.tagName === 'FIGCAPTION' && !refEl.value.id) {
    refEl.value.setAttribute('id', uuidv4());
  }

  // Check table reference
  if (refEl.value.tagName === 'TABLE') {
    refEl.value = refEl.value.querySelector('caption');
    if (!refEl.value) {
      error.value = {
        message: 'Invalid reference',
        details: `TABLE element with id="${toId.value}" cannot be referenced, because it does not have a CAPTION.`
      };
      return;
    }
  }
  if (refEl.value.tagName === 'CAPTION' && !refEl.value.id) {
    refEl.value.setAttribute('id', uuidv4());
  }

  // Check heading reference
  const tagNames = ['H1', 'H2', 'H3', 'H4', 'H5', 'H6', 'FIGCAPTION', 'CAPTION'];
  if (!tagNames.map(t => t.toUpperCase()).includes(refEl.value.tagName) && !slots.default) {
    error.value = {
      message: 'Invalid reference',
      details: `${refEl.value.tagName} element with id="${toId.value}" cannot be automatically referenced. Provide a reference title manually (e.g. "[reference title](#${toId.value})" or "<ref to="${toId.value}">reference title</ref>").`
    };
    return;
  }

}
onMounted(async () => {
  await callForTicks(4, () => updateReference());
  if (error.value) {
    console.warn(error.value.message, error.value);
  }
});
</script>
