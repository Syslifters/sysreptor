<template>
  <s-btn-icon 
    size="small"
    density="comfortable"
  >
    <v-icon icon="mdi-dots-vertical" />
    <v-tooltip activator="parent" location="top" text="More actions" />

    <v-menu activator="parent">
      <template #default>
        <v-list density="compact">
          <slot 
            name="default" 
          />
        </v-list>
      </template>
    </v-menu>
  </s-btn-icon>
</template>
