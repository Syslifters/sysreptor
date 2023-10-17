<template>
  <s-btn
    :disabled="disabled"
    icon
    variant="text"
    :ripple="false"
  >
    <s-emoji v-if="props.modelValue" :value="props.modelValue" />
    <v-icon v-else :icon="emptyIcon" />

    <v-menu
      activator="parent"
      v-model="dialogVisible"
      :disabled="disabled"
      :close-on-content-click="false"
    >
      <picker
        @select="selectEmoji"
        :data="emojiIndex"
        set="local"
        :show-skin-tones="false"
        :show-preview="false"
      >
        <template #searchTemplate="searchAttrs">
          <div class="d-flex flex-row">
            <search v-bind="searchAttrs" class="flex-grow-1" />
            <s-btn
              @click="clearEmoji"
              icon="$clear"
              variant="text"
              density="comfortable"
            />
          </div>
        </template>
      </picker>
    </v-menu>
  </s-btn>
</template>

<script setup lang="ts">
// @ts-ignore
import { Picker, EmojiIndex, Search } from "emoji-mart-vue-fast/src";
// @ts-ignore
import frequentlyUsedEmojis from 'emoji-mart-vue-fast/src/utils/frequently';
import emojiData from "emoji-mart-vue-fast/data/twitter.json";
import "emoji-mart-vue-fast/css/emoji-mart.css";

const props = withDefaults(defineProps<{
  modelValue: string|null;
  disabled?: boolean;
  emptyIcon?: string;
}>(), {
  modelValue: null,
  disabled: false,
  emptyIcon: 'mdi-emoticon-outline',
});
const emit = defineEmits<{
  'update:modelValue': [string|null];
}>();

const DEFAULT_EMOJIS = [
  'hankey',
  'clown_face',
  't-rex',
  'heavy_check_mark',
  'heavy_exclamation_mark',
  'question',
  'x',
  '+1',
  '-1',
  'fire',
  'bomb',
  '100',
  'boom',
  'joy',
  'cry',
  'grinning',
];
const recentEmojis = frequentlyUsedEmojis.get(10);
for (const d of DEFAULT_EMOJIS) {
  if (!recentEmojis.includes(d)) {
    recentEmojis.push(d);
  }
}
const emojiIndex = new EmojiIndex(emojiData, { recent: recentEmojis });
const dialogVisible = ref(false);

function selectEmoji(val: any) {
  dialogVisible.value = false;
  emit('update:modelValue', val.native);
}
function clearEmoji() {
  dialogVisible.value = false;
  emit('update:modelValue', null);
}

</script>

<style lang="scss" scoped>
:deep() {
  .emoji-type-image.emoji-set-local {
    background-image: url('@/assets/emojis/sheet_twitter_32_indexed_128.png');
  }

  .emoji-mart-emoji {
    span {
      cursor: pointer;
    }
  }
}
</style>
