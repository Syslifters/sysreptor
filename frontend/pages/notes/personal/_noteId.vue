<template>
  <fetch-loader v-bind="fetchLoaderAttrs">
    <div v-if="note" :key="note.id">
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

          <v-toolbar-title class="note-title">
            <markdown-text-field-content
              v-model="note.title"
              :disabled="readonly"
              :lang="null"
              :spellcheck-supported="true"
            />
          </v-toolbar-title>

          <emoji-picker-field 
            v-model="note.emoji" 
            :disabled="readonly"
          />
        </template>
      </edit-toolbar>

      <markdown-page 
        v-model="note.text"
        :disabled="readonly"
        lang="auto"
        :upload-file="uploadFile"
        :rewrite-file-url="rewriteFileUrl"
      />
    </div>
  </fetch-loader>
</template>

<script>
import urlJoin from 'url-join';
import { uploadFileHelper } from '~/utils/upload';
import LockEditMixin from '~/mixins/LockEditMixin';

export default {
  mixins: [LockEditMixin],
  data() {
    return {
      note: null,
    }
  },
  async fetch() {
    this.note = await this.$axios.$get(this.getBaseUrl({ id: this.$route.params.noteId }));
  },
  computed: {
    data() {
      return this.note;
    },
  },
  methods: {
    getBaseUrl(data) {
      return `/pentestusers/self/notes/${data.id}/`;
    },
    async performSave(data) {
      await this.$store.dispatch('usernotes/update', data);
    },
    async performDelete(data) {
      await this.$store.dispatch('usernotes/delete', data);
      this.$router.push('/notes/personal/');
    },
    updateInStore(data) {
      this.$store.commit('usernotes/set', data);
    },
    async onUpdateData({ oldValue, newValue }) {
      if (this.$refs.toolbar?.autoSaveEnabled && (
        oldValue.checked !== newValue.checked ||
        oldValue.emoji !== newValue.emoji
      )) {
        await this.$refs.toolbar.performSave();
      }
    },
    async uploadFile(file) {
      const img = await uploadFileHelper(this.$axios, urlJoin('/pentestusers/self/notes/images/'), file);
      return `![](/images/name/${img.name})`;
    },
    rewriteFileUrl(imgSrc) {
      return urlJoin('/pentestusers/self/notes/', imgSrc);
    },
  },
}
</script>

<style lang="scss" scoped>
.note-title {
  width: 100%;
}
</style>
