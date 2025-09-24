<script setup lang="ts">
import * as Icons from "@element-plus/icons-vue";
import { computed } from "vue";
import { useRoute } from "vue-router";
import { useI18n } from "vue-i18n";
interface MenuItem {
  titleKey: string;
  icon: keyof typeof Icons;
  route: string;
}

// The useI18n composable from @nuxtjs/i18n also provides the configured locales
const { t, locale, locales, setLocale } = useI18n();

const unifiedMenus: MenuItem[] = [
  { titleKey: "dashboard", icon: "HomeFilled", route: "/dashboard" },
  { titleKey: "accounts", icon: "User", route: "/accounts" },
  // { titleKey: "autoPost", icon: "Edit", route: "/auto-post" },
  { titleKey: "autoLike", icon: "StarFilled", route: "/auto-like" },
  { titleKey: "autoShare", icon: "Share", route: "/auto-shared" },
  { titleKey: "autoComment", icon: "ChatDotRound", route: "/auto-comment" },
  { titleKey: "Auto Follow", icon: "UserFilled", route: "/auto-follow" },
  { titleKey: "Auto Confirm", icon: "UserFilled", route: "/auto-confirm" },
  {
    titleKey: "Auto Add Friends",
    icon: "UserFilled",
    route: "/auto-add-friends",
  },
  { titleKey: "settings", icon: "Setting", route: "/settings" },
];
const menuItems = unifiedMenus.map((item) => ({
  ...item,
  iconComponent: Icons[item.icon] ?? Icons.HomeFilled,
}));
const route = useRoute();
const activeMenu = computed(() => route.path);

// Language switching
const currentLocaleLabel = computed(() => {
  // The 'locales' ref is an array of objects, but the structure might be different.
  // We ensure we are accessing the correct properties. The value from useI18n is a ReadonlyRef<LocaleObject[]>
  const found = locales.value.find((l) => l.code === locale.value);
  return found?.name ?? locale.value; // Use optional chaining for safety
});

const switchLocale = (code: "en" | "kh") => {
  setLocale(code);
};
</script>

<template>
  <el-header
    class="bg-white dark:bg-gray-900 shadow flex items-center justify-between px-6 h-16"
  >
    <div class="flex items-center gap-3">
      <span class="font-bold text-xl w-24">E Book</span>
      <el-menu
        mode="horizontal"
        router
        :default-active="activeMenu"
        class="bg-transparent"
      >
        <el-menu-item
          v-for="item in menuItems"
          :key="item.route"
          :index="item.route"
        >
          <el-icon>
            <component :is="item.iconComponent" />
          </el-icon>
          <span>{{ t(item.titleKey) }}</span>
        </el-menu-item>
      </el-menu>
    </div>

    <div class="flex items-center gap-4">
      <el-badge is-dot>
        <el-button icon="Bell" circle />
      </el-badge>

      <el-dropdown trigger="click">
        <span
          class="cursor-pointer flex items-center gap-1 px-2 py-1 border rounded"
        >
          {{ currentLocaleLabel }}
        </span>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item
              v-for="loc in locales"
              :key="loc.code"
              @click="switchLocale(loc.code)"
            >
              {{ loc.name }}
            </el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>

      <el-dropdown trigger="click">
        <span class="cursor-pointer flex items-center gap-2">
          <el-avatar icon="User" :size="32" />
          <span>Admin</span>
        </span>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item>{{ t("profile") }}</el-dropdown-item>
            <el-dropdown-item>{{ t("logout") }}</el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
    </div>
  </el-header>
</template>
