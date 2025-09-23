<script setup lang="ts">
import { ref, reactive, nextTick, watch } from "vue";

import {
  ElMessage,
  ElDialog,
  ElInput,
  ElButton,
  ElCard,
  ElTable,
  ElTableColumn,
  ElCheckbox,
} from "element-plus";
import Chart from "chart.js/auto";
import { faker } from "@faker-js/faker";

// ----- State -----
const isLoggedIn = ref(false);
const username = ref("");
const password = ref("");

const activeMenu = ref("dashboard");

// Generate 50 fake accounts
const accounts = reactive(
  Array.from({ length: 50 }).map(() => ({
    id: faker.string.uuid(),
    username: faker.internet.username(),
    email: faker.internet.email(),
    password: faker.internet.password(),
    url: faker.internet.url(),
    status: "Idle",
    selected: false,
  }))
);

// Logs
const logs = reactive({
  posts: [] as string[],
  likes: [] as string[],
  comments: [] as string[],
});

// Dashboard stats
const dashboardStats = reactive({
  posts: 0,
  likes: 0,
  comments: 0,
});

// Charts
let postsChart: Chart | null = null;
let likesChart: Chart | null = null;
let commentsChart: Chart | null = null;

// Login
const login = () => {
  if (!username.value || !password.value) {
    ElMessage.error("Enter username and password");
    return;
  }
  isLoggedIn.value = true;
  ElMessage.success(`Logged in as ${username.value}`);
};

// Select all / deselect all accounts
const allSelected = ref(false);
const toggleSelectAll = () => {
  allSelected.value = !allSelected.value;
  accounts.forEach((a) => (a.selected = allSelected.value));
};

// Fake task runner
const runTask = (
  type: "posts" | "likes" | "comments",
  targetAccounts?: any[]
) => {
  const list = targetAccounts || accounts.filter((a) => a.selected);
  if (!list.length) {
    ElMessage.warning("No accounts selected!");
    return;
  }
  logs[type].push(`Starting ${type} tasks on ${list.length} accounts...`);
  list.forEach((acc) => (acc.status = `${type} running...`));

  setTimeout(() => {
    list.forEach((acc) => (acc.status = "Idle"));
    logs[type].push(`${type} tasks completed for ${list.length} accounts!`);
    // Update dashboard stats
    if (type === "posts") dashboardStats.posts += list.length;
    if (type === "likes") dashboardStats.likes += list.length;
    if (type === "comments") dashboardStats.comments += list.length;
    updateCharts();
  }, 2000);
};

// Watch analytics tab
watch(activeMenu, async (val) => {
  if (val === "analytics") {
    await nextTick();
    const postsCtx = document.getElementById("postsChart") as HTMLCanvasElement;
    const likesCtx = document.getElementById("likesChart") as HTMLCanvasElement;
    const commentsCtx = document.getElementById(
      "commentsChart"
    ) as HTMLCanvasElement;

    if (postsCtx && likesCtx && commentsCtx) {
      postsChart = new Chart(postsCtx, {
        type: "bar",
        data: {
          labels: ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
          datasets: [
            {
              label: "Posts",
              data: [3, 5, 2, 8, 4, 7, 6],
              backgroundColor: "rgba(54,162,235,0.5)",
            },
          ],
        },
      });

      likesChart = new Chart(likesCtx, {
        type: "line",
        data: {
          labels: ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
          datasets: [
            {
              label: "Likes",
              data: [5, 10, 7, 12, 6, 15, 10],
              borderColor: "rgba(75,192,192,1)",
              fill: false,
            },
          ],
        },
      });

      commentsChart = new Chart(commentsCtx, {
        type: "bar",
        data: {
          labels: ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
          datasets: [
            {
              label: "Comments",
              data: [2, 3, 1, 5, 3, 4, 2],
              backgroundColor: "rgba(255,99,132,0.5)",
            },
          ],
        },
      });
    }
  }
});

const updateCharts = () => {
  if (postsChart) postsChart.update();
  if (likesChart) likesChart.update();
  if (commentsChart) commentsChart.update();
};

// Add account modal
const showAddAccountModal = ref(false);
const newAccountName = ref("");
const addAccount = () => {
  if (!newAccountName.value) {
    ElMessage.error("Account name required");
    return;
  }
  accounts.push({
    id: faker.string.uuid(),
    username: newAccountName.value,
    email: faker.internet.email(),
    password: faker.internet.password(),
    url: faker.internet.url(),
    status: "Idle",
    selected: false,
  });
  ElMessage.success(`Account ${newAccountName.value} added`);
  newAccountName.value = "";
  showAddAccountModal.value = false;
};
</script>

