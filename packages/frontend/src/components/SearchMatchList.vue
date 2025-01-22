<template>
  <v-list density="compact" class="match-list">
    <v-list-item
      v-for="match in result.matches" :key="match.field + match.from"
      :to="matchUrl(match)"
      @click="event => navigateToMatch(event, match)"
      :active="false"
    >
      <v-list-item-title>
        <span>{{ match.previewText.slice(0, match.previewFrom) }}</span>
        <span class="bg-search-match">{{ match.previewText.slice(match.previewFrom, match.previewTo) }}</span>
        <span>{{ match.previewText.slice(match.previewTo) }}</span>
      </v-list-item-title>
    </v-list-item>
  </v-list>
</template>

<script setup lang="ts">
const props = defineProps<{
  result: SearchResult<any>;
  toPrefix: string;
}>();

const route = useRoute();

function matchUrl(match: SearchResultMatch) {
  return `${props.toPrefix}#${match.field}:offset=${match.from}`;
}

function navigateToMatch(event: Event, match: SearchResultMatch) {
  const url = new URL(matchUrl(match), window.location.href);
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
.match-list {
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
</style>
