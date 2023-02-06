<template>
  <div>
    <splitpanes class="default-theme">
      <pane :size="previewSplitSize">
        <pdf-preview ref="pdfpreview" :fetch-pdf="fetchPreviewPdf" :show-loading-spinner-on-reload="true" />
      </pane>

      <pane :size="100 - previewSplitSize">
        <fill-screen-height>
          <v-container>
            <h1>{{ project.name }}</h1>

            <v-form class="pa-4">
              <!-- Design actions -->
              <div>
                <btn-confirm
                  :action="customizeDesign"
                  button-text="Customize Design"
                  button-icon="mdi-file-cog"
                  tooltip-text="Customize Design for this project"
                  dialog-text="Customize the current Design for this project. This allows you to adapt the appearence (HTML, CSS) of the design for this project only. The original design is not affected. Any changes made to the original design will not be automatically applied to the adapted design."
                  :disabled="project.readonly || projectType.source === 'customized'"
                />
                <s-btn 
                  :to="`/designer/${projectType.id}/pdfdesigner/`" 
                  :disabled="!$auth.hasScope('designer') || ['customized', 'imported_dependency'].includes(projectType.source)"
                  nuxt
                  color="secondary"
                >
                  <v-icon>mdi-file-edit</v-icon>
                  Edit Original Design
                </s-btn>
              </div>

              <!-- Set password for encrypting report -->
              <div>
                <s-checkbox v-model="form.encryptReport" label="Encrypt report PDF" />
                <s-text-field
                  v-if="form.encryptReport"
                  v-model="form.password"
                  :error-messages="(form.encryptReport && form.password.length === 0) ? ['Password required'] : []"
                  label="PDF password"
                  append-icon="mdi-lock-reset" @click:append="form.password = generateNewPassword()"
                  class="mt-4"
                />
              </div>

              <!-- Filename -->
              <div>
                <s-text-field 
                  v-model="form.filename"
                  label="Filename"
                  :rules="rules.filename"
                  class="mt-4"
                />
              </div>

              <div class="mt-4">
                <btn-confirm
                  :disabled="!canGenerateFinalReport"
                  :action="generateFinalReport"
                  :confirm="false"
                  button-text="Download"
                  button-icon="mdi-download"
                  button-color="primary"
                />
              </div>
              <div class="mt-4">
                <btn-readonly 
                  v-if="!project.readonly"
                  :value="project.readonly"
                  :set-readonly="setReadonly"
                  :disabled="!canGenerateFinalReport"
                />
              </div>
            </v-form>

            <error-list :value="[checkMessages, $refs.pdfpreview?.pdfRenderErrors]" :group="true">
              <template #location="{msg}">
                <NuxtLink v-if="messageLocationUrl(msg)" :to="messageLocationUrl(msg)" target="_blank">
                  in {{ msg.location.type }}
                  <template v-if="msg.location.name">"{{ msg.location.name }}"</template>
                  <template v-if="msg.location.path">field "{{ msg.location.path }}"</template>
                </NuxtLink>
                <span v-else-if="msg.location.name">
                  in {{ msg.location.type }}
                  <template v-if="msg.location.name">"{{ msg.location.name }}"</template>
                  <template v-if="msg.location.path">field "{{ msg.location.path }}"</template>
                </span>
              </template>
            </error-list>
          </v-container>
        </fill-screen-height>
      </pane>
    </splitpanes>
  </div>
</template>

<script>
import { Splitpanes, Pane } from 'splitpanes';
import fileDownload from 'js-file-download';
import { sampleSize } from 'lodash';

export default {
  components: { Splitpanes, Pane },
  async asyncData({ params, store }) {
    const project = await store.dispatch('projects/getById', params.projectId);
    const projectType = await store.dispatch('projecttypes/getById', project.project_type);
    return { project, projectType };
  },
  data() {
    return {
      previewSplitSize: 50,
      checkMessages: {},
      form: {
        encryptReport: true,
        password: this.generateNewPassword(),
        filename: 'report.pdf',
      },
      rules: {
        filename: [v => (Boolean(v) && /^[^/\\]+$/.test(v)) || 'Invalid filename'],
      }
    }
  },
  computed: {
    hasErrors() {
      return this.$refs.pdfpreview?.pdfRenderErrors?.length > 0 || (this.checkMessages?.error || []).length > 0;
    },
    canGenerateFinalReport() {
      return !this.reportGenerationInProgress && !this.hasErrors && this.$refs.pdfpreview?.pdfData !== null &&
        (this.form.encryptReport ? this.form.password.length > 0 : true);
    },
  },
  mounted() {
    this.performChecks();
  },
  methods: {
    async fetchPreviewPdf() {
      return await this.$axios.$post(`/pentestprojects/${this.project.id}/preview/`, {}, {
        responseType: 'arraybuffer',
      });
    },
    async performChecks() {
      try {
        this.checkMessages = await this.$axios.$get(`/pentestprojects/${this.project.id}/check/`);
      } catch (error) {
        this.$toast.global.requestError({ error });
      }
    },
    async generateFinalReport() {
      const res = await this.$axios.$post(`/pentestprojects/${this.project.id}/generate/`, {
        password: this.form.encryptReport ? this.form.password : null,
      }, {
        responseType: 'arraybuffer',
      });
      fileDownload(res, this.form.filename.endsWith('.pdf') ? this.form.filename : this.form.filename + '.pdf');
    },
    async setReadonly() {
      await this.$store.dispatch('projects/setReadonly', { projectId: this.project.id, readonly: true });
    },
    async customizeDesign() {
      await this.$store.dispatch('projects/customizeDesign', { projectId: this.project.id });
      this.$router.push({ path: `/projects/${this.project.id}/designer/` });
    },
    messageLocationUrl(msg) {
      if (!msg || !msg.location) {
        return null;
      } else if (msg.location.type === 'section') {
        return `/projects/${this.project.id}/reporting/sections/${msg.location.id}/` + (msg.location.path ? '#' + msg.location.path : '');
      } else if (msg.location.type === 'finding') {
        return `/projects/${this.project.id}/reporting/findings/${msg.location.id}/` + (msg.location.path ? '#' + msg.location.path : '');
      } else if (msg.location.type === 'design') {
        return `/designer/${this.project.project_type}/pdfdesigner/`;
      }

      return null;
    },
    generateNewPassword() {
      // Charset does not contain similar-looking characters and numbers; removed: 0,O, 1,l,I
      const charset = '23456789' + 'abcdefghijkmnopqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ' + '!#%&+-_';
      return sampleSize(charset, 20).join('');
    },
  }
}
</script>

<style lang="scss" scoped>
@import '@/assets/splitpanes.scss';

.pane-scrollable {
  overflow-y: auto;
}
</style>
