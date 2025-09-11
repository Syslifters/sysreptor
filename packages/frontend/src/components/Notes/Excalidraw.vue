<template>
  <iframe
    ref="iframeRef"
    :src="iframeSrc"
    @load="onIframeLoaded"
    class="iframe-container"
    :class="{
      'iframe-loading': loadingIndicator.isLoading.value,
      'iframe-fullscreen': iframeFullscreen,
    }"
    :style="{ 
      colorScheme: theme.current.value.dark ? 'dark': 'light',
    }"
    title="Excalidraw"
  />
</template>

<script setup lang="ts">

const props = defineProps<{
  apiUrl: string;
  websocketUrl?: string;
  readonly?: boolean;
}>();

const theme = useTheme();
const route = useRoute();
const apiSettings = useApiSettings();
const runtimeConfig = useRuntimeConfig();
const iframeRef = useTemplateRef('iframeRef');
const loadingIndicator = useLoadingIndicator();
onBeforeMount(() => loadingIndicator.start());

const iframeSrc = computed(() => `/static/excalidraw/dist/index.html?c=${runtimeConfig.app.buildId}#` + encodeParams({
  ...Object.fromEntries(new URLSearchParams(route.hash?.slice(1)).entries()),
  apiUrl: props.apiUrl,
  websocketUrl: (!props.readonly && apiSettings.settings!.features.websockets) ? props.websocketUrl : undefined,
}));


function onIframeLoaded() {
  loadingIndicator.finish();
}

function encodeParams(params: Record<string, string|undefined>): string {
  return new URLSearchParams(Object.entries(params).filter(([_, v]) => !!v) as [string, string][]).toString();
}


const iframeFullscreen = ref(false);
useEventListener(window, 'message', (event) => {
  if (event.source !== iframeRef.value?.contentWindow) {
    return;
  }
  if (event.data.type === 'toggleFullscreen') {
    iframeFullscreen.value = !iframeFullscreen.value;
  }
});

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

.iframe-fullscreen {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  z-index: 9999999;
  overflow: hidden;
}
</style>
