<template>
  <emoji
    :data="emojiIndex"
    :emoji="emojiObject"
    set="local"
    :size="emojiSize"
  />
</template>

<script setup lang="ts">
import data from 'emoji-mart-vue-fast/data/twitter.json';
import 'emoji-mart-vue-fast/css/emoji-mart.css';
// @ts-expect-error missing types
import { Emoji, EmojiIndex } from "emoji-mart-vue-fast/src";

const emojiIndex = new EmojiIndex(data);

const props = withDefaults(defineProps<{
  value: string;
  size?: 'default'|'small';
  small?: boolean;
}>(), {
  size: 'default',
});
const emojiSize = computed(() => props.size === 'small' ? 20 : 24);
const emojiObject = computed(() => emojiIndex.nativeEmoji(props.value));
</script>

<style lang="scss" scoped>
.emoji-mart-emoji {
  padding: 0;
}

:deep() {
  .emoji-type-image.emoji-set-local {
    background-image: url('@base/assets/emojis/sheet_twitter_32_indexed_128.png');
  }
}
</style>
