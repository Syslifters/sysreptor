<template>
  <div></div>
</template>

<script>
export default {
  fetch() {
    this.$router.push({ path: `/projects/${this.$route.params.projectId}/reporting/` });
  }
}
</script>
