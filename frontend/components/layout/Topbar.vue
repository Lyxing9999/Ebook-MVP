<template>
  <el-header
    height="64px"
    class="bg-white dark:bg-gray-900 shadow flex items-center justify-between px-6"
  >
    <!-- Left: Logo + Menu -->
    <div class="flex items-center gap-8">
      <span class="font-bold text-xl">TOOL DUC</span>
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
          <span>{{ item.title }}</span>
        </el-menu-item>
      </el-menu>
    </div>

    <!-- Right: Notifications + User -->
    <div class="flex items-center gap-4">
      <el-badge is-dot>
        <el-button icon="Bell" circle />
      </el-badge>
      <el-dropdown trigger="click">
        <span class="cursor-pointer flex items-center gap-2">
          <el-avatar icon="User" :size="32" />
          <span>Admin</span>
        </span>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item>Profile</el-dropdown-item>
            <el-dropdown-item>Logout</el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
    </div>
  </el-header>
</template>

<script setup lang="ts">
import * as Icons from "@element-plus/icons-vue";
import { ref, computed } from "vue";
import { useRoute } from "vue-router";

interface MenuItem {
  title: string;
  icon: keyof typeof Icons;
  route: string;
}

const unifiedMenus: MenuItem[] = [
  { title: "Dashboard", icon: "HomeFilled", route: "/dashboard" },
  { title: "Accounts", icon: "User", route: "/accounts" },
  { title: "Auto Post", icon: "Edit", route: "/auto-post" },
  { title: "Auto Like", icon: "StarFilled", route: "/auto-like" },
  { title: "Auto Share", icon: "Share", route: "/auto-shared" },
  { title: "Auto Comment", icon: "ChatDotRound", route: "/auto-comment" },
  { title: "Settings", icon: "Setting", route: "/settings" },
];

const menuItems = unifiedMenus.map((item) => ({
  ...item,
  iconComponent: Icons[item.icon] ?? Icons.HomeFilled,
}));

const route = useRoute();
const activeMenu = computed(() => route.path);
</script>

<style scoped>
.el-menu-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-weight: 500;
}
.el-menu-item:hover {
  background-color: rgba(126, 87, 194, 0.1);
  border-radius: 6px;
}
</style>
