<template>
  <div class="h-100 d-flex flex-column pos-relative">
    <pdf :value="pdfData" class="flex-grow-height" />

    <v-footer theme="dark" class="footer">
      <v-btn @click="showMessages = !showMessages" size="small" block class="footer-btn" :ripple="false">
        <v-spacer />
        <span class="mr-6"><v-icon start size="small" color="error" icon="mdi-close-circle" /> {{ messages.filter(m => m.level === MessageLevel.ERROR).length }}</span>
        <span class="mr-6"><v-icon start size="small" color="warning" icon="mdi-alert" /> {{ messages.filter(m => m.level === MessageLevel.WARNING).length }}</span>
        <span><v-icon start size="small" color="info" icon="mdi-message-text" /> {{ messages.filter(m => m.level === MessageLevel.INFO).length }}</span>
      </v-btn>
    </v-footer>

    <v-overlay
      :model-value="showMessages"
      persistent
      no-click-animation
      scroll-strategy="none"
      transition="none"
      contained
      z-index="10"
    >
      <error-list :value="messages" :show-no-message-info="true" class="mt-5" />
    </v-overlay>
    <v-overlay
      :model-value="renderingInProgress && (!pdfData || props.showLoadingSpinnerOnReload)"
      persistent
      no-click-animation
      transition="none"
      contained
      z-index="20"
    >
      <div class="initial-loading">
        <v-progress-circular indeterminate size="50" />
      </div>
    </v-overlay>
  </div>
</template>

<script setup lang="ts">
import { debounce } from "lodash-es"
import { MessageLevel } from '#imports'

const props = withDefaults(defineProps<{
  fetchPdf: () => Promise<PdfResponse>;
  reloadDebounceTime?: number;
  showLoadingSpinnerOnReload?: boolean
}>(), {
  reloadDebounceTime: 30 * 1000,
  showLoadingSpinnerOnReload: false,
});

const pdfData = ref<string|null>(null);
const renderingInProgress = ref(false);
const messages = ref<ErrorMessage[]>([]);
const showMessages = ref(false);

async function reload() {
  renderingInProgress.value = true;
  try {
    const res = await props.fetchPdf();
    messages.value = res.messages;
    if (messages.value.length === 0) {
      showMessages.value = false;
    }
    if (res.pdf) {
      pdfData.value = res.pdf;
    } else {
      showMessages.value = true;
    }
  } catch (error: any) {
    let details = null;
    if (error?.data?.detail) {
      details = error?.data?.detail;
    } else if (Array.isArray(error?.data) && error?.data?.length === 1) {
      details = error?.data[0];
    } else if (error?.status === 429) {
      details = 'Exceeded PDF rendering rate limit. Try again later.'
    }
    messages.value.push({
      level: MessageLevel.ERROR,
      message: 'PDF rendering error',
      details,
      location: {
        type: MessageLocationType.OTHER,
        id: null,
        name: null,
        path: null
      }
    });
    showMessages.value = true;
  } finally {
    renderingInProgress.value = false;
  }
}
const reloadDebounced = debounce(reload, props.reloadDebounceTime);
function reloadImmediate() {
  reloadDebounced();
  reloadDebounced.flush();
}
onMounted(() => {
  reloadImmediate();
})

defineExpose({
  pdfData,
  renderingInProgress,
  reloadDebounced,
  reloadImmediate,
})
</script>

<style lang="scss" scoped>
.v-overlay {
  color: white;

  :deep(.v-overlay__content) {
    width: 100%;
    height: 100%;
    overflow-y: auto;
  }
  :deep(.v-overlay__scrim) {
    background-color: black;
    opacity: 0.7;
  }
}

.initial-loading {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;

  & > * {
    margin-top: auto;
    margin-bottom: auto;
    align-self: center;
  }
}

.footer {
  z-index: 11;
  padding: 0;
}
.footer-btn {
  width: 100%;
  :deep(.v-btn__content) {
    width: 100%;
    display: flex;
    flex-direction: row;
  }
}

.pos-relative {
  position: relative;
}
</style>
