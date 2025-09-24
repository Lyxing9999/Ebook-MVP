<script setup lang="ts">
import { ref, onMounted } from "vue";
import { useAccountStore } from "~/stores/account";
import {
  ElMessage,
  ElButton,
  ElDialog,
  ElForm,
  ElFormItem,
  ElInput,
  ElTag,
} from "element-plus";
import SmartTable from "~/components/TableEdit/core/SmartTable.vue";
import { h } from "vue";

definePageMeta({ layout: "main" });

// --- Store ---
const accountStore = useAccountStore();
onMounted(() => accountStore.getAccounts());

// --- Manual textarea for quick add ---
const accountsText = ref("");

// --- Columns for SmartTable ---
const columnsAccounts = ref([
  {
    field: "index",
    label: "#",
    width: "60",
    component: ElInput,
    childComponentProps: { disabled: true, readOnly: true },
  },
  { field: "username", label: "Username", component: ElInput },
  { field: "password", label: "Password", component: ElInput },
  {
    field: "status",
    label: "Status",
    render: (row: any, field: any) => {
      const status = row[field];
      let type: "success" | "danger" | "warning" = "success";
      if (status === "normal") type = "success";
      else if (status === "banned") type = "danger";
      else type = "warning";
      return h(ElTag, { type }, status);
    },
  },
  {
    field: "operation",
    label: "Actions",
    operation: true,
    width: "120",
    render: (row: any) =>
      h(
        ElButton,
        {
          type: "danger",
          size: "small",
          onClick: () => accountStore.deleteAccount(row._id),
        },
        () => "Delete"
      ),
  },
]);

// --- Add multiple accounts from textarea ---
const addMultipleAccounts = async () => {
  if (!accountsText.value.trim()) {
    ElMessage.warning(
      "Please enter accounts in format username,password per line."
    );
    return;
  }

  const lines = accountsText.value.split("\n");
  const accounts = lines
    .map((line) => {
      const [username, password] = line.split(",").map((s) => s.trim());
      if (username && password) return { username, password };
    })
    .filter(Boolean);

  if (accounts.length === 0) return;

  try {
    const res = await fetch("http://localhost:5000/facebook/save_account", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(accounts),
    });
    const data = await res.json();
    console.log(data);
    if (data.success) {
      ElMessage.success(`Saved ${data.saved.length} accounts.`);
      accountStore.getAccounts(); // refresh table
      accountsText.value = "";
    }
  } catch (err) {
    ElMessage.error("Failed to save accounts.");
  }
};
</script>

<template>
  <div class="p-6 max-w-4xl mx-auto">
    <h1 class="text-2xl font-bold mb-4">Facebook Accounts</h1>

    <!-- Manual add textarea -->
    <el-form class="mb-4">
      <el-form-item label="Add Multiple Accounts (username,password per line)">
        <el-input
          type="textarea"
          v-model="accountsText"
          placeholder="user1,pass1\nuser2,pass2"
          :rows="4"
        />
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="addMultipleAccounts"
          >Add Accounts</el-button
        >
      </el-form-item>
    </el-form>

    <!-- Smart Table -->
    <div class="mt-4">
      <SmartTable
        :data="accountStore.data"
        :columns="columnsAccounts"
        row-key="_id"
        :loading="accountStore.loading"
      >
        <template #operation="{ row }">
          <el-button
            type="danger"
            size="small"
            @click="accountStore.deleteAccount(row._id)"
          >
            Delete
          </el-button>
        </template>
      </SmartTable>
    </div>

    <!-- Add single account dialog -->
    <el-dialog
      title="Add Facebook Account"
      v-model="accountStore.dialogVisible"
      width="500px"
      :close-on-click-modal="false"
    >
      <el-form label-position="top" class="max-w-2xl">
        <el-form-item label="Username">
          <el-input v-model="accountStore.form.username" />
        </el-form-item>
        <el-form-item label="Password">
          <el-input type="password" v-model="accountStore.form.password" />
        </el-form-item>
        <el-form-item class="flex justify-end">
          <el-button @click="accountStore.dialogVisible = false"
            >Cancel</el-button
          >
          <el-button
            type="primary"
            @click="accountStore.addAccount"
            :loading="accountStore.loading"
            >Add</el-button
          >
        </el-form-item>
      </el-form>
    </el-dialog>
  </div>
</template>

<style scoped>
textarea,
input {
  font-family: monospace;
}
</style>