<template>
  <div class="min-h-screen flex bg-gray-100">
    <!-- Sidebar -->
    <aside class="w-64 bg-gray-800 text-white flex flex-col">
      <div class="text-2xl font-bold text-center py-6 border-b border-gray-700">
        FPlus Demo
      </div>
      <nav class="flex-1 p-4 flex flex-col gap-2">
        <button
          @click="activeMenu = 'dashboard'"
          :class="
            activeMenu === 'dashboard' ? 'bg-gray-700' : 'hover:bg-gray-700'
          "
          class="w-full text-left px-3 py-2 rounded"
        >
          Dashboard
        </button>
        <button
          @click="activeMenu = 'accounts'"
          :class="
            activeMenu === 'accounts' ? 'bg-gray-700' : 'hover:bg-gray-700'
          "
          class="w-full text-left px-3 py-2 rounded"
        >
          Accounts
        </button>
        <button
          @click="activeMenu = 'logs'"
          :class="activeMenu === 'logs' ? 'bg-gray-700' : 'hover:bg-gray-700'"
          class="w-full text-left px-3 py-2 rounded"
        >
          Logs
        </button>
        <button
          @click="activeMenu = 'analytics'"
          :class="
            activeMenu === 'analytics' ? 'bg-gray-700' : 'hover:bg-gray-700'
          "
          class="w-full text-left px-3 py-2 rounded"
        >
          Analytics
        </button>
      </nav>
    </aside>

    <!-- Main -->
    <main class="flex-1 p-6 overflow-auto">
      <!-- Login -->
      <div v-if="!isLoggedIn" class="max-w-md mx-auto">
        <el-card class="p-6">
          <h2 class="text-xl font-bold mb-4">Login</h2>
          <el-input v-model="username" placeholder="Username" class="mb-2" />
          <el-input
            v-model="password"
            placeholder="Password"
            show-password
            class="mb-4"
          />
          <el-button type="primary" class="w-full" @click="login"
            >Login</el-button
          >
        </el-card>
      </div>

      <!-- Logged in -->
      <template v-else>
        <!-- Dashboard -->
        <div v-if="activeMenu === 'dashboard'" class="grid grid-cols-3 gap-4">
          <el-card class="p-4">
            <h3 class="text-lg font-semibold">Posts</h3>
            <div class="text-3xl font-bold">{{ dashboardStats.posts }}</div>
          </el-card>
          <el-card class="p-4">
            <h3 class="text-lg font-semibold">Likes</h3>
            <div class="text-3xl font-bold">{{ dashboardStats.likes }}</div>
          </el-card>
          <el-card class="p-4">
            <h3 class="text-lg font-semibold">Comments</h3>
            <div class="text-3xl font-bold">{{ dashboardStats.comments }}</div>
          </el-card>
        </div>

        <!-- Accounts -->
        <div v-if="activeMenu === 'accounts'" class="mt-4">
          <el-card class="p-4 mb-4">
            <div class="flex justify-between items-center mb-2">
              <h2 class="text-xl font-semibold">Accounts</h2>
              <div>
                <el-button
                  type="primary"
                  size="small"
                  @click="toggleSelectAll"
                  >{{ allSelected ? "Deselect All" : "Select All" }}</el-button
                >
                <el-button type="success" size="small" @click="runTask('posts')"
                  >Start Posts</el-button
                >
                <el-button type="success" size="small" @click="runTask('likes')"
                  >Start Likes</el-button
                >
                <el-button
                  type="success"
                  size="small"
                  @click="runTask('comments')"
                  >Start Comments</el-button
                >
                <el-button
                  type="primary"
                  size="small"
                  @click="showAddAccountModal = true"
                  >Add Account</el-button
                >
              </div>
            </div>
            <el-table :data="accounts" stripe style="width: 100%">
              <el-table-column label="">
                <template #default="{ row }">
                  <el-checkbox v-model="row.selected" />
                </template>
              </el-table-column>
              <el-table-column prop="username" label="Username" />
              <el-table-column prop="email" label="Email" />
              <el-table-column prop="password" label="Password" />
              <el-table-column prop="url" label="URL" />
              <el-table-column prop="status" label="Status" />
            </el-table>
          </el-card>
        </div>

        <!-- Logs -->
        <div v-if="activeMenu === 'logs'" class="mt-4 grid grid-cols-3 gap-4">
          <el-card class="p-2">
            <h3 class="text-lg font-semibold">Post Logs</h3>
            <div
              class="bg-black text-green-400 p-2 h-64 overflow-y-auto font-mono text-sm"
            >
              <div v-for="(log, i) in logs.posts" :key="i">{{ log }}</div>
            </div>
          </el-card>
          <el-card class="p-2">
            <h3 class="text-lg font-semibold">Like Logs</h3>
            <div
              class="bg-black text-green-400 p-2 h-64 overflow-y-auto font-mono text-sm"
            >
              <div v-for="(log, i) in logs.likes" :key="i">{{ log }}</div>
            </div>
          </el-card>
          <el-card class="p-2">
            <h3 class="text-lg font-semibold">Comment Logs</h3>
            <div
              class="bg-black text-green-400 p-2 h-64 overflow-y-auto font-mono text-sm"
            >
              <div v-for="(log, i) in logs.comments" :key="i">{{ log }}</div>
            </div>
          </el-card>
        </div>

        <!-- Analytics -->
        <div
          v-if="activeMenu === 'analytics'"
          class="mt-4 grid grid-cols-3 gap-4"
        >
          <el-card class="p-4">
            <h3 class="text-lg font-semibold mb-2">Posts Chart</h3>
            <canvas id="postsChart"></canvas>
          </el-card>
          <el-card class="p-4">
            <h3 class="text-lg font-semibold mb-2">Likes Chart</h3>
            <canvas id="likesChart"></canvas>
          </el-card>
          <el-card class="p-4">
            <h3 class="text-lg font-semibold mb-2">Comments Chart</h3>
            <canvas id="commentsChart"></canvas>
          </el-card>
        </div>

        <!-- Add Account Modal -->
        <el-dialog v-model="showAddAccountModal" title="Add New Account">
          <el-input v-model="newAccountName" placeholder="Username" />
          <span slot="footer" class="dialog-footer">
            <el-button @click="showAddAccountModal = false">Cancel</el-button>
            <el-button type="primary" @click="addAccount">Add</el-button>
          </span>
        </el-dialog>
      </template>
    </main>
  </div>
</template>

<style scoped>
.el-card {
  border-radius: 12px;
  box-shadow: 0 6px 12px rgba(0, 0, 0, 0.1);
}
</style>
