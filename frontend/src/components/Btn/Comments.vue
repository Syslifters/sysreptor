<template>
  <s-btn-icon
    @click="emit('update:modelValue', !props.modelValue)"
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
import { type Comment } from '@/utils/types';

const props = defineProps<{
  modelValue: boolean;
  comments: Comment[];
}>();
const emit = defineEmits<{
  'update:modelValue': [value: boolean];
}>();

const numOpenComments = computed(() => props.comments.filter(c => c.status === CommentStatus.OPEN).length);
</script>
