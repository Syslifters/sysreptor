<template>
  <div>
    <splitpanes class="default-theme">
      <pane :size="previewSplitSize">
        <edit-toolbar v-bind="toolbarAttrs" v-on="toolbarEvents">
          <template #title>{{ project.name }}</template>

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
          <v-tab>HTML+Vue</v-tab>
          <v-tab-item>
            <fill-screen-height>
              <design-code-editor 
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
              <design-code-editor 
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
              <design-asset-manager :project-type="projectType" :disabled="readonly" />
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
import { pick } from 'lodash';
import LockEditMixin from '~/mixins/LockEditMixin';

export default {
  components: { Splitpanes, Pane },
  mixins: [LockEditMixin],
  async asyncData({ $axios, store, params }) {
    const project = await store.dispatch('projects/getById', params.projectId);
    const projectType = await $axios.$get(`/projecttypes/${project.project_type}/`);
    return { project, projectType };
  },
  data() {
    return {
      previewSplitSize: 60,
      pdfRenderingInProgress: false,
    }
  },
  head: {
    title: 'Designs',
  },
  computed: {
    data() {
      return this.projectType;
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
    getBaseUrl(data) {
      return `/projecttypes/${data.id}/`;
    },
    async fetchPdf() {
      return await this.$axios.$post(`/pentestprojects/${this.project.id}/preview/`, pick(this.projectType, ['report_template', 'report_styles']));
    },
    loadPdf(immediate = true) {
      if (immediate) {
        this.$refs.pdfpreview.reloadImmediate();
      } else {
        this.$refs.pdfpreview.reloadDebounced();
      }
    },
    async performSave(data) {
      await this.$store.dispatch('projecttypes/partialUpdate', { obj: data, fields: ['report_template', 'report_styles'] });
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
