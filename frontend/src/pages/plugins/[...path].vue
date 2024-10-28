<template>
  <div></div>
</template>

<script setup lang="ts">
useAsyncDataE(async () => {
  throw createError({
    statusCode: 404,
    statusMessage: 'Not Found',
  });
})
</script>
