<template>
  <emoji 
    tag="i"
    :data="emojiIndex" 
    :emoji="emojiObject" 
    set="local"
    :size="size" 
    class="v-icon"
  />
</template>

<script>
import data from 'emoji-mart-vue-fast/data/twitter.json';
import { Emoji, EmojiIndex } from 'emoji-mart-vue-fast'

const emojiIndex = new EmojiIndex(data)

export default {
  components: { Emoji },
  props: {
    value: {
      type: String,
      required: true,
    },
    small: {
      type: Boolean,
      default: false,
    }
  },
  computed: {
    emojiIndex() {
      return emojiIndex;
    },
    emojiObject() {
      return this.emojiIndex.nativeEmoji(this.value);
    },
    size() {
      return this.small ? 20 : 24;
    }
  }
}
</script>

<style lang="scss" scoped>
.emoji-mart-emoji {
  padding: 0;
}

:deep() {
  .emoji-type-image.emoji-set-local {
    background-image: url('~assets/emojis/sheet_twitter_32_indexed_128.png');
  }
}
</style>
