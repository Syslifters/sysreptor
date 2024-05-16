<template>
  <s-btn-icon v-if="(props.orderingOptions?.length || 0) > 0">
    <v-icon icon="mdi-sort" />

    <v-menu activator="parent" location="bottom">
      <v-list 
        :selected="[modelValue]"
        @update:selected="modelValue = $event[0] || null"
      >
        <v-list-item
          v-for="option in props.orderingOptions" :key="option.id"
          prepend-icon="mdi-sort"
          :title="option.title"
          :value="option"
        />
      </v-list>
    </v-menu>
  </s-btn-icon>
</template>

<script setup lang="ts">
const modelValue = defineModel<OrderingOption|null>();
const props = defineProps<{
  orderingOptions?: OrderingOption[];
}>();
</script>
