<template>
  <v-navigation-drawer
    v-if="modelValue"
    absolute
    permanent
    location="right"
    width="350"
    class="comment-sidebar"
  >
    <div class="sidebar-header">
      <v-list-item>
        <v-list-item-title class="text-h6">
          <pro-info>Comments</pro-info>
        </v-list-item-title>
        <template #append>
          <v-btn icon variant="text" @click="modelValue = false">
            <v-icon size="x-large" icon="mdi-close" />
          </v-btn>
        </template>
      </v-list-item>
      <v-divider />
    </div>

    <!-- TODO: community edition: comments disabled -->

    <div v-if="comments.length === 0">
      <v-list-item title="No comments yet" />
    </div>
    
    <v-list-item v-for="commentGroup, path in commentGroups" :key="path" class="pl-0 pr-0">
      <v-list-subheader :title="path as string" class="mt-0" />
      
      <v-card 
        v-for="comment in commentGroup" :key="comment.id"
        @click="emit('comment', {type: 'select', comment: comment})"
        :ripple="false"
        density="compact"
        class="ma-1"
        :class="{'comment-selected': props.commentProps.selected?.id === comment?.id}"
      >
        <comment-content 
          :model-value="comment"
          @update:model-value="updateComment"
          :delete="deleteComment"  
        >
          <template #menu>
            <btn-confirm
              :action="resolveComment"
              :confirm="false"
              button-variant="icon"
              button-icon="mdi-check"
              button-text="Resolve"
              tooltip-text="Resolve comment"
              :button-color=" 'success'"
            />
          </template>
        </comment-content>
        <div v-for="answer in comment.answers" :key="answer.id" class="ml-4">
          <v-divider />
          <comment-content 
            :model-value="answer"
            @update:model-value="updateAnswer"
            :delete="deleteAnswer"
          />
        </div>
      </v-card>
      <v-divider />
    </v-list-item>
  </v-navigation-drawer>
</template>

<script setup lang="ts">
import groupBy from 'lodash/groupBy';

const modelValue = defineModel<boolean>();
const props = defineProps<{
  commentProps: CommentPropType;
}>();
const emit = defineEmits<{
  'comment': [value: any];
}>();

const comments = computed(() => props.commentProps.comments);
const commentGroups = computed(() => groupBy(comments.value, 'dataPath'));
</script>

<style lang="scss" scoped>
@use "@/assets/vuetify.scss" as vuetify;

.sidebar-header {
  position: sticky;
  top: 0;
  z-index: 10;
  background-color: vuetify.$navigation-drawer-background;
}

.comment-selected {
  :deep(.v-card__overlay) {
    background-color: currentColor;
    opacity: var(--v-activated-opacity);
  }
}
</style>
