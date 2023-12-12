<template>
  <file-drop-area @drop="importBtnRef.performImport($event)" class="h-100">
    <full-height-page>
      <list-view ref="listViewRef" url="/api/v1/projecttypes/?scope=global&ordering=name">
        <template #title>Designs</template>
        <template #actions>
          <design-create-design-dialog />
          <design-import-design-dialog ref="importBtnRef" />
        </template>
        <template #searchbar="{ items }">
          <v-row dense class="mb-2 w-100">
            <v-col cols="12" md="10">
              <v-text-field
                :model-value="items.search.value"
                @update:model-value="listViewRef?.updateSearch"
                label="Search"
                spellcheck="false"
                hide-details="auto"
                variant="underlined"
                autofocus
                class="ma-0"
              />
            </v-col>
            <v-col cols="12" md="2">
              <s-select 
                v-model="designScopeFilter"
                :items="[{ title: 'All Designs', value: designFilterAllValue }, { title: 'Global Designs', value: ProjectTypeScope.GLOBAL}, { title: 'Private Designs', value: ProjectTypeScope.PRIVATE }]"
                label="Scope"
                variant="underlined"
                class="ma-0"
              />
            </v-col>
          </v-row>
        </template>
        <template #item="{item}">
          <v-list-item :to="`/designs/${item.id}/pdfdesigner/`" lines="two">
            <v-list-item-title>{{ item.name }}</v-list-item-title>
            <v-list-item-subtitle>
              <v-chip v-if="item.scope === ProjectTypeScope.GLOBAL" size="small" class="ma-1">
                <v-icon size="small" start icon="mdi-earth" />
                Global Design
              </v-chip>
              <v-chip v-else-if="item.scope === ProjectTypeScope.PRIVATE" size="small" class="ma-1">
                <v-icon size="small" start icon="mdi-account" />
                Private Design
              </v-chip>
              <chip-created :value="item.created" />
            </v-list-item-subtitle>
          </v-list-item>
        </template>
      </list-view>
    </full-height-page>
  </file-drop-area>
</template>

<script setup lang="ts">
definePageMeta({
  title: 'Designs',
  toplevel: true,
});
useHeadExtended({
  breadcrumbs: () => designListBreadcrumbs(),
});

const route = useRoute();
const router = useRouter();

const importBtnRef = ref();

const listViewRef = ref();
const designFilterAllValue = String([ProjectTypeScope.GLOBAL, ProjectTypeScope.PRIVATE]);
const designScopeFilter = computed({
  get: () => {
    const currentScope = String(route.query.scope || '');
    if (!currentScope) {
      return ProjectTypeScope.GLOBAL;
    } else {
      return currentScope;
    }
  }, 
  set: (val) => {
    router.replace({ query: { ...route.query, scope: val.split(',') } });
  }
});
</script>
