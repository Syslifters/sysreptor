<template>
  <div>
    <s-sub-menu>
      <v-tab to="/projects/" nuxt exact>Active Projects</v-tab>
      <v-tab to="/projects/finished/" nuxt>Finished Projects</v-tab>
      <v-tab to="/projects/archived/" nuxt>Archived Projects</v-tab>
    </s-sub-menu>

    <list-view url="/archivedprojects/">
      <template #title>Archived Projects</template>
      <template #item="{item}">
        <v-list-item :to="`/projects/archived/${item.id}/`" nuxt two-line>
          <v-list-item-content>
            <v-list-item-title>
              {{ item.name }}
            </v-list-item-title>

            <v-list-item-subtitle>
              <chip-created :value="item.created" />
              <chip-auto-delete :value="item.auto_delete_date" />

              <s-tooltip>
                <template #activator="{ on }">
                  <v-chip small class="ma-1" v-on="on">
                    <v-icon v-if="item.key_parts.some(p => !p.user.is_active) && item.key_parts.filter(p => p.user.is_active).length < item.threshold * 2" small left color="warning">mdi-alert</v-icon>
                    {{ item.threshold }} / {{ item.key_parts.length }}
                  </v-chip>
                </template>
                <span>{{ item.threshold }} of {{ item.key_parts.length }} users are required to restore this project</span>
              </s-tooltip>

              <s-tooltip v-for="keypart in item.key_parts" :key="keypart.id">
                <template #activator="{on}">
                  <v-chip class="ma-1" small v-on="on">
                    <v-icon v-if="keypart.is_decrypted" small left color="green">mdi-lock-open-variant</v-icon>
                    <v-icon v-else small left color="red">mdi-lock</v-icon>
                    {{ keypart.user.username }}
                  </v-chip>
                </template>

                <template #default>
                  <span v-if="keypart.is_decrypted">{{ keypart.user.username }} already restored their part</span>
                  <span v-else>{{ keypart.user.username }}'s part is still encrypted</span>
                </template>
              </s-tooltip>

              <chip-tag v-for="tag in item.tags" :key="tag" :value="tag" class="mt-2" />
            </v-list-item-subtitle>
          </v-list-item-content>
        </v-list-item>
      </template>
    </list-view>
  </div>
</template>

<script>
export default {
  head: {
    title: 'Projects',
  },
}
</script>
