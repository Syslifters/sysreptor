<template>
  <fill-screen-height>
    <pdf :value="pdfData" />
    <v-overlay v-if="pdfRenderErrors" color="grey darken-4" opacity="0.7" absolute>
      <error-list :value="pdfRenderErrors" />
    </v-overlay>
    <v-overlay v-else-if="!pdfData || (renderingInProgress && showLoadingSpinnerOnReload)" absolute>
      <div class="initial-loading">
        <v-progress-circular indeterminate />
      </div>
    </v-overlay>
  </fill-screen-height>
</template>

<script>
import { debounce } from 'lodash';

export default {
  props: {
    fetchPdf: {
      type: Function,
      required: true,
    },
    reloadDebounceTime: {
      type: Number,
      default: 30 * 1000,
    },
    showLoadingSpinnerOnReload: {
      type: Boolean,
      default: false,
    },
  },
  data() {
    return {
      pdfData: null,
      pdfRenderErrors: null,
      renderingInProgress: true,
    }
  },
  created() {
    this.reloadDebounced = debounce(this.reload, this.reloadDebounceTime);
  },
  mounted() {
    this.reloadImmediate();
  },
  destroyed() {
    this.reloadDebounced.cancel();
  },
  methods: {
    async reload() {
      this.renderingInProgress = true;
      this.$emit('renderprogress', true);
      try {
        const res = await this.fetchPdf();
        this.pdfData = new Uint8Array(res);
        this.pdfRenderErrors = null;
      } catch (error) {
        if (error?.response?.status === 400) {
          this.pdfRenderErrors = JSON.parse(String.fromCharCode.apply(null, new Uint8Array(error.response.data))) || {};
        } else {
          this.$toast.global.requestError({ error, message: 'PDF rendering error' });
        }
      }
      this.renderingInProgress = false;
      this.$emit('renderprogress', false);
    },
    reloadImmediate() {
      this.reloadDebounced();
      this.reloadDebounced.flush();
    },
  }
}
</script>

<style lang="scss" scoped>
:deep(.v-overlay__content) {
  width: 100%;
  height: 100%;
  overflow-y: auto;
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
</style>
