<template>
  <div :id="id" class="h-100" :class="{'splitpanes--collapsed': isCollapsed}">
    <splitpanes 
      :maximize-panes="false"
      @resized="modelValue = $event.prevPane.size"
      @ready="isReady = true"
      class="default-theme h-100"
    >
      <pane :size="modelValue" class="h-100 overflow-y-auto">
        <div class="h-100 w-100">
          <slot name="menu" />
        </div>
      </pane>
      <pane ref="contentPaneRef" :size="100 - modelValue" class="h-100 overflow-y-auto">
        <v-container fluid class="pt-0 pb-0" v-bind="props.contentProps">
          <slot name="default" />
        </v-container>
      </pane>
    </splitpanes>

    <teleport v-if="isReady && isCollapsed" :to="`#${id} > .splitpanes > .splitpanes__splitter`" defer>
      <!-- 
        Button to expand the menu when it is collapsed. 
        No slot is provided by splitpanes, so we use teleport instead 
      -->
      <div class="splitpanes--expand">
        <s-btn-icon
          @click="modelValue = expandSize"
          icon="mdi-chevron-right"
          density="compact"
        />
      </div>
    </teleport>
  </div>
</template>

<script setup lang="ts">
// @ts-expect-error missing types
import { Splitpanes, Pane } from 'splitpanes';
import 'splitpanes/dist/splitpanes.css';

const router = useRouter();

const modelValue = defineModel<number>({ default: 15 });
const props = defineProps<{
  expandSize?: number;
  contentProps?: Record<string, any>;
}>();


const id = useId();
const isReady = ref(false);
const initialModelValue = modelValue.value;
const expandSize = computed(() => props.expandSize ?? Math.max(initialModelValue, 15));
const COLLAPSE_THRESHOLD = 2; // Threshold below which the menu is considered collapsed
const isCollapsed = computed(() => modelValue.value < COLLAPSE_THRESHOLD && expandSize.value > 0);


// Scroll to top on navigate
const contentPaneRef = useTemplateRef('contentPaneRef');
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

.splitpanes--collapsed:deep() {
  .splitpanes__splitter {
    &:before, &:after {
      display: none;
    }
  }
  .splitpanes--expand {
    position: absolute;
    top: 50%;
    left: 0;
    transform: translateY(-50%);
    z-index: 1;
    background-color: rgba(var(--v-theme-surface));

    border: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));
    border-radius: 50%;
    border-left-width: 0;
    border-top-left-radius: 0;
    border-bottom-left-radius: 0;
  }
  
}

.splitpanes.default-theme:deep() {
  .splitpanes__pane {
    background-color: inherit;
  }
  .splitpanes__splitter {
    background-color: inherit;
    border-left: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));
    border-right: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));

    &:before, &:after {
      background-color: rgba(var(--v-theme-primary), 1);
      background-color: currentColor;
      opacity: 0.3;
    }
    &:hover:before, &:hover:after {
      background-color: currentColor;
      opacity: 0.5;
    }
  }
}
</style>
