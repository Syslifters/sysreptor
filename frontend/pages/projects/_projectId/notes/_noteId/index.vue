<template>
  <fetch-loader v-bind="fetchLoaderAttrs">
    <div v-if="project && note" :key="project.id + note.id">
      <edit-toolbar v-bind="toolbarAttrs" v-on="toolbarEvents" :can-auto-save="true">
        <template #default>
          <v-checkbox 
            value :input-value="note.checked === false ? false : true" :indeterminate="note.checked === null"
            @change="note.checked = note.checked === null ? false : note.checked === false ? true : null"
            :disabled="readonly"
            on-icon="mdi-checkbox-marked"
            off-icon="mdi-checkbox-blank-outline"
            indeterminate-icon="mdi-checkbox-blank-off-outline"
            color="inherit"
            hide-details
          />
          <s-emoji-picker-field
            v-if="note.checked === null"
            v-model="note.icon_emoji"
            :empty-icon="hasChildNotes ? 'mdi-folder-outline' : 'mdi-note-text-outline'"
            :disabled="readonly"
          />

          <v-toolbar-title class="note-title">
            <markdown-text-field-content
              v-model="note.title"
              :disabled="readonly"
              :lang="project.language"
              :spellcheck-supported="true"
            />
          </v-toolbar-title>

          <s-emoji-picker-field 
            v-model="note.status_emoji" 
            :disabled="readonly"
          />

          <div class="assignee-container ml-1 mr-1">
            <user-selection 
              v-model="note.assignee" 
              :selectable-users="project.members" 
              :disabled="readonly" 
              label="Assignee"
              :outlined="false" dense
            />
          </div>

          <s-btn @click="historyVisible = !historyVisible" color="secondary">
            <v-icon left>mdi-history</v-icon>
            Version History
          </s-btn>
        </template>

        <template #context-menu>
          <btn-export 
            :export-url="exportPdfUrl"
            :name="note.title"
            extension=".pdf"
            button-text="Export as PDF"
            list-item
          />
        </template>
      </edit-toolbar>

      <project-history-timeline 
        v-model="historyVisible"
        :project="project"
        :note="note"
      />

      <markdown-page 
        v-model="note.text"
        :disabled="readonly"
        :lang="project.language"
        :upload-file="uploadFile"
        :rewrite-file-url="rewriteFileUrl"
      />
    </div>
  </fetch-loader>
</template>

<script>
import urlJoin from 'url-join';
import { omit } from 'lodash';
import { uploadFileHelper } from '~/utils/upload';
import ProjectLockEditMixin from '~/mixins/ProjectLockEditMixin';

export default {
  mixins: [ProjectLockEditMixin],
  data() {
    return {
      note: null,
      project: null,
      historyVisible: false,
    }
  },
  async fetch() {
    const [project, note] = await Promise.all([
      this.$store.dispatch('projects/getById', this.$route.params.projectId),
      this.$axios.$get(this.getBaseUrl({ id: this.$route.params.noteId })),
    ]);
    this.project = project;
    this.note = note;
  },
  computed: {
    data() {
      return this.note;
    },
    hasChildNotes() {
      return this.$store.getters['projects/notes'](this.project.id)
        .some(n => n.parent === this.note.id && n.id !== this.note.id);
    },
    exportPdfUrl() {
      return urlJoin(this.baseUrl, '/export-pdf/');
    },
  },
  methods: {
    getBaseUrl(data) {
      return urlJoin(this.projectUrl, `/notes/${data.id}/`)
    },
    async uploadFile(file) {
      const obj = await uploadFileHelper(this.$axios, urlJoin(this.projectUrl, '/upload/'), file);
      if (obj.resource_type === 'file') {
        return `[${obj.name}](/files/name/${obj.name})`;
      } else {
        return `![](/images/name/${obj.name})`;
      }
    },
    async performSave(data) {
      await this.$store.dispatch('projects/updateNote', { projectId: this.project.id, note: data });
    },
    async performDelete(data) {
      await this.$store.dispatch('projects/deleteNote', { projectId: this.project.id, noteId: data.id });
      this.$router.push(`/projects/${this.project.id}/notes/`);
    },
    updateInStore(data) {
      this.$store.commit('projects/setNote', { projectId: this.project.id, note: omit(data, ['parent', 'order']) });
    },
    async onUpdateData({ oldValue, newValue }) {
      const toolbar = this.getToolbarRef();
      if (toolbar?.autoSaveEnabled && (
        oldValue.checked !== newValue.checked ||
        oldValue.status_emoji !== newValue.status_emoji ||
        oldValue.icon_emoji !== newValue.icon_emoji
      )) {
        await toolbar.performSave();
      }
    },
  },
}
</script>

<style lang="scss" scoped>
.note-title {
  width: 100%;
}

.assignee-container {
  width: 17em;
  min-width: 17em;
}
</style>
