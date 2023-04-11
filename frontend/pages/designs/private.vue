<template>
  <div>
    <s-sub-menu>
      <v-tab :to="`/designs/`" nuxt exact>Global Designs</v-tab>
      <v-tab :to="`/designs/private/`" nuxt>Private Designs</v-tab>
    </s-sub-menu>

    <list-view url="/projecttypes/?scope=private&ordering=name">
      <template #title>Private Designs</template>
      <template #actions>
        <create-design-dialog project-type-scope="private" />
      </template>
      <template #item="{item}">
        <v-list-item :to="`/designs/${item.id}/pdfdesigner/`" nuxt>
          <v-list-item-title>
            {{ item.name }}
          </v-list-item-title>
        </v-list-item>
      </template>
    </list-view>
  </div>
</template>

<script>
export default {
  head: {
    title: 'Private Designs',
  },
}
</script>
