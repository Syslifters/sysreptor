<template>
  <div>
    <div v-for="result in props.resultGroup" :key="result.item.id">
      <v-list-item
        :to="noteUrl(result.item)"
        :ripple="false"
        class="note-list-item"
      >
        <template #prepend>
          <div class="note-list-children-icon">
            <v-icon v-if="result.children.length > 0" icon="mdi-menu-down" />
          </div>
          <div class="note-icon">
            <v-icon v-if="result.item.checked === true" size="small" class="text-disabled" icon="mdi-checkbox-marked" />
            <v-icon v-else-if="result.item.checked === false" size="small" class="text-disabled" icon="mdi-checkbox-blank-outline" />
            <s-emoji v-else-if="result.item.icon_emoji" :value="result.item.icon_emoji" size="small" class="emoji-icon" />
            <v-icon v-else-if="result.children.length > 0" size="small" class="text-disabled" icon="mdi-folder-outline" />
            <v-icon v-else size="small" class="text-disabled" icon="mdi-note-text-outline" />
          </div>
        </template>
        <template #default>
          <v-list-item-title class="text-body-2">{{ result.item.title }}</v-list-item-title>
        </template>
      </v-list-item>

      <search-match-list
        :result="result"
        :to-prefix="noteUrl(result.item)"
        class="match-list"
      />

      <v-list density="compact" class="pt-0 pb-0">
        <notes-search-result-list
          :result-group="result.children || []"
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

function noteUrl(note: NoteBase,) {
  return `${props.toPrefix}${note.id}/`;
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

.match-list {
  padding-left: 2rem;
}
</style>
