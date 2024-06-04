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
            <btn-confirm
              :disabled="modelValue.user?.id !== auth.user.value!.id"
              :action="editAnswer"
              :confirm="false"
              button-variant="list-item"
              button-icon="mdi-pencil"
              button-text="Edit"
            />
            <btn-delete
              :delete="props.delete"
              :disabled="modelValue.user?.id !== auth.user.value!.id"
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
        v-model="editText"
        density="compact"
      />
      <div class="mt-1">
        <s-btn-other @click="editEnabled = false" size="small" text="Cancel" />
        <s-btn-other @click="performUpdate" size="small" text="Save" />
      </div>
    </div>
    <span v-else>{{ modelValue.text }}</span>
  </v-card-text>
</template>

<script setup lang="ts">
import { parseISO, formatISO9075 } from 'date-fns';
import { type Comment } from '@/utils/types';

const auth = useAuth();

const modelValue = defineModel<Comment|CommentAnswer>({ required: true });
const props = defineProps<{
  delete: () => Promise<void>;
}>();

const formattedDate = computed(() => formatISO9075(parseISO(modelValue.value.created)));

const editEnabled = ref(false);
const editText = ref('');
function editAnswer() {
  editEnabled.value = true;
  editText.value = modelValue.value.text;
}

function performUpdate() {
  modelValue.value = { ...modelValue.value, text: editText.value };
  editEnabled.value = false;
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
