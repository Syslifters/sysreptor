<template>
  <div class="h-100">
    <div v-if="isLoading" class="centered" v-bind="$attrs">
      <v-progress-circular indeterminate size="50" />
    </div>
    <iframe
      ref="iframeRef"
      :src="iframeUrl"
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

const route = useRoute();
const attrs = useAttrs();
const theme = useTheme();

const iframeRef = ref<HTMLIFrameElement>();
const isLoading = ref(true);
const iframeUrl = computed(() => {
  const url = new URL(props.src, window.location.href);
  // Append current query to iframe URL
  new URLSearchParams(route.query as Record<string, string>).forEach((value, key) => url.searchParams.append(key, value));
  // Append route params as query to iframe URL
  new URLSearchParams(route.params as Record<string, string>).forEach((value, key) => url.searchParams.append(key, value));
  return url.toString();
});


function onIframeLoaded() {
  isLoading.value = false;

  // Hook navigation inside iframe: redirect to top-level navigation outside of iframe
  // Add target="_top" to all <a> tags inside iframe
  const iframeDocument = iframeRef.value!.contentWindow!.document;
  iframeDocument.querySelectorAll('a:not([target])')
    .forEach((a) => a.setAttribute('target', '_top'));
  new MutationObserver((mutationList) => {
    for (const mutation of mutationList) {
      if (mutation.type === 'childList') {
        for (const an of mutation.addedNodes) {
          for (const node of getChildElementsRecursive(an)) {
            if (node.nodeName === 'A' && !node.hasAttribute('target')) {
              node.setAttribute('target', '_top');
            }
          }
        }
      }
    }
  }).observe(iframeDocument.body, { childList: true, subtree: true });
  // TODO: hook programmatic navigation?
  // TODO: cache-busting for plugin iframe .html and plugin.js files
}

function* getChildElementsRecursive(node: Node): Generator<Element> {
  if (node.nodeType === Node.ELEMENT_NODE) {
    yield node as Element;
  }
  for (const child of node.childNodes) {
    yield* getChildElementsRecursive(child);
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

