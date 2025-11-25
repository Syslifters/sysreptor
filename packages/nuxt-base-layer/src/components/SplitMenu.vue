<template>
  <div class="split-menu">
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

    <Transition  name="sidebar-slide">
      <resizable-navigation-drawer
        v-if="$slots['sidebar'] && sidebarWidth !== undefined"
        v-model="sidebarWidth"
        handle-location="right"
        class="split-menu__sidebar h-100"
      >
        <div class="h-100 w-100 overflow-y-auto">
          <slot name="sidebar" />
        </div>
      </resizable-navigation-drawer>
    </Transition>
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
@use "@base/assets/vuetify.scss" as vuetify;

.split-menu {
  display: flex;
  position: relative;
  width: 100%;
  height: 100%;
  overflow: hidden;
}

.split-menu__content {
  flex: 1;
  min-width: 0;
}

.sidebar-slide {
  &-enter-active, &-leave-active {
    transition-property: vuetify.$navigation-drawer-transition-property;
    transition-duration: vuetify.$navigation-drawer-transition-duration;
    transition-timing-function: vuetify.$navigation-drawer-transition-timing-function;

    position: fixed;
    right: 0;
  }
  &-enter-from, &-leave-to {
    transform: translateX(100%);
  }
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
