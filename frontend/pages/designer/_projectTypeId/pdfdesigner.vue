<template>
  <div>
    <splitpanes class="default-theme">
      <pane :size="previewSplitSize">
        <edit-toolbar ref="toolbar" :data="projectType" :save="performSave">
          <template #title>{{ projectType.name }}</template>

          <template #default>
            <!-- TODO: allow users to enable/disable auto-refresh -->
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
              <code-editor v-model="projectType.report_template" language="html" class="pdf-code-editor" />
            </fill-screen-height>
          </v-tab-item>

          <v-tab>CSS</v-tab>
          <v-tab-item>
            <fill-screen-height>
              <code-editor v-model="projectType.report_styles" language="css" class="pdf-code-editor" />
            </fill-screen-height>
          </v-tab-item>

          <v-tab>Assets</v-tab>
          <v-tab-item>
            <fill-screen-height>
              <asset-manager :project-type="projectType" />
            </fill-screen-height>
          </v-tab-item>

          <v-tab>Preview Data</v-tab>
          <v-tab-item>
            <fill-screen-height>
              <pdf-preview-data-form v-model="projectType.report_preview_data" :project-type="projectType" />
            </fill-screen-height>
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
import FillScreenHeight from '~/components/FillScreenHeight.vue';
import AssetManager from '~/components/AssetManager.vue';
import PdfPreview from '~/components/PdfPreview.vue';

export default {
  components: { Splitpanes, Pane, FillScreenHeight, AssetManager, PdfPreview },
  beforeRouteLeave(to, from, next) {
    this.$refs.toolbar.beforeLeave(to, from, next);
  },
  beforeRouteUpdate(to, from, next) {
    this.$refs.toolbar.beforeLeave(to, from, next);
  },
  async asyncData({ $axios, params }) {
    return {
      projectType: await $axios.$get(`/projecttypes/${params.projectTypeId}/`),
    }
  },
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
      return await this.$axios.$post(`/projecttypes/${this.projectType.id}/preview/`, this.projectType, {
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
