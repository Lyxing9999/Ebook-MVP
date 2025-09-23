<template>
  <div class="flex flex-col h-screen">
    <Topbar />
    <main class="flex-1 overflow-auto p-4 bg-gray-50 dark:bg-gray-800">
      <NuxtPage />
    </main>
  </div>
</template>

<script setup lang="ts">
import Topbar from "~/components/layout/Topbar.vue";
</script>
