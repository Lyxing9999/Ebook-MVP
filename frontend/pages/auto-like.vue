<script setup>
import { ref, nextTick, onUnmounted } from "vue";
import { ElMessage, ElInput, ElButton, ElCard } from "element-plus";

definePageMeta({
  layout: "main",
  middleware: [],
});
const username = ref("");
const password = ref("");
const postUrl = ref("");
const logs = ref([]);
const loading = ref(false);
const showLogs = ref(false);

let eventSource = null;

const handleSubmit = (e) => {
  e.preventDefault();
  if (!username.value || !password.value || !postUrl.value) {
    ElMessage.warning("Please fill in all fields.");
    return;
  }

  // Reset logs
  logs.value = [];
  loading.value = true;
  showLogs.value = true;

  // Close any existing EventSource
  if (eventSource) eventSource.close();

  // Start new EventSource
  eventSource = new EventSource(
    `http://localhost:5000/facebook/auto_like?username=${encodeURIComponent(
      username.value
    )}&password=${encodeURIComponent(
      password.value
    )}&post_url=${encodeURIComponent(postUrl.value)}`
  );

  eventSource.onmessage = async (e) => {
    logs.value.push(e.data);
    await nextTick();
    const container = document.getElementById("logs-container");
    if (container) container.scrollTop = container.scrollHeight;

    // Stop loading when task finishes
    if (e.data === "[INFO] Task completed.") {
      loading.value = false;
      eventSource.close();
      eventSource = null;
    }
  };

  eventSource.onerror = () => {
    logs.value.push("[DEBUG] Stream ended unexpectedly.");
    loading.value = false;
    if (eventSource) {
      eventSource.close();
      eventSource = null;
    }
  };
};

// Cleanup on unmount
onUnmounted(() => {
  if (eventSource) eventSource.close();
});
</script>

<template>
  <el-card class="auto-like-card">
    <h2>Facebook Auto-Like Demo</h2>

    <form @submit="handleSubmit" class="form">
      <el-input v-model="username" placeholder="Facebook Username" />
      <el-input v-model="password" type="password" placeholder="Password" />
      <el-input v-model="postUrl" placeholder="Post URL" />
      <el-button type="primary" :loading="loading" native-type="submit">
        Start Auto Like
      </el-button>
    </form>

    <div v-if="showLogs" id="logs-container" class="logs-panel">
      <div v-for="(log, i) in logs" :key="i">{{ log }}</div>
    </div>
  </el-card>
</template>

<style scoped>
.auto-like-card {
  max-width: 600px;
  margin: 40px auto;
  padding: 20px;
  border-radius: 16px;
}
.form {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-bottom: 20px;
}
.logs-panel {
  margin-top: 20px;
  padding: 10px;
  background: #1e1e1e;
  color: #d4d4d4;
  font-family: monospace;
  font-size: 14px;
  max-height: 300px;
  overflow-y: auto;
  border-radius: 8px;
  scroll-behavior: smooth;
}
</style>
