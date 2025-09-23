<script setup lang="ts">
import { ref, nextTick, onBeforeUnmount } from "vue";
import { ElMessage } from "element-plus";
definePageMeta({
  layout: "main",
  middleware: [],
});
const username = ref("");
const password = ref("");
const content = ref("");

const logs = ref<{ text: string; type: string }[]>([]);
const loading = ref(false);
const currentStep = ref(0);
const showLogs = ref(false);

let eventSource: EventSource | null = null;

const steps = [
  { title: "Start" },
  { title: "Login" },
  { title: "Post" },
  { title: "Confirm" },
  { title: "Done" },
];

const handleSubmit = (e: Event) => {
  e.preventDefault();
  if (!username.value || !password.value || !content.value) {
    ElMessage.warning("Fill all fields");
    return;
  }

  // reset state
  logs.value = [];
  currentStep.value = 0;
  loading.value = true;
  showLogs.value = false;

  if (eventSource) eventSource.close();

  // Connect SSE
  eventSource = new EventSource(
    `http://localhost:5000/facebook/post?username=${encodeURIComponent(
      username.value
    )}&password=${encodeURIComponent(
      password.value
    )}&content=${encodeURIComponent(content.value)}`
  );

  eventSource.onmessage = async (event) => {
    const text = event.data;
    let type = "info";
    if (text.includes("[ERROR]")) type = "error";
    else if (text.includes("✅")) type = "success";
    else if (text.includes("⚠️")) type = "warning";

    logs.value.push({ text, type });

    // update steps
    if (text.includes("Logging in")) currentStep.value = 1;
    else if (text.includes("Typed post content")) currentStep.value = 2;
    else if (text.includes("Clicked POST button")) currentStep.value = 3;
    else if (text.includes("Post confirmed")) currentStep.value = 4;

    await nextTick();
    const container = document.getElementById("logs-container");
    if (container) container.scrollTop = container.scrollHeight;
  };

  eventSource.onerror = () => {
    logs.value.push({ text: "[DEBUG] Stream ended.", type: "info" });
    loading.value = false;
    if (eventSource) {
      eventSource.close();
      eventSource = null;
    }
  };
};

const revealLogs = () => (showLogs.value = true);

// cleanup when leaving page
onBeforeUnmount(() => {
  if (eventSource) eventSource.close();
});
</script>

<template>
  <el-card>
    <!-- Steps -->
    <el-steps :active="currentStep" finish-status="success">
      <el-step v-for="(s, i) in steps" :key="i" :title="s.title" />
    </el-steps>

    <!-- Form -->
    <form class="flex flex-col gap-3 mt-4" @submit="handleSubmit">
      <el-input v-model="username" placeholder="Username" :disabled="loading" />
      <el-input
        v-model="password"
        type="password"
        placeholder="Password"
        :disabled="loading"
      />
      <el-input
        v-model="content"
        type="textarea"
        placeholder="Content"
        :rows="5"
        :disabled="loading"
      />
      <div class="flex gap-3">
        <el-button type="primary" :loading="loading" native-type="submit">
          Post
        </el-button>
        <el-button
          type="success"
          @click="revealLogs"
          :disabled="showLogs || logs.length === 0"
        >
          Show Logs
        </el-button>
      </div>
    </form>

    <!-- Logs -->
    <div
      v-if="showLogs"
      id="logs-container"
      class="bg-[#1e1e1e] text-[#d4d4d4] font-mono text-sm max-h-72 overflow-y-auto p-3 rounded-xl mt-4"
    >
      <div
        v-for="(log, i) in logs"
        :key="i"
        :style="{
          color:
            log.type === 'error'
              ? '#f44336'
              : log.type === 'success'
              ? '#4caf50'
              : log.type === 'warning'
              ? '#ff9800'
              : '#c0c0c0',
        }"
      >
        {{ log.text }}
      </div>
    </div>
  </el-card>
</template>
