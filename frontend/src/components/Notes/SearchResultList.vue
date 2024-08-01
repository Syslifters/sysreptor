<template>
  <div>
    <div v-for="item in props.resultGroup" :key="item.note.id">
      <v-list-item
        :to="noteUrl(item.note)"
        :ripple="false"
        class="note-list-item"
      >
        <template #prepend>
          <div class="note-list-children-icon">
            <v-icon v-if="item.children.length > 0" icon="mdi-menu-down" />
          </div>
          <div class="note-icon">
            <v-icon v-if="item.note.checked === true" size="small" class="text-disabled" icon="mdi-checkbox-marked" />
            <v-icon v-else-if="item.note.checked === false" size="small" class="text-disabled" icon="mdi-checkbox-blank-outline" />
            <s-emoji v-else-if="item.note.icon_emoji" :value="item.note.icon_emoji" size="small" class="emoji-icon" />
            <v-icon v-else-if="item.children.length > 0" size="small" class="text-disabled" icon="mdi-folder-outline" />
            <v-icon v-else size="small" class="text-disabled" icon="mdi-note-text-outline" />
          </div>
        </template>
        <template #default>
          <v-list-item-title class="text-body-2">{{ item.note.title }}</v-list-item-title>
        </template>
      </v-list-item>

      <v-list density="compact" class="match-list">
        <v-list-item
          v-for="match in item.matches" :key="match.field + match.from"
          :to="noteUrl(item.note, match)"
          @click="event => navigateToMatch(event, item.note, match)"
          :active="false"
        >
          <v-list-item-title>
            <span>{{ match.previewText.slice(0, match.previewFrom) }}</span>
            <span class="highlight-match">{{ match.previewText.slice(match.previewFrom, match.previewTo) }}</span>
            <span>{{ match.previewText.slice(match.previewTo) }}</span>
          </v-list-item-title>
        </v-list-item>
      </v-list>

      <v-list density="compact" class="pt-0 pb-0">
        <notes-search-result-list
          :result-group="item.children || []"
          :to-prefix="props.toPrefix"
          :level="(props.level || 0) + 1"
          class="child-list"
        />
      </v-list>
    </div>
  </div>
</template>

<script setup lang="ts">
const props = defineProps<{
  resultGroup: NoteSearchResults<NoteBase>;
  toPrefix: string;
  level?: number;
}>();

const route = useRoute();

function noteUrl(note: NoteBase, match?: SearchResultMatch) {
  return `${props.toPrefix}${note.id}/` + (match ? `#${match.field}:offset=${match.from}` : '');
}

function navigateToMatch(event: Event, note: NoteBase, match: SearchResultMatch) {
  const url = new URL(noteUrl(note, match), window.location.href);
  if (!url) {
    return;
  }
  if (route.path === url.pathname) {
    focusElement(url.hash, { scroll: { behavior: 'smooth', block: 'center' } });
    event.preventDefault();
  }
}

</script>

<style lang="scss" scoped>
.note-list-item {
  min-height: 1em;
  padding-left: 0 !important;

  .note-list-children-icon {
    width: 1.5rem;
    min-width: 1.5rem;
    height: 1.5rem;

    :deep(.v-icon) {
      width: 1.5rem;
    }
  }

  .note-icon {
    width: 1.5rem;
    height: 1.5rem;

    .emoji-icon {
      padding-top: 2px
    }
  }
}

.child-list {
  padding-left: 1rem;
}

:deep(.v-list-item-subtitle) {
  font-size: x-small !important;
}

.match-list {
  padding-left: 2rem;
  padding-top: 0;
  padding-bottom: 0;

  .v-list-item {
    padding-top: 0;
    padding-bottom: 0;
    min-height: 24px;

    .v-list-item-title {
      font-size: small;
    }
  }
}
.highlight-match {
  // TODO: define highlight color
  background-color: yellow;
  color: black;
}
</style>
