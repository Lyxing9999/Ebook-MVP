import { defineNuxtConfig } from "nuxt/config";

export default defineNuxtConfig({
  ssr: true,
  modules: [
    "@nuxtjs/tailwindcss",
    "@element-plus/nuxt",
    "@pinia/nuxt",
    "@nuxtjs/i18n",
  ],
  css: ["element-plus/dist/index.css"],

  i18n: {
    langDir: "locales",
    locales: [
      { code: "en", iso: "en-US", name: "English", file: "en-US.json" },
      { code: "kh", iso: "km-KH", name: "ខ្មែរ", file: "km-KH.json" },
    ],
    defaultLocale: "en",
    strategy: "prefix_except_default",
    detectBrowserLanguage: {
      useCookie: true,
      cookieKey: "i18n_redirected",
      alwaysRedirect: true,
      redirectOn: "root",
    },
  },
});
