<template>
  <v-card 
    :id="`comment-${comment.id}`"
    :ripple="false"
    density="compact"
    class="ma-1"
    :variant="props.isActive ? 'outlined' : undefined"
    :class="{
      'comment-selected': props.isActive,
      'comment-resolved': comment.status !== CommentStatus.OPEN,
    }"
  >
    <comment-content 
      :model-value="comment"
      :update="(c) => projectStore.updateComment(props.project, c)"
      :delete="() => projectStore.deleteComment(props.project, comment)"
      :readonly="readonly"
      placeholder="Comment text..."
      class="comment-content"
    >
      <template #menu>
        <btn-confirm
          v-if="comment.status === CommentStatus.OPEN"
          :action="() => projectStore.resolveComment(props.project, comment, { status: comment.status === CommentStatus.OPEN ? CommentStatus.RESOLVED : CommentStatus.OPEN })"
          :disabled="readonly"
          :confirm="false"
          button-variant="icon"
          button-icon="mdi-check"
          button-text="Resolve"
          tooltip-text="Resolve comment"
          :button-color="'success'"
          density="compact"
        />
      </template>
      <template #prepend-text>
        <blockquote 
          v-if="comment.text_original" 
          @click="textOriginalExpanded = !textOriginalExpanded"
          class="comment-textoriginal"
        >
          <span v-if="textOriginalExpanded" class="comment-textoriginal-expanded">{{ comment.text_original }}</span>
          <span v-else>{{ truncate(comment.text_original, { length: 50 }) }}</span>
        </blockquote>
      </template>
    </comment-content>
    <div v-for="answer in comment.answers" :key="answer.id" class="ml-4">
      <v-divider />
      <comment-answer 
        :answer="answer"
        :comment="props.comment"
        :project="props.project"
        :readonly="props.readonly"
        placeholder="Answer..."
        class="answer-content"
      />
    </div>
    <div v-if="props.isActive && comment.status === CommentStatus.OPEN && comment.text && !readonly" class="ml-4">
      <v-divider />
      <comment-answer
        :answer="{ text: '' } as unknown as CommentAnswer"
        :comment="props.comment"
        :project="props.project"
        :update="a => projectStore.createCommentAnswer(props.project, comment, a)"
        :initial-edit="true"
        class="answer-new"
      />
    </div>
  </v-card>
</template>

<script setup lang="ts">
import { truncate } from 'lodash-es';
import { type Comment } from '@/utils/types';

const props = defineProps<{
  project: PentestProject;
  comment: Comment;
  isActive?: boolean;
  readonly?: boolean;
}>();

const projectStore = useProjectStore();

const textOriginalExpanded = ref(false);

</script>

<style lang="scss" scoped>
@use "@/assets/vuetify.scss" as vuetify;

.comment-selected {
  :deep(.v-card__overlay) {
    background-color: currentColor;
    opacity: var(--v-activated-opacity);
  }
}

.comment-resolved {
  opacity: vuetify.$card-disabled-opacity;
}

.comment-textoriginal {
  background-color: rgba(var(--v-theme-on-surface), 0.05);
  border-left: 5px solid rgba(var(--v-theme-on-surface), 0.3);
  padding-left: 0.2em;
  margin-bottom: 0.4em;

  &-expanded {
    white-space: pre-wrap;
  }
}
</style>
