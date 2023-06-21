<template>
  <div>
    <fill-screen-height class="d-flex flex-column">
      <pdf :value="pdfData" class="flex-grow-1" />

      <v-footer padless dark class="footer">
        <v-btn @click="showMessages = !showMessages" small width="100%" :ripple="false">
          <v-spacer />
          <span class="mr-6"><v-icon left small color="error">mdi-close-circle</v-icon> {{ messages.filter(m => m.level === 'error' ).length }}</span>
          <span class="mr-6"><v-icon left small color="warning">mdi-alert</v-icon> {{ messages.filter(m => m.level === 'warning' ).length }}</span>
          <span><v-icon left small color="info">mdi-message-text</v-icon> {{ messages.filter(m => m.level === 'info' ).length }}</span>
        </v-btn>
      </v-footer>

      <v-overlay v-if="showMessages" color="grey darken-4" opacity="0.7" absolute>
        <error-list :value="messages" :show-no-message-info="true" class="mt-5" />
      </v-overlay>
      <v-overlay v-else-if="renderingInProgress && (!pdfData || showLoadingSpinnerOnReload)" absolute z-index="20">
        <div class="initial-loading">
          <v-progress-circular indeterminate />
        </div>
      </v-overlay>
    </fill-screen-height>
  </div>
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
      messages: [],
      renderingInProgress: true,
      showMessages: false,
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
        this.messages = res.messages;
        if (this.messages.length === 0) {
          this.showMessages = false;
        }
        if (res.pdf) {
          this.pdfData = res.pdf;
        } else {
          this.showMessages = true;
        }
      } catch (error) {
        let details = null;
        if (error?.response?.data?.detail) {
          details += ': ' + error?.response?.data?.detail;
        } else if (Array.isArray(error?.response?.data) && error?.response?.data?.length === 1) {
          details += ': ' + error?.response?.data[0];
        } else if (error?.response?.status === 429) {
          details = 'Exceeded PDF rendering rate limit. Try again later.'
        }
        this.messages.push({
          level: 'error',
          message: 'PDF rendering error',
          details,
        });
        this.showMessages = true;
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

.footer {
  z-index: 10;
}
</style>
