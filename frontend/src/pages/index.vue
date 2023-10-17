<script setup lang="ts">
definePageMeta({
  middleware: [
    function () {
      return navigateTo('/projects/', {
        replace: true,
      });
    }
  ]
});
</script>
