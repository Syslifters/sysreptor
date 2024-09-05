<template>
  <div>
    <v-card-item class="comment-header">
      <div v-if="!props.initialEdit">
        <span v-if="modelValue.user" class="text-subtitle-2 text-medium-emphasis">
          @{{ modelValue.user.username }}
          <s-tooltip activator="parent" :text="modelValue.user.name" />
        </span>
        <chip-date :value="modelValue.created" size="small" />
      </div>

      <template #append v-if="!props.initialEdit">
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
                v-if="props.delete"
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
      <slot name="prepend-text" />

      <div v-if="editEnabled" @click.stop.prevent>
        <v-textarea
          ref="textFieldRef"
          v-model="editText"
          :placeholder="props.placeholder"
          density="compact"
          variant="outlined"
          rows="1"
          auto-grow
          hide-details="auto"
          spellcheck="false"
          class="comment-textfield"
        />
        <div class="mt-1">
          <s-btn-other 
            v-if="!props.initialEdit" 
            @click="editEnabled = false" 
            size="small" 
            text="Cancel" 
          />
          <s-btn-other 
            @click="performUpdate"
            :disabled="!editText.trim()"
            :loading="updateInProgress" 
            size="small" 
            text="Save" 
          />
        </div>
      </div>
      <span v-else class="comment-text">{{ modelValue.text }}</span>
    </v-card-text>
  </div>
</template>

<script setup lang="ts">
import type { Comment } from '#imports';

const auth = useAuth();

const modelValue = defineModel<Comment|CommentAnswer>({ required: true });
const props = defineProps<{
  delete?: () => Promise<void>;
  update: (value: any) => Promise<void>;
  readonly?: boolean;
  isNew?: boolean;
  initialEdit?: boolean;
  placeholder?: string;
}>();

const editEnabled = ref(props.initialEdit || false);
const editText = ref('');
const textFieldRef = ref<HTMLInputElement|null>(null);
whenever(() => props.isNew, () => {
  editEnabled.value = true;
}, { immediate: true });
whenever(editEnabled, () => {
  editText.value = modelValue.value.text;
}, { immediate: true });

const updateInProgress = ref(false);
async function performUpdate() {
  try {
    updateInProgress.value = true;
    const value = { ...modelValue.value, text: editText.value, editEnabled: false };
    await props.update(value);
    if (props.initialEdit) {
      editEnabled.value = true;
      editText.value = modelValue.value.text;
    } else {
      editEnabled.value = false;
    }
  } catch (error) {
    requestErrorToast({ error })
  } finally {
    updateInProgress.value = false;
  }
}

</script>

<style lang="scss" scoped>
@use "@/assets/vuetify.scss" as vuetify;

.comment-header {
  padding-top: 0.1em;
  padding-bottom: 0.1em;

  .v-card-subtitle {
    padding-bottom: 0;
  }
}
.comment-text {
  white-space: pre-wrap;
  word-break: break-word;
}
.comment-textfield {
  :deep(.v-field) {
    font-size: vuetify.$card-text-font-size;
  }
}
</style>
