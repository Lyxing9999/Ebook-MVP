<script lang="ts" setup>
definePageMeta({
  layout: "main",
});

import { ref, onMounted } from "vue";
import axios from "axios";
import { ElMessage } from "element-plus";
import SmartTable from "~/components/TableEdit/core/SmartTable.vue";
import { ElInput, ElButton, ElDialog, ElForm, ElFormItem } from "element-plus";
// --- State ---
const data = ref<any[]>([]);
const loading = ref(false);
const dialogVisible = ref(false);
const form = ref({
  email: "",
  password: "",
});
const addIndexToData = (data: any[]) => {
  return data.map((item, index) => ({
    ...item,
    index: index + 1, // Add index field to each row (1-based index)
  }));
};

// --- Columns for SmartTable ---
import { h } from "vue";

const columns = ref([
  {
    field: "index",
    label: "#",
    width: "50",
  },
  {
    field: "email",
    label: "Email",
    component: ElInput,
    inlineEditActive: false,
  },
  {
    field: "password",
    label: "Password",
    component: ElInput,
    inlineEditActive: false,
  },
  {
    field: "operation",
    label: "Actions",
    operation: true,
    render: (row: any) =>
      h(
        "el-button",
        {
          type: "danger",
          size: "small",
          onClick: () => deleteAccount(row._id),
        },
        () => "Delete"
      ),
  },
]);

// --- Fetch accounts ---
const getAccounts = async () => {
  try {
    loading.value = true;
    const res = await axios.get("http://localhost:5000/facebook/get_accounts");
    console.log(res.data);
    data.value = addIndexToData(res.data);
    console.log(data.value);
  } catch (err) {
    console.error(err);
    ElMessage.error("Failed to load accounts");
  } finally {
    loading.value = false;
  }
};

// --- Add account ---
const addAccount = () => {
  dialogVisible.value = true;
};

const addAccountSubmit = async () => {
  try {
    loading.value = true;
    await axios.post("http://localhost:5000/facebook/save_account", form.value);
    dialogVisible.value = false;
    form.value.email = "";
    form.value.password = "";
    ElMessage.success("Account added successfully");
    await getAccounts();
  } catch (err: any) {
    console.error(err);
    ElMessage.error(err.response?.data?.error || "Failed to add account");
  } finally {
    loading.value = false;
  }
};

// --- Delete account ---
const deleteAccount = async (id: string) => {
  try {
    loading.value = true;
    await axios.delete(`http://localhost:5000/facebook/delete_account/${id}`);
    ElMessage.success("Account deleted successfully");
    await getAccounts();
  } catch (err) {
    console.error(err);
    ElMessage.error("Failed to delete account");
  } finally {
    loading.value = false;
  }
};

// --- Lifecycle ---
onMounted(() => {
  getAccounts();
});
</script>

<template>
  <div class="p-4">
    <el-row>
      <el-col :span="4" justify="center">
        <el-button type="primary" @click="addAccount" :loading="loading">
          Add Account
        </el-button>
      </el-col>
    </el-row>

    <el-dialog
      title="Add Facebook Account"
      v-model="dialogVisible"
      width="500px"
      :close-on-click-modal="false"
    >
      <el-form label-position="top" class="max-w-2xl">
        <el-form-item label="Email">
          <el-input v-model="form.email" />
        </el-form-item>
        <el-form-item label="Password">
          <el-input v-model="form.password" type="password" />
        </el-form-item>
        <el-form-item class="flex justify-end">
          <el-button @click="dialogVisible = false">Cancel</el-button>
          <el-button
            type="primary"
            @click="addAccountSubmit"
            :loading="loading"
          >
            Add
          </el-button>
        </el-form-item>
      </el-form>
    </el-dialog>

    <div class="mt-4">
      <SmartTable
        :data="data"
        :columns="columns"
        row-key="_id"
        :loading="loading"
      >
        <template #operation="{ row }">
          <el-button type="danger" size="small" @click="deleteAccount(row._id)">
            Delete
          </el-button>
        </template>
      </SmartTable>
    </div>
  </div>
</template>
