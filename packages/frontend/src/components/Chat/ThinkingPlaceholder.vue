<template>
  <span
    class="chat-thinking-placeholder text-body-medium text-disabled"
    role="status"
  >
    <slot name="default">Thinking...</slot>
  </span>
</template>

<style lang="scss" scoped>
.chat-thinking-placeholder {
  mask-image: linear-gradient(
    90deg,
    rgba(0, 0, 0, 0.5) 0%,
    rgba(0, 0, 0, 0.5) 40%,
    rgba(0, 0, 0, 1) 50%,
    rgba(0, 0, 0, 0.5) 60%,
    rgba(0, 0, 0, 0.5) 100%
  );
  mask-size: 300% 100%;
  mask-repeat: no-repeat;
  animation: chat-text-shimmer 1.2s linear infinite;
}

@keyframes chat-text-shimmer {
  0% {
    mask-position: 100% 0;
  }
  100% {
    mask-position: 0% 0;
  }
}
</style>
