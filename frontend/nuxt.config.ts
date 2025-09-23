// https://nuxt.com/docs/api/configuration/nuxt-config

import { defineNuxtConfig } from "nuxt/config";

export default defineNuxtConfig({
  ssr: true,
  modules: ["@nuxtjs/tailwindcss", "@element-plus/nuxt"],
  build: {
    transpile: ["element-plus"],
  },
  css: ["element-plus/dist/index.css"],
});
