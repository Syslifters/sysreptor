<template>
  <v-menu 
    v-model="dialogVisible"
    :disabled="disabled" 
    :close-on-content-click="false"
    offset-y
  >
    <template #activator="{attrs: menuAttrs, on: menuOn}">
      <s-btn :disabled="disabled" v-bind="menuAttrs" v-on="menuOn" icon>
        <v-icon v-if="value" class="emoji-icon">{{ value }}</v-icon>
        <v-icon v-else>mdi-emoticon-outline</v-icon>
      </s-btn>
    </template>

    <template #default>
      <picker 
        @select="selectEmoji" 
        :data="emojiIndex" 
        :native="true" :set="null"
        :show-skin-tones="false"
        :show-preview="false"
      >
        <template #searchTemplate="searchAttrs">
          <div class="d-flex flex-row">
            <search v-bind="searchAttrs" @search="searchAttrs.onSearch" class="flex-grow-1" />
            <s-btn @click="clearEmoji" icon>
              <v-icon>mdi-close</v-icon>
            </s-btn>
          </div>
        </template>
      </picker>
    </template>
  </v-menu>
</template>

<script>
import { Picker, EmojiIndex, Search } from "emoji-mart-vue-fast";
import frequentlyUsedEmojis from 'emoji-mart-vue-fast/src/utils/frequently';
import emojiData from "emoji-mart-vue-fast/data/all.json";
import "emoji-mart-vue-fast/css/emoji-mart.css";

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

export default {
  components: { Picker, Search },
  props: {
    value: {
      type: String,
      default: null,
    },
    disabled: {
      type: Boolean,
      default: false,
    }
  },
  data() {
    const recent = frequentlyUsedEmojis.get(10);
    for (const d of DEFAULT_EMOJIS) {
      if (!recent.includes(d)) {
        recent.push(d);
      }
    }

    return {
      emojiIndex: new EmojiIndex(emojiData, { recent }),
      dialogVisible: false,
    };
  },
  methods: {
    selectEmoji(val) {
      this.dialogVisible = false;
      this.$emit('input', val.native);
    },
    clearEmoji() {
      this.dialogVisible = false;
      this.$emit('input', null);
    }
  }
}
</script>

<style lang="scss" scoped>
.emoji-icon {
  font-style: normal;
  color: black !important;
}

:deep() {
  .emoji-mart-emoji {
    span {
      cursor: pointer;
    }
  }
}
</style>
