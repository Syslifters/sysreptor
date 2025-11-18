<template>
  <s-btn-icon
    @click="modelValue = !modelValue"
  >
    <v-badge 
      v-if="numOpenComments > 0"
      :content="numOpenComments" 
      floating 
      :max="9"
      :offset-x="6"
      :offset-y="6"
    >
      <v-icon icon="mdi-comment-text-outline" />
    </v-badge>
    <v-icon v-else icon="mdi-comment-text-outline" />

    <s-tooltip activator="parent" location="bottom" text="Comments" />
  </s-btn-icon>
</template>

<script setup lang="ts">
import type { Comment } from '#imports';

const modelValue = defineModel<boolean>();
const props = defineProps<{
  comments: Comment[];
}>();
const numOpenComments = computed(() => props.comments.filter(c => c.status === CommentStatus.OPEN).length);
</script>
