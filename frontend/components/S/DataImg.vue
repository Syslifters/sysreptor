<template>
  <v-img :src="srcUrl" v-bind="$attrs" v-on="$listeners" />
</template>

<script>
export default {
  props: {
    src: {
      type: String,
      required: true,
    },
  },
  data() {
    return {
      srcUrl: null,
    }
  },
  watch: {
    src: {
      immediate: true,
      async handler(val) {
        try {
          const imgRes = await this.$axios.$get(val, {
            responseType: 'arraybuffer',
          });
          this.srcUrl = 'data:image;base64,' + Buffer.from(imgRes).toString('base64');
        } catch (error) {
          this.srcUrl = null;
        }
      }
    }
  }
}
</script>
