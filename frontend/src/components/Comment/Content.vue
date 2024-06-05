<template>
  <v-card-item class="comment-header">
    <div>
      <span v-if="modelValue.user" class="text-subtitle-2 text-medium-emphasis">
        @{{ modelValue.user.username }}
        <s-tooltip activator="parent" :text="modelValue.user.name" />
      </span>
      <chip-date :value="modelValue.created" size="small" />
    </div>

    <template #append>
      <slot name="menu" />

      <s-btn-icon density="compact">
        <v-icon icon="mdi-dots-vertical" />

        <v-menu 
          activator="parent" 
          location="bottom left" 
          :close-on-content-click="true"
          class="context-menu"
        >
          <v-list density="compact">
            <v-list-item 
              @click="editEnabled = true"
              :disabled="props.readonly || modelValue.user?.id !== auth.user.value!.id"
              prepend-icon="mdi-pencil"
              title="Edit"
            />
            <btn-delete
              :delete="props.delete"
              :disabled="props.readonly || modelValue.user?.id !== auth.user.value!.id"
              button-variant="list-item"
            />
          </v-list>
        </v-menu>
      </s-btn-icon>
    </template>
  </v-card-item>

  <v-card-text>
    <div v-if="editEnabled" @click.stop.prevent>
      <s-text-field
        ref="textFieldRef"
        v-model="editText"
        density="compact"
      />
      <div class="mt-1">
        <s-btn-other @click="editEnabled = false" size="small" text="Cancel" />
        <s-btn-other @click="performUpdate" :loading="updateInProgress" size="small" text="Save" />
      </div>
    </div>
    <span v-else>{{ modelValue.text }}</span>
  </v-card-text>
</template>

<script setup lang="ts">
import { type Comment } from '@/utils/types';

const auth = useAuth();

const modelValue = defineModel<Comment|CommentAnswer>({ required: true });
const props = defineProps<{
  readonly?: boolean;
  delete: () => Promise<void>;
  update: (value: any) => Promise<void>;
}>();

const editEnabled = ref(false);
const editText = ref('');
const textFieldRef = ref<HTMLInputElement|null>(null);
watch(modelValue, () => {
  const comment = modelValue.value as Comment;
  if (comment.editEnabled) {
    editEnabled.value = true;
    comment.editEnabled = false;
  }
}, { immediate: true });
watch(editEnabled, async (value) => {
  if (value) {
    editText.value = modelValue.value.text;
    await nextTick();
    textFieldRef.value?.focus();
  }
}, { immediate: true });

const updateInProgress = ref(false);
async function performUpdate() {
  try {
    updateInProgress.value = true;
    const value = { ...modelValue.value, text: editText.value, editEnabled: false };
    await props.update(value)
    editEnabled.value = false;
  } catch (error) {
    requestErrorToast({ error })
  } finally {
    updateInProgress.value = false;
  }
}

</script>

<style lang="scss" scoped>
.comment-header {
  padding-top: 0.1em;
  padding-bottom: 0.1em;

  .v-card-subtitle {
    padding-bottom: 0;
  }
}
</style>
