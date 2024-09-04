<template>
  <splitpanes @resized="emit('update:modelValue', $event[0].size)" class="default-theme h-100">
    <pane :size="props.modelValue" class="h-100 overflow-y-auto">
      <div class="h-100 w-100">
        <slot name="menu" />
      </div>
    </pane>
    <pane ref="contentPaneRef" :size="100 - props.modelValue" class="h-100 overflow-y-auto">
      <v-container fluid class="pt-0 pb-0" v-bind="props.contentProps">
        <slot name="default" />
      </v-container>
    </pane>
  </splitpanes>
</template>

<script setup lang="ts">
// @ts-expect-error missing types
import { Splitpanes, Pane } from 'splitpanes';
import 'splitpanes/dist/splitpanes.css';

const router = useRouter();

// TODO: menu slides on load; occurs on loading heavyweight components or loading components that use non-vue rendering (code-editor, markdown-editor)

const props = withDefaults(defineProps<{
  modelValue?: number;
  contentProps?: object;
}>(), {
  modelValue: 15,
  contentProps: () => ({}),
});
const emit = defineEmits<{
  (e: 'update:modelValue', modelValue: number): void
}>();

// Scroll to top on navigate
const contentPaneRef = ref();
watch(router.currentRoute, () => {
  contentPaneRef.value?.$el?.scrollTo({ top: 0, behavior: 'instant' });
});

</script>

<style lang="scss" scoped>

.splitpanes--dragging:deep() {
  iframe {
    // Fix dragging in Firefox when mouse moves over iframes. 
    // Firefox does not emit mouse events (mousemove, mouseup, used by splitpanes) when mouse is over iframes.
    // Setting pointer-events prevents iframes from eating mouse events.
    pointer-events: none;
  }
}

.splitpanes.default-theme:deep() {
  .splitpanes__pane {
    background-color: inherit;
  }
  .splitpanes__splitter {
    background-color: inherit;
    border-left-color: rgba(var(--v-border-color), var(--v-border-opacity));
    border-right: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));

    &:before, &:after {
      background-color: currentColor;
      opacity: 0.2;
    }
    &:hover:before, &:hover:after {
      opacity: 0.4;
    }
  }
}
</style>
