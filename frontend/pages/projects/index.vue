<template>
  <list-view url="/pentestprojects/">
    <template #title>Projects</template>
    <template #actions>
      <s-btn to="/projects/new/" color="primary">
        <v-icon>mdi-plus</v-icon>
        Create new project
      </s-btn>
    </template>
    <template #item="{item}">
      <v-list-item :to="`/projects/${item.id}/reporting/`" nuxt two-line>
        <v-list-item-content>
          <v-list-item-title>
            {{ item.name }}
          </v-list-item-title>
            
          <v-list-item-subtitle>
            <v-chip v-for="pentester in item.pentesters" :key="pentester.id" class="ma-1 mt-2" small>
              {{ pentester.name }}
            </v-chip>
          </v-list-item-subtitle>
        </v-list-item-content>
      </v-list-item>
    </template>
  </list-view>
</template>
