<template>
  <div></div>
</template>

<script setup lang="ts">
useAsyncDataE(async () => {
  throw createError({
    status: 404,
    statusText: 'Not Found',
  });
})
</script>
