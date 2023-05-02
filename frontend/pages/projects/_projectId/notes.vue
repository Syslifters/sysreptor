<template>
  <split-menu v-model="menuSize">
    <template #menu>
      <v-list dense>
        <v-list-item-title class="text-h6 pl-2">{{ project.name }}</v-list-item-title>

        <notes-sortable-list 
          :value="noteGroups" 
          @input="updateNoteOrder"
          @update:note="updateNote"
          :disabled="project.readonly" 
          :to-prefix="`/projects/${$route.params.projectId}/notes/`"
        />
        
        <v-list-item>
          <v-list-item-action>
            <btn-confirm 
              :action="createNote"
              :disabled="project.readonly"
              :confirm="false"
              button-text="Add"
              button-icon="mdi-plus"
              tooltip-text="Add Note"
              small
            />
          </v-list-item-action>
        </v-list-item>
      </v-list>
    </template>

    <template #default>
      <nuxt-child />
    </template>
  </split-menu>
</template>

<script>
import { debounce } from 'lodash';

export default {
  async asyncData({ store, params }) {
    const project = store.dispatch('projects/getById', params.projectId);
    const notes = store.dispatch('projects/getNotes', params.projectId);
    await Promise.all([project, notes]);
    return { project: await project };
  },
  data() {
    return {
      refreshListingsInterval: null,
    }
  },
  head: {
    title: 'Notes',
  },
  computed: {
    noteGroups() {
      return this.$store.getters['projects/noteGroups'](this.project.id);
    },
    menuSize: {
      get() {
        return this.$store.state.settings.notebookInputMenuSize;
      },
      set(val) {
        this.$store.commit('settings/updateNotebookInputMenuSize', val);
      }
    },
  },
  created() {
    // Execute in next tick: prevent two requests for events in the same tick
    this.updateNoteOrder = debounce(this.updateNoteOrder_, 0);
  },
  mounted() {
    this.refreshListingsInterval = setInterval(this.refreshListings, 10_000);
  },
  beforeDestroy() {
    if (this.refreshListingsInterval !== null) {
      clearInterval(this.refreshListingsInterval);
      this.refreshListingsInterval = null;
    }
  },
  methods: {
    async refreshListings() {
      try {
        await this.$store.dispatch('projects/fetchNotes', this.project.id);
      } catch (error) {
        // hide error
      }
    },
    async createNote() {
      const currentNote = this.$store.getters['projects/notes'](this.project.id).find(n => n.id === this.$route.params.noteId);
      const obj = await this.$store.dispatch('projects/createNote', {
        projectId: this.project.id,
        note: { 
          title: "New Note",
          // Insert new note after the currently selected note, or at the end of the list
          parent: currentNote?.parent || null,
          order: currentNote ? currentNote.order + 1 : null,
          checked: [true, false].includes(currentNote?.checked) ? false : null,
        } 
      });
      // Reload note list to get updated order
      this.refreshListings();
      
      this.$router.push(`/projects/${this.project.id}/notes/${obj.id}/`);
    },
    async updateNote(note) {
      try {
        await this.$store.dispatch('projects/partialUpdateNote', { projectId: this.project.id, note, fields: ['checked'] });
      } catch (error) {
        this.$toast.global.requestError({ error });
      }
    },
    async updateNoteOrder_(val) {
      try {
        await this.$store.dispatch('projects/sortNotes', { projectId: this.project.id, noteGroups: val });
      } catch (error) {
        this.$toast.global.requestError({ error });
      }
    },
  },
}
</script>

<style lang="scss" scoped>
.note-checked {
  display: inline-block;
  margin: 0;
  padding: 0;

  :deep() {
    .v-input--selection-controls__input {
      margin-right: 0;
      height: auto;
      width: auto;
    }
    .v-icon.v-icon--dense {
      font-size: 1em;
    }
  }
}
</style>
