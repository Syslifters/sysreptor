<template>
  <s-card
    v-if="askUser"
    prepend-icon="mdi-comment-question-outline"
    :title="askUser.question"
    density="compact"
    variant="tonal"
    class="interrupt-prompt-card"
  >
    <v-card-text class="pb-0">
      <v-list
        v-model:selected="selected"
        select-strategy="single-leaf"
        density="compact"
        :lines="false"
        class="pa-0"
      >
        <v-list-item
          v-for="(opt, index) in askUser.options"
          :key="index"
          :value="index"
          class="pa-0"
        >
          <template #prepend="{ isSelected }">
            <v-checkbox-btn
              :model-value="isSelected"
              true-icon="$radioOn"
              false-icon="$radioOff"
              density="compact"
            />
          </template>
          <template #title>
            <span class="text-body-medium text-wrap">{{ opt }}</span>
          </template>
        </v-list-item>

        <v-list-item
          :value="OTHER_VALUE"
          @click="focusOtherTextarea"
          class="pa-0 ask-user-other-item"
        >
          <template #prepend="{ isSelected }">
            <v-checkbox-btn
              :model-value="isSelected"
              true-icon="$radioOn"
              false-icon="$radioOff"
              density="compact"
            />
          </template>
          <v-textarea
            ref="otherTextareaRef"
            :model-value="otherText"
            @update:model-value="onOtherTextUpdate"
            @keydown.enter.prevent
            :readonly="selection !== OTHER_VALUE"
            placeholder="Other..."
            variant="plain"
            density="compact"
            hide-details
            spellcheck="false"
            rows="1"
            max-rows="8"
            auto-grow
            class="ask-user-other-textarea"
            @click.stop="selectOtherAndFocus"
            @focus="selectOtherAndFocus"
          />
        </v-list-item>
      </v-list>
    </v-card-text>
    <v-card-actions>
      <v-spacer />
      <s-btn-primary
        @click="submit"
        :disabled="!canSubmit"
        text="Submit answer"
        prepend-icon="mdi-send"
        size="small"
      />
    </v-card-actions>
  </s-card>
</template>

<script setup lang="ts">
import type { ChatInterrupt } from '@/utils/agent';

const OTHER_VALUE = '__other__';

const props = defineProps<{
  interrupt: ChatInterrupt;
}>();

const emit = defineEmits<{
  resume: [payload: Record<string, any>];
}>();

const selected = ref<(number | typeof OTHER_VALUE)[]>([]);
const selection = computed(() => selected.value[0] ?? null);
const otherText = ref('');
const otherTextareaRef = useTemplateRef('otherTextareaRef');

function onOtherTextUpdate(value: string) {
  otherText.value = value.replace(/[\r\n]+/g, '');
}

const askUser = computed(
  () => props.interrupt.value?.interrupt_type === 'ask_user' ? props.interrupt.value : null,
);

async function selectOtherAndFocus() {
  selected.value = [OTHER_VALUE];
  await focusOtherTextarea();
}

async function focusOtherTextarea() {
  await nextTick();
  const refValue = otherTextareaRef.value as any;
  if (typeof refValue?.focus === 'function') {
    refValue.focus();
    return;
  }
  const el: HTMLElement | undefined = refValue?.$el;
  const target = el?.querySelector('textarea') as HTMLTextAreaElement | null;
  target?.focus();
}

const canSubmit = computed(() => {
  if (!askUser.value || selection.value === null || selection.value === undefined) {
    return false;
  }
  if (selection.value === OTHER_VALUE) {
    return Boolean(otherText.value.trim());
  }
  return true;
});

function submit() {
  if (!askUser.value || !canSubmit.value) {
    return;
  }

  const answer = selection.value === OTHER_VALUE
    ? otherText.value.trim()
    : askUser.value.options[selection.value as number];

  emit('resume', {
    [props.interrupt.id]: answer,
  });
}
</script>

<style lang="scss" scoped>
.ask-user-other-textarea:deep() {
  .v-field__input {
    mask-image: none;
  }

  textarea {
    font-size: 0.875rem;
    line-height: 1.5;
    padding-top: 4px;
    padding-bottom: 4px;
  }
}

.interrupt-prompt-card:deep() {
  overflow: hidden;

  .v-card-title {
    font-size: 0.875rem;
    font-weight: bold;
    white-space: normal;
  }
}
</style>
