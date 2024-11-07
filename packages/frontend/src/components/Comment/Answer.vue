<template>
  <comment-content 
    :model-value="props.answer"
    :update="performUpdate"
    :delete="() => projectStore.deleteCommentAnswer(props.project, props.comment, props.answer)"
    :readonly="props.readonly"
    placeholder="Answer..."
    class="answer-content"
  />
</template>

<script setup lang="ts">
import type { Comment, CommentAnswer } from '#imports';

const props = defineProps<{
  answer: CommentAnswer;
  comment: Comment;
  project: PentestProject;
  readonly?: boolean
  update?: (value: CommentAnswer) => Promise<void>;
}>()

const projectStore = useProjectStore();

async function performUpdate(answer: CommentAnswer) {
  if (props.update) {
    return await props.update(answer);
  } else {
    return await projectStore.updateCommentAnswer(props.project, props.comment, answer);
  }
}

</script>
