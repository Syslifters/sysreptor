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

          <s-btn 
            v-if="$store.getters['projects/notes'](project.id).map(n => n.id).includes(note.id)" 
            :to="`/projects/${$route.params.projectId}/notes/${$route.params.noteId}/`" nuxt exact 
            color="secondary" 
            class="ml-1 mr-1"
          >
            <v-icon left>mdi-undo</v-icon>
            Back to current version
          </s-btn>

          <s-btn @click="historyVisible = !historyVisible" color="secondary">
            <v-icon left>mdi-history</v-icon>
            Version History
          </s-btn>
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
import ProjectHistoryMixin from '~/mixins/ProjectHistoryMixin';

export default {
  mixins: [ProjectHistoryMixin],
  data() {
    return {
      note: null,
      project: null,
      historyVisible: false,
    }
  },
  async fetch() {
    const [note, project] = await Promise.all([
      this.$axios.$get(this.getBaseUrl({ id: this.$route.params.noteId })),
      this.$axios.$get(this.projectUrl),
    ]);
    this.project = project;
    this.note = note;
  },
  computed: {
    data() {
      return this.note;
    },
    hasChildNotes() {
      return false;
    },
  },
  methods: {
    getBaseUrl(data) {
      return urlJoin(this.projectUrl, `/notes/${data.id}/`)
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
