<template>
  <iframe
    ref="iframeRef"
    :src="iframeUrl"
    class="iframe-container"
    :class="{
      'iframe-loading': loadingIndicator.isLoading.value,
    }"
    :style="{ 
      colorScheme: theme.current.value.dark ? 'dark': 'light',
    }"
    @load="onIframeLoaded"
    v-bind="attrs"
  />
</template>

<script setup lang="ts">
const props = defineProps<{
  src: string;
}>();

const router = useRouter();
const route = useRoute();
const theme = useTheme();
const attrs = useAttrs();
const loadingIndicator = useLoadingIndicator();
loadingIndicator.start();

const iframeRef = ref<HTMLIFrameElement>();
const iframeUrl = computed(() => {
  const url = new URL(props.src, window.location.href);
  // Append current query to iframe URL
  new URLSearchParams(route.query as Record<string, string>).forEach((value, key) => url.searchParams.append(key, value));
  // Append route params as query to iframe URL
  new URLSearchParams(route.params as Record<string, string>).forEach((value, key) => url.searchParams.append(key, value));
  return url.toString();
});


function onIframeLoaded() {
  // Hook navigation inside iframe: redirect to top-level navigation outside of iframe
  // Add target="_top" to all <a> tags inside iframe
  const iframeWindow = iframeRef.value!.contentWindow!;
  iframeWindow.document.querySelectorAll('a:not([target])')
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
  }).observe(iframeWindow.document.body, { childList: true, subtree: true });

  // Patch window.open
  const windowOpenOriginal = iframeWindow.open;
  iframeWindow.open = (url?: string, target?: string, features?: string) => {
    if (!target) {
      target = '_top';
    }
    return windowOpenOriginal(url, target, features);
  };
  // Hook navigation events (Chrome only)
  (iframeWindow as any).navigation?.addEventListener('navigate', (event: any) => {
    if (event.hashChange || event.downloadRequest || event.formData || !event.cancelable || event.destination.sameDocument) {
      return;
    }
    event.preventDefault();
    iframeWindow.open(event.destination.url, '_top');
  })

  // Disable loading animation
  if (iframeWindow.document.readyState === 'loading') {
    iframeWindow.document.addEventListener('load', () => loadingIndicator.finish());
  } else {
    loadingIndicator.finish();
  }
}

function* getChildElementsRecursive(node: Node): Generator<Element> {
  if (node.nodeType === Node.ELEMENT_NODE) {
    yield node as Element;
  }
  for (const child of node.childNodes) {
    yield* getChildElementsRecursive(child);
  }
}


// Redirect native top-level navigation to nuxt navigation.
// Speed up navigation performance and prevent flashing pages (supported only in Chrome)
onMounted(() => {
  (window as any).navigation?.addEventListener('navigate', onNavigate, { once: true });
});
onUnmounted(() => {
  (window as any).navigation?.removeEventListener('navigate', onNavigate);
});
function onNavigate(event: any) {
  if (!['push', 'traverse'].includes(event.navigationType) || !event.cancelable || new URL(event.destination.url).origin !== window.location.origin) {
    return;
  }
  
  const resolvedRoute = router.resolve('/' + event.destination.url.split('/').slice(3).join('/'));
  if (resolvedRoute) {
    event.preventDefault();
    navigateTo(resolvedRoute);
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

