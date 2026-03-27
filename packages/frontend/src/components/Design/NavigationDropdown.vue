<template>
  <navigation-dropdown
    v-if="apiSettings.settings!.features.private_designs"
    :value="props.value"
    :items="[
      { 
        value: 'global', 
        title: 'Global', 
        icon: 'mdi-earth',
        to: { path: '/designs/', query: route.query },
      },
      { 
        value: 'private', 
        title: 'Private', 
        icon: 'mdi-account',
        disabled: !apiSettings.settings!.features.private_designs,
        to: { path: '/designs/private/', query: route.query },
      },
    ]"
  />
</template>

<script setup lang="ts">
const props = defineProps<{
  value: string;
}>();

const route = useRoute();
const apiSettings = useApiSettings();

</script>
