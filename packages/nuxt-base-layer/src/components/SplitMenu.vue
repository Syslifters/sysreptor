<template>
  <div class="split-menu h-100 w-100">
    <resizable-navigation-drawer
      v-if="$slots['menu']"
      v-model="menuWidth"
      handle-location="left"
      class="h-100"
    >
      <div class="h-100 w-100 overflow-y-auto">
        <slot name="menu" />
      </div>
    </resizable-navigation-drawer>

    <div class="split-menu__content h-100 overflow-y-auto" ref="contentPaneRef">
      <v-container fluid class="pt-0 pb-0" v-bind="props.contentProps">
        <slot name="default" />
      </v-container>
    </div>

    <resizable-navigation-drawer
      v-if="$slots['sidebar']"
      v-model="sidebarWidth"
      handle-location="right"
      class="h-100"
    >
      <div class="h-100 w-100 overflow-y-auto">
        <slot name="sidebar" />
      </div>
    </resizable-navigation-drawer>
  </div>
</template>

<script setup lang="ts">
const router = useRouter();

const menuWidth = defineModel<number>({ default: 300 });
const sidebarWidth = defineModel<number>('sidebarWidth', { required: false });

const props = defineProps<{
  contentProps?: Record<string, any>;
}>();

// Scroll to top on navigate
const contentPaneRef = useTemplateRef('contentPaneRef');
watch(router.currentRoute, () => {
  contentPaneRef.value?.scrollTo({ top: 0, behavior: 'instant' });
});
</script>

<style lang="scss" scoped>
.split-menu {
  display: flex;
  position: relative;
}

.split-menu__content {
  flex: 1;
  min-width: 0;
}

.resizing:deep() {
  iframe {
    // Fix dragging in Firefox when mouse moves over iframes. 
    // Firefox does not emit mouse events (mousemove, mouseup) when mouse is over iframes.
    // Setting pointer-events prevents iframes from eating mouse events.
    pointer-events: none;
  }
}
</style>
