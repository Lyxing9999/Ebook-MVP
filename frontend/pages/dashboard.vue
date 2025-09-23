<script setup lang="ts">
definePageMeta({
  layout: "main", // Uses your layouts/main.vue automatically
});

// Dashboard cards
interface Card {
  title: string;
  description: string;
  link: string;
}

const cards: Card[] = [
  {
    title: "Auto Post",
    description: "Schedule and post automatically",
    link: "/auto-post",
  },
  {
    title: "Auto Like",
    description: "Automatically like posts",
    link: "/auto-like",
  },
  {
    title: "Auto Comment",
    description: "Automatically comment on posts",
    link: "/auto-comment",
  },
  { title: "Accounts", description: "Manage all accounts", link: "/accounts" },
  {
    title: "Settings",
    description: "Configure system settings",
    link: "/settings",
  },
];
</script>

<template>
  <div class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
    <NuxtLink
      v-for="card in cards"
      :key="card.title"
      :to="card.link"
      class="p-6 rounded-lg shadow-lg bg-white dark:bg-gray-800 hover:shadow-xl transition transform hover:-translate-y-1 flex flex-col gap-2"
    >
      <h2 class="text-xl font-bold text-gray-900 dark:text-white">
        {{ card.title }}
      </h2>
      <p class="text-gray-600 dark:text-gray-300">{{ card.description }}</p>
      <div class="mt-auto">
        <button
          class="mt-2 px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 transition"
        >
          Go
        </button>
      </div>
    </NuxtLink>
  </div>
</template>

<style scoped>
/* Optional: smooth hover animation for all links */
.nuxt-link:hover {
  transform: translateY(-2px);
}
</style>
