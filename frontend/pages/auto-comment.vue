<script setup lang="ts">
import { ref, nextTick, onBeforeUnmount, onMounted } from "vue";
import { ElInput, ElButton, ElCard, ElForm, ElFormItem } from "element-plus";
import { useAccountStore } from "~/stores/account";
import AccountList from "~/components/accounts/AccountList.vue";

definePageMeta({ layout: "main" });

interface Account {
  username: string;
  password: string;
  selected: boolean;
}

const accountStore = useAccountStore();

// Form state
const accounts = ref<Account[]>([]);
const posts = ref<string[]>([""]);
const comments = ref<string[]>([""]);
const concurrency = ref(3);

const logs = ref<string[]>([]);
const loading = ref(false);

let eventSource: EventSource | null = null;

// Load accounts from store on mount
onMounted(async () => {
  await accountStore.getAccounts();
  accounts.value = accountStore.data.map((acc) => ({
    username: acc.username,
    password: acc.password,
    selected: false, // Default selected to false
  }));
});

// Functions for managing posts and comments
const addPost = () => posts.value.push("");
const removePost = (index: number) => posts.value.splice(index, 1);

const addComment = () => comments.value.push("");
const removeComment = (index: number) => comments.value.splice(index, 1);

// Function to start auto-commenting
const startAutoComment = async () => {
  const selectedAccounts = accounts.value.filter((acc) => acc.selected);

  if (
    !selectedAccounts.length ||
    !posts.value.length ||
    !comments.value.length
  ) {
    alert("Please add at least one selected account, post, and comment!");
    return;
  }

  logs.value = [];
  loading.value = true;
  eventSource?.close();

  const payload = {
    accounts: selectedAccounts,
    posts: posts.value,
    comments: comments.value,
    concurrency: concurrency.value,
  };

  try {
    const response = await fetch(
      "http://localhost:5000/facebook/auto_comment_multi",
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      }
    );

    if (!response.body) throw new Error("No response from server");

    const reader = response.body.getReader();
    const decoder = new TextDecoder();

    eventSource = { close: () => reader.cancel() } as any;

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
  } catch (err: any) {
    logs.value.push(`Error: ${err.message}`);
  } finally {
    loading.value = false;
  }
};

// Function to stop auto-commenting
const stopAutoComment = () => {
  eventSource?.close();
  loading.value = false;
  eventSource = null;
};

// Update accounts when the AccountList component modifies the list
const updateAccounts = (updatedAccounts: Account[]) => {
  accounts.value = updatedAccounts;
  // Optionally, sync the changes to the store if needed:
  // accountStore.updateAccounts(updatedAccounts);
};

onBeforeUnmount(() => stopAutoComment());
</script>
<template>
  <el-row :gutter="20">
    <el-col :span="12">
      <ElCard>
        <!-- Posts Section -->
        <div class="mb-4">
          <h3 class="font-semibold mb-2">Post URLs</h3>
          <div
            v-for="(post, index) in posts"
            :key="index"
            class="flex gap-2 mb-2"
          >
            <ElInput v-model="posts[index]" placeholder="Post URL" />
            <ElButton type="danger" @click="removePost(index)">Remove</ElButton>
          </div>
          <ElButton type="primary" @click="addPost">Add Post</ElButton>
        </div>

        <!-- Comments Section -->
        <div class="mb-4">
          <h3 class="font-semibold mb-2">Comments</h3>
          <div
            v-for="(comment, index) in comments"
            :key="index"
            class="flex gap-2 mb-2"
          >
            <ElInput
              v-model="comments[index]"
              type="textarea"
              placeholder="Comment Text"
            />
            <ElButton type="danger" @click="removeComment(index)"
              >Remove</ElButton
            >
          </div>
          <ElButton type="primary" @click="addComment">Add Comment</ElButton>
        </div>

        <!-- Concurrency Section -->
        <ElForm class="mb-4">
          <ElFormItem label="Chrome Open">
            <ElInput v-model.number="concurrency" type="number" min="1" />
          </ElFormItem>
        </ElForm>

        <!-- Buttons Section -->
        <div class="flex gap-2 mb-4">
          <ElButton type="success" :loading="loading" @click="startAutoComment"
            >Start</ElButton
          >
          <ElButton @click="stopAutoComment">Stop</ElButton>
        </div>

        <!-- Logs Section -->
        <div
          id="log-container"
          class="h-64 overflow-auto border p-2 bg-gray-50 font-mono"
        >
          <div v-for="(log, index) in logs" :key="index">{{ log }}</div>
        </div>
      </ElCard>
    </el-col>

    <!-- Accounts Section -->
    <el-col :span="12">
      <ElCard>
        <div class="mb-4">
          <h3 class="font-semibold mb-2">Accounts</h3>
          <!-- Reusable Account List Component -->
          <AccountList :accounts="accounts" @update:accounts="updateAccounts" />
        </div>
      </ElCard>
    </el-col>
  </el-row>
</template>

<style scoped>
#log-container {
  white-space: pre-wrap;
}

.account-list {
  max-height: 400px;
  overflow-y: auto;
}
</style>

<style scoped>
#log-container {
  white-space: pre-wrap;
}

.account-list {
  max-height: 400px;
  overflow-y: auto;
}
</style>
