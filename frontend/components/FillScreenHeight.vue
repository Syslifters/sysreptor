<template>
  <div ref="container" class="screen-height-container" v-intersect="updateHeight" :style="{height: height + 'px'}">
    <slot />
  </div>
</template>

<script>
export default {
  emits: ['resize'],
  data() {
    return {
      height: 0,
    }
  },
  mounted() {
    this.updateHeight();
    window.addEventListener('resize', this.updateHeight);
  },
  beforeDestroy() {
    window.removeEventListener('resize', this.updateHeight);
  },
  methods: {
    updateHeight() {
      const clientRects = this.$refs.container?.getClientRects();
      if (!clientRects || clientRects.length === 0) {
        return;
      }
      const startY = clientRects[0].top;
      this.height = window.innerHeight - startY;
      this.$emit('resize');
    },
  }
}
</script>

<style lang="scss" scoped>
.screen-height-container {
  width: 100%;
  display: block;
  position: relative;
  overflow-y: auto;
}
</style>
