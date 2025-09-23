<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, nextTick } from "vue";
import { ElInput, ElButton, ElCard } from "element-plus";
definePageMeta({
  layout: "main",
  middleware: [],
});

const username = ref("");
const password = ref("");
const postUrl = ref("");
const comment = ref("");
const logs = ref<string[]>([]);
const loading = ref(false);

let eventSource: EventSource | null = null;

const startAutoComment = () => {
  if (!username.value || !password.value || !postUrl.value || !comment.value) {
    alert("Please fill all fields!");
    return;
  }

  logs.value = [];
  loading.value = true;

  // Close existing connection if any
  if (eventSource) {
    eventSource.close();
  }

  const params = new URLSearchParams({
    username: username.value,
    password: password.value,
    post_url: postUrl.value,
    comment: comment.value,
  });
  eventSource = new EventSource(
    `http://localhost:5000/facebook/auto_comment?${params.toString()}`
  );

  eventSource.onmessage = (event) => {
    logs.value.push(event.data);
    // Scroll to bottom
    nextTick(() => {
      const container = document.getElementById("log-container");
      if (container) container.scrollTop = container.scrollHeight;
    });
  };

  eventSource.onerror = () => {
    loading.value = false;
    eventSource?.close();
    eventSource = null;
  };
};

const stopAutoComment = () => {
  eventSource?.close();
  loading.value = false;
  eventSource = null;
};

onBeforeUnmount(() => {
  stopAutoComment();
});
</script>

<template>
  <ElCard class="p-4">
    <div class="grid gap-3">
      <ElInput v-model="username" placeholder="Username" />
      <ElInput v-model="password" type="password" placeholder="Password" />
      <ElInput v-model="postUrl" placeholder="Post URL" />
      <ElInput v-model="comment" placeholder="Comment" />

      <div class="flex gap-2">
        <ElButton type="primary" :loading="loading" @click="startAutoComment"
          >Start</ElButton
        >
        <ElButton @click="stopAutoComment">Stop</ElButton>
      </div>

      <div
        id="log-container"
        class="h-64 overflow-auto border p-2 mt-2 bg-gray-50"
      >
        <div v-for="(log, index) in logs" :key="index">{{ log }}</div>
      </div>
    </div>
  </ElCard>
</template>

<style scoped>
#log-container {
  font-family: monospace;
  white-space: pre-wrap;
}
</style>
