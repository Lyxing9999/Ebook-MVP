<script setup lang="ts">
definePageMeta({ layout: "main" });

import { computed } from "vue";
import { useI18n } from "vue-i18n";

const { t, locale } = useI18n(); // i18n composable

// Card interface
interface Card {
  titleKey: string;
  descriptionKey: string;
  link: string;
}

// Base cards with i18n keys
const cards: Card[] = [
  {
    titleKey: "accounts",
    descriptionKey: "cards.accountsDesc",
    link: "/accounts",
  },
  {
    titleKey: "autoPost",
    descriptionKey: "cards.autoPostDesc",
    link: "/auto-post",
  },
  {
    titleKey: "autoLike",
    descriptionKey: "cards.autoLikeDesc",
    link: "/auto-like",
  },
  {
    titleKey: "autoComment",
    descriptionKey: "cards.autoCommentDesc",
    link: "/auto-comment",
  },
  {
    titleKey: "autoShare",
    descriptionKey: "cards.autoShareDesc",
    link: "/auto-share",
  },
  {
    titleKey: "settings",
    descriptionKey: "cards.settingsDesc",
    link: "/settings",
  },
];

// Computed today string
const today = computed(() => {
  const now = new Date();

  const weekday = now
    .toLocaleDateString("en", { weekday: "long" })
    .toLowerCase();
  const month = now.toLocaleDateString("en", { month: "long" }).toLowerCase();
  const day = now.getDate().toString();
  const year = now.getFullYear().toString();

  return `${t(weekday)}, ${t(month)} ${t(day)}, ${t(year)}`;
});
// Translated cards (reactive)
const translatedCards = computed(() =>
  cards.map((card) => ({
    ...card,
    title: t(card.titleKey),
    description: t(card.descriptionKey),
  }))
);

// Function to switch locale
const switchLocale = (code: "en" | "kh") => {
  locale.value = code;
};
</script>

<template>
  <div class="min-h-screen p-6 bg-gray-50 dark:bg-gray-900">
    <div class="max-w-6xl mx-auto space-y-6">
      <!-- Header -->
      <div class="flex justify-between items-center">
        <h1 class="text-3xl font-bold text-gray-900 dark:text-white">
          {{ today }}
        </h1>
        <span
          class="text-sm text-gray-500 dark:text-gray-400 bg-gray-200 dark:bg-gray-700 px-3 py-1 rounded-full"
        >
          {{ translatedCards.length }} tools
        </span>
      </div>

      <!-- Cards grid -->
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
        <NuxtLink
          v-for="card in translatedCards"
          :key="card.titleKey"
          :to="card.link"
          class="group block"
        >
          <div
            class="relative p-6 rounded-xl bg-white dark:bg-gray-800 shadow-sm border border-gray-200 dark:border-gray-700 hover:shadow-lg hover:border-blue-300 dark:hover:border-blue-600 transition-all duration-200 group-hover:-translate-y-1"
          >
            <h2
              class="text-xl font-semibold text-gray-900 dark:text-white group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors"
            >
              {{ t(card.titleKey) }}
            </h2>
            <p class="text-gray-600 dark:text-gray-300 mb-6 leading-relaxed">
              {{ t(card.descriptionKey) }}
            </p>
            <div class="flex items-center justify-between">
              <span
                class="text-sm font-medium text-blue-600 dark:text-blue-400 group-hover:text-blue-700 dark:group-hover:text-blue-300 transition-colors"
              >
                {{ t("openTool") }}
              </span>
            </div>
          </div>
        </NuxtLink>
      </div>

      <!-- Language switcher -->
      <div class="mt-6">
        <button
          class="px-4 py-2 rounded border bg-gray-100 dark:bg-gray-700"
          @click="switchLocale('en')"
        >
          English
        </button>
        <button
          class="px-4 py-2 rounded border bg-gray-100 dark:bg-gray-700 ml-2"
          @click="switchLocale('kh')"
        >
          ខ្មែរ
        </button>
      </div>
    </div>
  </div>
</template>
