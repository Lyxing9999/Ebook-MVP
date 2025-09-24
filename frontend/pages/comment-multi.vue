<script setup lang="ts">
import { ref, nextTick, onBeforeUnmount } from "vue";
import { ElInput, ElButton, ElCard, ElForm, ElFormItem } from "element-plus";

definePageMeta({
  layout: "main",
});

interface Account {
  username: string;
  password: string;
}

// Form state
const accounts = ref<Account[]>([{ username: "", password: "" }]);
const posts = ref<string[]>([""]);
const comments = ref<string[]>([""]);
const concurrency = ref(3);

const logs = ref<string[]>([]);
const loading = ref(false);

let eventSource: EventSource | null = null;

// Functions
const addAccount = () => accounts.value.push({ username: "", password: "" });
const removeAccount = (index: number) => accounts.value.splice(index, 1);
const addPost = () => posts.value.push("");
const removePost = (index: number) => posts.value.splice(index, 1);
const addComment = () => comments.value.push("");
const removeComment = (index: number) => comments.value.splice(index, 1);

const startAutoComment = async () => {
  // Validation
  if (!accounts.value.length || !posts.value.length || !comments.value.length) {
    alert("Please add at least one account, post, and comment!");
    return;
  }

  logs.value = [];
  loading.value = true;

  // Close existing connection if any
  if (eventSource) eventSource.close();

  // Use Fetch + SSE polyfill
  const payload = {
    accounts: accounts.value,
    posts: posts.value,
    comments: comments.value,
    concurrency: concurrency.value,
  };

  // Create a Blob URL to mimic SSE for POST
  const response = await fetch(
    "http://localhost:5000/facebook/auto_comment_multi",
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }
  );

  if (!response.body) {
    alert("No response from server.");
    loading.value = false;
    return;
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();

  eventSource = {
    close: () => reader.cancel(),
  } as any;

  const readStream = async () => {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      const chunk = decoder.decode(value);
      chunk.split("\n\n").forEach((line) => {
        if (line.startsWith("data: ")) {
          const log = line.replace("data: ", "").trim();
          logs.value.push(log);
          nextTick(() => {
            const container = document.getElementById("log-container");
            if (container) container.scrollTop = container.scrollHeight;
          });
        }
      });
    }
    loading.value = false;
  };

  readStream();
};

const stopAutoComment = () => {
  eventSource?.close();
  loading.value = false;
  eventSource = null;
};

onBeforeUnmount(() => stopAutoComment());
</script>

<template>
  <ElCard class="p-4">
    <h2 class="mb-4 text-lg font-bold">Auto Comment Multi</h2>

    <!-- Accounts -->
    <div class="mb-4">
      <h3 class="font-semibold mb-2">Accounts</h3>
      <div
        v-for="(acc, index) in accounts"
        :key="index"
        class="flex gap-2 mb-2"
      >
        <ElInput v-model="acc.username" placeholder="Username" />
        <ElInput
          v-model="acc.password"
          type="password"
          placeholder="Password"
        />
        <ElButton type="danger" @click="removeAccount(index)">Remove</ElButton>
      </div>
      <ElButton type="primary" @click="addAccount">Add Account</ElButton>
    </div>

    <!-- Posts -->
    <div class="mb-4">
      <h3 class="font-semibold mb-2">Post URLs</h3>
      <div v-for="(post, index) in posts" :key="index" class="flex gap-2 mb-2">
        <ElInput v-model="posts[index]" placeholder="Post URL" />
        <ElButton type="danger" @click="removePost(index)">Remove</ElButton>
      </div>
      <ElButton type="primary" @click="addPost">Add Post</ElButton>
    </div>

    <!-- Comments -->
    <div class="mb-4">
      <h3 class="font-semibold mb-2">Comments</h3>
      <div
        v-for="(commentText, index) in comments"
        :key="index"
        class="flex gap-2 mb-2"
      >
        <ElInput v-model="comments[index]" placeholder="Comment Text" />
        <ElButton type="danger" @click="removeComment(index)">Remove</ElButton>
      </div>
      <ElButton type="primary" @click="addComment">Add Comment</ElButton>
    </div>

    <!-- Concurrency -->
    <ElForm class="mb-4">
      <ElFormItem label="Concurrency">
        <ElInput v-model.number="concurrency" type="number" min="1" />
      </ElFormItem>
    </ElForm>

    <!-- Buttons -->
    <div class="flex gap-2 mb-4">
      <ElButton type="success" :loading="loading" @click="startAutoComment"
        >Start</ElButton
      >
      <ElButton @click="stopAutoComment">Stop</ElButton>
    </div>

    <!-- Logs -->
    <div
      id="log-container"
      class="h-64 overflow-auto border p-2 bg-gray-50 font-mono"
    >
      <div v-for="(log, index) in logs" :key="index">{{ log }}</div>
    </div>
  </ElCard>
</template>

<style scoped>
#log-container {
  white-space: pre-wrap;
}
</style>
