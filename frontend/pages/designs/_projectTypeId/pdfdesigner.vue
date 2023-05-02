<template>
  <div>
    <splitpanes class="default-theme">
      <pane :size="previewSplitSize">
        <edit-toolbar v-bind="toolbarAttrs" v-on="toolbarEvents">
          <template #title>{{ projectType.name }}</template>

          <template #default>
            <s-btn 
              :loading="pdfRenderingInProgress" 
              :disabled="pdfRenderingInProgress" 
              @click="loadPdf"
              color="secondary"
            >
              <v-icon>mdi-cached</v-icon>
              Refresh PDF

              <template #loader>
                <saving-loader-spinner />
                Refresh PDF
              </template>
            </s-btn>
          </template>
        </edit-toolbar>

        <v-tabs grow>
          <v-tab>HTML</v-tab>
          <v-tab-item>
            <fill-screen-height>
              <code-editor 
                v-model="projectType.report_template" 
                language="html" 
                class="pdf-code-editor" 
                :disabled="readonly"
              />
            </fill-screen-height>
          </v-tab-item>

          <v-tab>CSS</v-tab>
          <v-tab-item>
            <fill-screen-height>
              <code-editor 
                v-model="projectType.report_styles" 
                language="css" 
                class="pdf-code-editor" 
                :disabled="readonly"
              />
            </fill-screen-height>
          </v-tab-item>

          <v-tab>Assets</v-tab>
          <v-tab-item>
            <fill-screen-height>
              <asset-manager :project-type="projectType" :disabled="readonly" />
            </fill-screen-height>
          </v-tab-item>

          <v-tab>Preview Data</v-tab>
          <v-tab-item>
            <pdf-preview-data-form v-model="projectType.report_preview_data" :project-type="projectType" :disabled="readonly" />
          </v-tab-item>
        </v-tabs>
      </pane>

      <pane :size="100 - previewSplitSize">
        <!-- PDF preview -->
        <pdf-preview ref="pdfpreview" :fetch-pdf="fetchPdf" @renderprogress="pdfRenderingInProgress = $event" />
      </pane>
    </splitpanes>
  </div>
</template>

<script>
import { Splitpanes, Pane } from 'splitpanes';
import urlJoin from 'url-join';
import ProjectTypeLockEditMixin from '~/mixins/ProjectTypeLockEditMixin';

export default {
  components: { Splitpanes, Pane },
  mixins: [ProjectTypeLockEditMixin],
  data() {
    return {
      previewSplitSize: 60,
      pdfRenderingInProgress: false,
    }
  },
  watch: {
    projectType: {
      deep: true,
      handler() {
        this.loadPdf(false);
      },
    }
  },
  methods: {
    async fetchPdf() {
      return await this.$axios.$post(urlJoin(this.getBaseUrl(this.data), '/preview/'), this.projectType, {
        responseType: 'arraybuffer',
      });
    },
    loadPdf(immediate = true) {
      if (immediate) {
        this.$refs.pdfpreview.reloadImmediate();
      } else {
        this.$refs.pdfpreview.reloadDebounced();
      }
    },
    async performSave(data) {
      await this.$store.dispatch('projecttypes/partialUpdate', { obj: data, fields: ['report_template', 'report_styles', 'report_preview_data'] });
    },
  },
}
</script>

<style lang="scss">
@import '@/assets/splitpanes.scss';

.pdf-code-editor {
  height: 100%;
}
</style>
