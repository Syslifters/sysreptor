<template>
  <list-view url="/findingtemplates/">
    <template #title>Finding Templates</template>
    <template #searchbar="{items}">
      <v-row dense>
        <v-col cols="12" md="10">
          <v-text-field :value="items.searchQuery" @input="updateSearchQuery(items, $event)" label="Search" spellcheck="false" autofocus class="mt-4" />
        </v-col>
        <v-col cols="12" md="2">
          <language-selection v-model="currentLanguage" :items="languageChoices" :outlined="false" />
        </v-col>
      </v-row>
    </template>
    <template #actions v-if="$auth.hasScope('template_editor')">
      <s-btn to="/templates/new/" nuxt color="primary">
        <v-icon>mdi-plus</v-icon>
        Create
      </s-btn>
      <btn-import :import="performImport" />
    </template>
    <template #item="{item}">
      <template-list-item :value="item" :language="currentLanguage" :to="{path: `/templates/${item.id}/`, query: {language: currentLanguage}}" nuxt two-line />
    </template>
  </list-view>
</template>

<script>
import TemplateListItem from '~/components/Template/ListItem.vue';
import { uploadFileHelper } from '~/utils/upload';

export default {
  components: { TemplateListItem },
  head: {
    title: 'Templates',
  },
  computed: {
    languageChoices() {
      return [{ code: null, name: 'All' }].concat(this.$store.getters['apisettings/settings'].languages.filter(l => l.enabled || l.code === this.$route.query.language));
    },
    currentLanguage: {
      get() {
        return this.$route.query.language || null;
      },
      set(val) {
        this.$router.replace({ query: { ...this.$route.query, language: val || '' } });
      }
    },
  },
  methods: {
    async performImport(file) {
      const templates = await uploadFileHelper(this.$axios, '/findingtemplates/import/', file);
      this.$router.push({ path: `/templates/${templates[0].id}/` });
    },
    updateSearchQuery(items, search) {
      items.search(search);
      this.$router.replace({ query: { ...this.$route.query, search: search || '' } });
    },
  }
}
</script>
