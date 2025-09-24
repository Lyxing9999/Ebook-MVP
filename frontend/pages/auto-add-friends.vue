<template>
  <el-row :gutter="20">
    <el-col :span="12">
      <ElCard>
        <!-- Options Section -->
        <ElForm class="mb-4">
          <ElFormItem label="Max Friends per Account">
            <ElInput v-model.number="maxToAdd" type="number" min="1" />
          </ElFormItem>
          <ElFormItem label="Chrome Open (Concurrency)">
            <ElInput
              v-model.number="concurrentBrowsers"
              type="number"
              min="1"
            />
          </ElFormItem>
        </ElForm>

        <!-- Start/Stop Buttons -->
        <div class="flex gap-2 mb-4">
          <ElButton type="success" :loading="loading" @click="startAutoAdd">
            Start Auto Add Friends
          </ElButton>
          <ElButton type="danger" @click="stopAutoAdd">Stop</ElButton>
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

<script setup lang="ts">
import { ref, onMounted } from "vue";
import { ElInput, ElButton, ElCard, ElForm, ElFormItem } from "element-plus";
import AccountList from "~/components/accounts/AccountList.vue";
import { useAccountStore } from "~/stores/account";

definePageMeta({ layout: "main" });

interface Account {
  username: string;
  password: string;
  selected: boolean;
}

// State
const accounts = ref<Account[]>([
  { username: "", password: "", selected: false },
]);
const maxToAdd = ref(50);
const concurrentBrowsers = ref(5);
const logs = ref<string[]>([]);
const loading = ref(false);

// Store
const accountStore = useAccountStore();

// Load accounts from store
onMounted(async () => {
  await accountStore.getAccounts();
  accounts.value = accountStore.data.map((acc) => ({
    username: acc.username,
    password: acc.password,
    selected: false,
  }));
});

// Update accounts from AccountList
const updateAccounts = (updatedAccounts: Account[]) => {
  accounts.value = updatedAccounts;
};

// Start Auto Add Friends
const startAutoAdd = async () => {
  const selectedAccounts = accounts.value.filter((a) => a.selected);
  if (!selectedAccounts.length) {
    alert("Please select at least one account!");
    return;
  }

  loading.value = true;
  logs.value = [];

  const payload = {
    accounts: selectedAccounts,
    max_to_add: maxToAdd.value,
    concurrent_browsers: concurrentBrowsers.value,
  };

  try {
    const response = await fetch(
      "http://localhost:5000/facebook/auto_add_friends_multi",
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
          if (container) container.scrollTop = container.scrollHeight;
        }
      });
    }
  } catch (err) {
    logs.value.push(`[ERROR] ${(err as Error).message}`);
  } finally {
    loading.value = false;
  }
};

// Stop Auto Add
const stopAutoAdd = () => {
  loading.value = false;
};
</script>

<style scoped>
#log-container {
  white-space: pre-wrap;
}
.el-button {
  margin-top: 10px;
}
</style>
