<template>
  <splitpanes @resized="emit('update:modelValue', $event[0].size)" class="default-theme h-100">
    <pane :size="props.modelValue" class="h-100 overflow-y-auto">
      <div class="h-100 w-100">
        <slot name="menu" />
      </div>
    </pane>
    <pane :size="100 - props.modelValue" class="h-100 overflow-y-auto">
      <v-container fluid class="pt-0 pb-0" v-bind="props.contentProps">
        <slot name="default" />
      </v-container>
    </pane>
  </splitpanes>
</template>

<script setup lang="ts">
// @ts-ignore
import { Splitpanes, Pane } from 'splitpanes';
import 'splitpanes/dist/splitpanes.css';

// TODO: menu slides on load; occurs on loading heavyweight components or loading components that use non-vue rendering (code-editor, markdown-editor)

const props = withDefaults(defineProps<{
  modelValue?: number;
  contentProps?: Object;
}>(), {
  modelValue: 15,
  contentProps: () => ({}),
});
const emit = defineEmits<{
  (e: 'update:modelValue', modelValue: number): void
}>();
</script>

<style lang="scss" scoped>
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
