<template>
  <split-menu v-model="menuSize">
    <template #menu>
      <v-list dense>
        <v-list-item-title class="text-h6 pl-2">Personal Notes</v-list-item-title>

        <notes-sortable-list 
          :value="noteGroups" 
          @input="updateNoteOrder"
          @update:note="updateNote"
          to-prefix="/notes/personal/"
        />
        
        <v-list-item>
          <v-list-item-action>
            <btn-confirm 
              :action="createNote"
              :confirm="false"
              button-text="Add"
              button-icon="mdi-plus"
              tooltip-text="Add Notebook Page"
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
  async asyncData({ store }) {
    return {
      notes: await store.dispatch('usernotes/getAll'),
    };
  },
  data() {
    return {
      refreshListingsInterval: null,
    }
  },
  head() {
    return {
      titleTemplate: title => this.$root.$options.head.titleTemplate((title ? `${title} | ` : '') + 'Notes'),
    }
  },
  computed: {
    noteGroups() {
      return this.$store.getters['usernotes/noteGroups'];
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
  methods: {
    async createNote() {
      const currentNote = this.$store.getters['usernotes/notes'].find(n => n.id === this.$route.params.noteId);
      const obj = await this.$store.dispatch('usernotes/create', {
        title: "New Note",
        // Insert new note after the currently selected note, or at the end of the list
        parent: currentNote?.parent || null,
        order: currentNote ? currentNote.order + 1 : null,
        checked: [true, false].includes(currentNote?.checked) ? false : null,
      });
      // Reload note list to get updated order
      this.$store.dispatch('usernotes/fetchAll');
      this.$router.push(`/notes/personal/${obj.id}/`);
    },
    async updateNote(note) {
      try {
        await this.$store.dispatch('usernotes/partialUpdate', { obj: note, fields: ['checked'] });
      } catch (error) {
        this.$toast.global.requestError({ error });
      }
    },
    async updateNoteOrder_(val) {
      try {
        await this.$store.dispatch('usernotes/sort', { noteGroups: val });
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
