<template>
  <div class="h-100 d-flex flex-column">
    <div class="flex-grow-0">
      <slot name="header" />
    </div>

    <div class="flex-grow-height overflow-y-auto">
      <slot name="default" />
    </div>
  </div>
</template>
