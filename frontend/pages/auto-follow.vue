<script setup lang="ts">
import { ref, onMounted } from "vue";
import { ElInput, ElButton, ElCard, ElForm, ElFormItem } from "element-plus";
import AccountList from "~/components/accounts/AccountList.vue";
import { useAccountStore } from "~/stores/account"; // Ensure correct import of account store

definePageMeta({ layout: "main" });

const accounts = ref<
  { username: string; password: string; selected: boolean }[]
>([{ username: "", password: "", selected: false }]);

const urlsToFollow = ref<string[]>([
  "https://m.facebook.com/page1",
  "https://m.facebook.com/page2",
]);

const concurrency = ref(3);
const logs = ref<string[]>([]);
const loading = ref(false);

// Add new URL to follow
const addUrl = () => urlsToFollow.value.push("");

// Remove URL
const removeUrl = (index: number) => urlsToFollow.value.splice(index, 1);

// Start Auto Follow
const startAutoFollow = async () => {
  if (accounts.value.length === 0 || urlsToFollow.value.length === 0) {
    alert("Please add at least one account and one URL.");
    return;
  }

  loading.value = true;
  logs.value = [];

  const payload = {
    accounts: accounts.value.filter((acc) => acc.selected),
    urls_to_follow: urlsToFollow.value,
    concurrency: concurrency.value,
  };

  try {
    const response = await fetch(
      "http://localhost:5000/facebook/auto_follow_multi",
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      }
    );

    if (!response.body) throw new Error("No response from server");

    const reader = response.body.getReader();
    const decoder = new TextDecoder();

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      const chunk = decoder.decode(value);
      chunk.split("\n\n").forEach((line) => {
        if (line.startsWith("data: ")) {
          const log = line.replace("data: ", "").trim();
          logs.value.push(log);
          const container = document.getElementById("log-container");
          if (container) container.scrollTop = container.scrollHeight; // Auto-scroll to bottom
        }
      });
    }
  } catch (err) {
    logs.value.push(`Error: ${(err as Error).message}`);
  } finally {
    loading.value = false;
  }
};

// Stop Auto Follow
const stopAutoFollow = () => {
  loading.value = false;
};

// Get accounts from the store
const accountStore = useAccountStore();
onMounted(async () => {
  await accountStore.getAccounts();
  accounts.value = accountStore.data.map((acc) => ({
    username: acc.username,
    password: acc.password,
    selected: false, // Default selected to false
  }));
});

// Update accounts from AccountList component
const updateAccounts = (
  updatedAccounts: { username: string; password: string; selected: boolean }[]
) => {
  accounts.value = updatedAccounts;
};
</script>
<template>
  <el-row :gutter="20">
    <el-col :span="12">
      <ElCard>
        <!-- URLs Section -->
        <div class="mb-4">
          <h3 class="font-semibold mb-2">Pages to Follow</h3>
          <div
            v-for="(url, index) in urlsToFollow"
            :key="index"
            class="flex gap-2 mb-2"
          >
            <ElInput v-model="urlsToFollow[index]" placeholder="Page URL" />
            <ElButton type="danger" @click="removeUrl(index)">Remove</ElButton>
          </div>

          <ElButton type="primary" @click="addUrl">Add URL</ElButton>
        </div>

        <!-- Concurrency Section -->
        <ElForm class="mb-4">
          <ElFormItem label="Max Concurrency">
            <ElInput v-model.number="concurrency" type="number" min="1" />
          </ElFormItem>
        </ElForm>

        <!-- Start Button Section -->
        <div class="flex gap-2 mb-4">
          <ElButton type="success" :loading="loading" @click="startAutoFollow"
            >Start Auto Follow</ElButton
          >
          <ElButton type="danger" @click="stopAutoFollow">Stop</ElButton>
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
        <h3 class="font-semibold mb-2">Accounts</h3>
        <AccountList :accounts="accounts" @update:accounts="updateAccounts" />
      </ElCard>
    </el-col>
  </el-row>
</template>

<style scoped>
#log-container {
  white-space: pre-wrap;
}

.el-button {
  margin-top: 10px;
}
</style>
