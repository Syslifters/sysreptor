<template>
  <div class="h-100">
    <div v-if="isLoading" class="centered" v-bind="$attrs">
      <v-progress-circular indeterminate size="50" />
    </div>
    <iframe
      ref="iframeRef"
      :src="props.src"
      class="iframe-container"
      :class="{
        'iframe-loading': isLoading,
      }"
      :style="{ 
        colorScheme: theme.current.value.dark ? 'dark': 'light',
      }"
      @load="onIframeLoaded"
      v-bind="attrs"
    />
  </div>
</template>

<script setup lang="ts">
const props = defineProps<{
  src: string;
}>();

const attrs = useAttrs();
const theme = useTheme();

const iframeRef = ref<HTMLIFrameElement>('iframeRef');
const isLoading = ref(true);

function onIframeLoaded() {
  isLoading.value = false;

  // Hook navigation inside iframe: redirect to top-level navigation outside of iframe
  // Add target="_top" to all <a> tags inside iframe
  new MutationObserver((mutationList) => {
    for (const mutation of mutationList) {
      if (mutation.type === 'childList') {
        for (const an of mutation.addedNodes) {
          for (const node of getChildNotesRecursive(an)) {
            if (node.nodeType === Node.ELEMENT_NODE && node.nodeName === 'A' && !node.hasAttribute('target')) {
              node.setAttribute('target', '_top');
            }
          }
        }
      }
    }
  }).observe(iframeRef.value.contentWindow.document.body, { childList: true, subtree: true });
  // TODO: hook programmatic navigation?
  // TODO: pass project id to iframe: hash or window.parent.useNuxtApp().$router.currentRoute.value.params.projectId
}

function* getChildNotesRecursive(node) {
  yield node;
  for (const child of node.childNodes) {
    yield* getChildNotesRecursive(child);
  }
}


</script>

<style lang="scss" scoped>
.iframe-container {
  display: block;
  width: 100%;
  height: 100%;
  border: 0;
}

.iframe-loading {
  opacity: 0;
  top: 0;
  position: absolute;
}

.centered {
  height: 100%;
  display: flex;
  flex-direction: row;
  align-items: center;
  margin-left: 50vw;
}
</style>

