<template>
  <div>
    <splitpanes class="default-theme">
      <pane :size="previewSplitSize">
        <pdf-preview ref="pdfpreview" :fetch-pdf="fetchPreviewPdf" :show-loading-spinner-on-reload="true" />
      </pane>

      <pane :size="100 - previewSplitSize">
        <fill-screen-height>
          <h1>Publish Report: {{ project.name }} <template v-if="project.readonly">(readonly)</template></h1>

          <v-form class="pa-4">
            <!-- Set password for encrypting report -->
            <div>
              <s-checkbox v-model="form.encryptReport" label="Encrypt report PDF" />
              <s-text-field
                v-if="form.encryptReport"
                v-model="form.password"
                :error-messages="(form.encryptReport && form.password.length === 0) ? ['Password required'] : []"
                label="PDF password"
                hint="Encrypt the PDF with this password"
                append-icon="mdi-lock-reset" @click:append="form.password = generateNewPassword()"
                class="mt-4"
              />
            </div>

            <!-- Set readonly -->
            <div>
              <s-checkbox v-if="!project.readonly" v-model="form.readonly" label="Mark project as finished and set it readonly" />
            </div>

            <!-- Render as different design -->
            <div>
              <s-checkbox v-model="form.renderWithDifferentProjectType" label="Render report PDF with different design" />
              <template v-if="form.renderWithDifferentProjectType">
                <v-alert type="warning" dense>
                  Different designs might have conflicting report and/or finding fields.<br>
                  Check the resulting PDF if everything is rendered as expected or if some fields are missing.
                </v-alert>
                <project-type-selection
                  :value="form.projectType || projectType" 
                  @input="changeDesign"
                  :return-object="true"
                  class="mt-4"
                />
              </template>
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

            <s-btn
              type="submit"
              :disabled="!canGenerateFinalReport"
              :loading="reportGenerationInProgress"
              @click.prevent="generateFinalReport"
              color="primary"
              class="mt-4"
            >
              <v-icon>mdi-download</v-icon>
              Generate Final Report
            </s-btn>
          </v-form>

          <error-list :value="checkMessages">
            <template #message="{msg}">
              {{ msg.message }}
              <NuxtLink v-if="messageLocationUrl(msg)" :to="messageLocationUrl(msg)" class="error-location">
                in {{ msg.location.type }}
                <template v-if="msg.location.name">"{{ msg.location.name }}"</template>
                <template v-if="msg.location.path">field "{{ msg.location.path }}"</template>
              </NuxtLink>
              <span v-else-if="msg.location.name" class="error-location">
                in {{ msg.location.type }}
                <template v-if="msg.location.name">"{{ msg.location.name }}"</template>
                <template v-if="msg.location.path">field "{{ msg.location.path }}"</template>
              </span>
            </template>
          </error-list>
        </fill-screen-height>
      </pane>
    </splitpanes>
  </div>
</template>

<script>
import { Splitpanes, Pane } from 'splitpanes';
import fileDownload from 'js-file-download';
import { sampleSize } from 'lodash';
import PdfPreview from '~/components/PdfPreview.vue'
import ErrorList from '~/components/ErrorList.vue';
import FillScreenHeight from '~/components/FillScreenHeight.vue';
import ProjectTypeSelection from '~/components/ProjectTypeSelection.vue';

export default {
  components: { Splitpanes, Pane, PdfPreview, ErrorList, FillScreenHeight, ProjectTypeSelection },
  async asyncData({ params, store }) {
    const project = await store.dispatch('projects/getById', params.projectId);
    const projectType = await store.dispatch('projecttypes/getById', project.project_type);
    return { project, projectType };
  },
  data() {
    return {
      previewSplitSize: 50,
      reportGenerationInProgress: false,
      checkMessages: {},
      form: {
        encryptReport: true,
        password: this.generateNewPassword(),
        renderWithDifferentProjectType: false,
        projectType: null,
        readonly: false,
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
      return await this.$axios.$post(`/pentestprojects/${this.project.id}/preview/`, {
        project_type: this.form.renderWithDifferentProjectType ? this.form.projectType?.id : null,
      }, {
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
      this.reportGenerationInProgress = true;
      try {
        const res = await this.$axios.$post(`/pentestprojects/${this.project.id}/generate/`, {
          password: this.form.encryptReport ? this.form.password : null,
          readonly: this.form.readonly,
          project_type: this.form.renderWithDifferentProjectType ? this.form.projectType?.id : null,
        }, {
          responseType: 'arraybuffer',
        });
        fileDownload(res, this.form.filename.endsWith('.pdf') ? this.form.filename : this.form.filename + '.pdf');

        if (this.form.readonly) {
          // Remove project from store: invalidates cache
          this.$store.commit('projects/remove', this.project);
        }
      } catch (error) {
        this.$toast.global.requestError({ error });
      }
      this.reportGenerationInProgress = false;
    },
    messageLocationUrl(msg) {
      if (!msg || !msg.location) {
        return null;
      } else if (msg.location.type === 'section') {
        return `/projects/${this.project.id}/reporting/sections/${msg.location.id}/` + (msg.location.path ? '#' + msg.location.path : '');
      } else if (msg.location.type === 'finding') {
        return `/projects/${this.project.id}/reporting/findings/${msg.location.id}/` + (msg.location.path ? '#' + msg.location.path : '');
      } else if (msg.location.type === 'template') {
        return `/designer/${this.project.project_type}/pdfdesigner/`;
      }

      return null;
    },
    generateNewPassword() {
      // Charset does not contain similar-looking characters and numbers; removed: 0,O, 1,l,I
      const charset = '23456789' + 'abcdefghijkmnopqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ' + '!#%&+-_';
      return sampleSize(charset, 32).join('');
    },
    changeDesign(projectType) {
      this.form.projectType = projectType;
      this.$refs.pdfpreview.reloadImmediate();
    }
  }
}
</script>
