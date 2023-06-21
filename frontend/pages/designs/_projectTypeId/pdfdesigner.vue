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

        <v-tabs v-model="currentTab" grow>
          <v-tab :value="0">Layout <v-icon right>mdi-flask</v-icon></v-tab>
          <v-tab :value="1">HTML+Vue</v-tab>
          <v-tab :value="2">CSS</v-tab>
          <v-tab :value="3">Assets</v-tab>
          <v-tab :value="4">Preview Data</v-tab>
        </v-tabs>
        <v-tabs-items v-model="currentTab">
          <v-tab-item :value="0">
            <design-layout-editor
              :project-type="projectType" 
              :upload-file="uploadFile"
              :rewrite-file-url="rewriteFileUrl"
              :disabled="readonly"
              @update="onUpdateCode"
              @jump-to-code="jumpToCode"
            />
          </v-tab-item>
          <v-tab-item :value="1">
            <fill-screen-height>
              <design-code-editor 
                ref="htmlEditor"
                v-model="projectType.report_template" 
                language="html" 
                class="pdf-code-editor" 
                :disabled="readonly"
              />
            </fill-screen-height>
          </v-tab-item>
          <v-tab-item :value="2">
            <fill-screen-height>
              <design-code-editor 
                ref="cssEditor"
                v-model="projectType.report_styles" 
                language="css" 
                class="pdf-code-editor" 
                :disabled="readonly"
              />
            </fill-screen-height>
          </v-tab-item>
          <v-tab-item :value="3">
            <fill-screen-height>
              <design-asset-manager :project-type="projectType" :disabled="readonly" />
            </fill-screen-height>
          </v-tab-item>
          <v-tab-item :value="4">
            <design-preview-data-form 
              v-model="projectType.report_preview_data" 
              :project-type="projectType" 
              :upload-file="uploadFile"
              :rewrite-file-url="rewriteFileUrl"
              :disabled="readonly"
            />
          </v-tab-item>
        </v-tabs-items>
      </pane>

      <pane :size="100 - previewSplitSize">
        <!-- PDF preview -->
        <pdf-preview ref="pdfpreview" :fetch-pdf="fetchPdf" @renderprogress="pdfRenderingInProgress = $event" />
      </pane>
    </splitpanes>

    <s-dialog v-model="showStartDialog">
      <template #title>Start Designing</template>
      <template #default>
        <v-card-text>
          <p>
            It looks like you haven't started designing your report yet.
            We recommend following approach:
          </p>
          <ol>
            <li>
              Before starting to design, define your 
              <nuxt-link :to="`/designs/${projectType.id}/reportfields/`">report fields</nuxt-link> and 
              <nuxt-link :to="`/designs/${projectType.id}/findingfields/`">finding fields</nuxt-link>
            </li>
            <li>Include base styles (click "Start Designing" below to add them)</li>
            <li>Define the report structure in "Layout"</li>
            <li>Customize the HTML and CSS to your needs via the code editors</li>
            <li>Hint: Use "Preview Data" to test your design</li>
          </ol>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <s-btn @click="showStartDialog = false" color="secondary">Cancel</s-btn>
          <s-btn @click="startDesigning" color="primary">Start Designing</s-btn>
        </v-card-actions>
      </template>
    </s-dialog>
  </div>
</template>

<script>
import { Splitpanes, Pane } from 'splitpanes';
import urlJoin from 'url-join';
import { uploadFileHelper } from '~/utils/upload';
import ProjectTypeLockEditMixin from '~/mixins/ProjectTypeLockEditMixin';
import { initialCss } from '~/components/Design/designer-components';

export default {
  components: { Splitpanes, Pane },
  mixins: [ProjectTypeLockEditMixin],
  data() {
    return {
      currentTab: 1, // HTML
      previewSplitSize: 60,
      pdfRenderingInProgress: false,
      showStartDialog: false,
    };
  },
  watch: {
    projectType: {
      deep: true,
      handler() {
        this.loadPdf(false);
      },
    }
  },
  mounted() {
    this.showStartDialog = !this.projectType.report_template && !this.projectType.report_styles && !this.readonly;
  },
  methods: {
    async fetchPdf() {
      return await this.$axios.$post(urlJoin(this.getBaseUrl(this.data), '/preview/'), this.projectType);
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
    async uploadFile(file) {
      const img = await uploadFileHelper(this.$axios, `/projecttypes/${this.projectType.id}/assets/`, file);
      return `![](/assets/name/${img.name})`;
    },
    rewriteFileUrl(imgSrc) {
      return urlJoin(`/projecttypes/${this.projectType.id}/`, imgSrc);
    },
    async jumpToCode({ tab, position }) {
      if (tab === 'html') {
        this.currentTab = 1;
        await this.$nextTick();
        await this.$nextTick();
        this.$refs.htmlEditor.jumpToPosition(position);
      } else if (tab === 'css') {
        this.currentTab = 2;
        await this.$nextTick();
        await this.$nextTick();
        this.$refs.cssEditor.jumpToPosition(position);
      }
    },
    async onUpdateCode({ html, css, formatHtml = false, reloadPdf = false }) {
      this.projectType.report_template = html;
      this.projectType.report_styles = css;
      if (formatHtml) {
        await this.$nextTick();
        this.$refs.htmlEditor.formatDocument();
      }
      if (reloadPdf) {
        await this.$nextTick();
        this.loadPdf(true);
      }
    },
    startDesigning() {
      this.showStartDialog = false;
      this.projectType.report_styles = initialCss;
      this.currentTab = 0; // Layout
    }
  },
}
</script>

<style lang="scss">
@import '@/assets/splitpanes.scss';

.pdf-code-editor {
  height: 100%;
}
</style>
