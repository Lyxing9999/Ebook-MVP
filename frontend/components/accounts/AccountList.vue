<template>
  <div>
    <!-- Select All / Remove/Restore Buttons -->
    <div class="flex gap-2 mb-4">
      <ElButton type="primary" @click="selectAllAccounts">Select All</ElButton>
      <ElButton
        :type="isAccountsCleared ? 'default' : 'warning'"
        @click="toggleRemoveRestore"
      >
        {{ isAccountsCleared ? "Restore All" : "Remove All" }}
      </ElButton>
    </div>

    <!-- Scrollable Accounts List -->
    <div class="account-list" style="max-height: 400px; overflow-y: auto">
      <div
        v-for="(acc, index) in localAccounts"
        :key="index"
        class="flex gap-2 m-2"
      >
        <ElCheckbox v-model="acc.selected" />
        <ElInput v-model="acc.username" placeholder="Username" />
        <ElInput v-model="acc.password" placeholder="Password" />
        <ElButton type="danger" @click="removeAccount(index)">Remove</ElButton>
      </div>
    </div>

    <ElButton type="primary" @click="addAccount" class="mt-4"
      >Add Account</ElButton
    >
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted } from "vue";
import { ElButton, ElCheckbox, ElInput } from "element-plus";
import { useAccountStore } from "~/stores/account";

const accountStore = useAccountStore();

const props = defineProps({
  accounts: { type: Array, required: true },
});

const emit = defineEmits(["update:accounts"]);

const isAccountsCleared = ref(false);

// Create a local reactive copy to avoid mutating props directly
const localAccounts = ref([...props.accounts]);

// Sync localAccounts with parent when props.accounts change
watch(
  () => props.accounts,
  (newVal) => {
    localAccounts.value = [...newVal];
  },
  { deep: true }
);

// Emit updates to parent whenever localAccounts change
watch(
  localAccounts,
  (newVal) => {
    emit("update:accounts", newVal);
  },
  { deep: true }
);

const addAccount = () => {
  localAccounts.value.push({ username: "", password: "", selected: false });
};

const removeAccount = (index: number) => {
  localAccounts.value.splice(index, 1);
};

const removeAllAccounts = () => {
  localAccounts.value.splice(0, localAccounts.value.length);
  isAccountsCleared.value = true;
};

const restoreAllAccounts = async () => {
  await accountStore.getAccounts(); // Fetch from store
  localAccounts.value = accountStore.data.map((acc) => ({
    ...acc,
    selected: false,
  }));
  isAccountsCleared.value = false;
};

const toggleRemoveRestore = () => {
  isAccountsCleared.value ? restoreAllAccounts() : removeAllAccounts();
};

const selectAllAccounts = () => {
  const selectAll = !localAccounts.value.every((acc) => acc.selected);
  localAccounts.value.forEach((acc) => (acc.selected = selectAll));
};

// Load accounts on mounted if empty
onMounted(() => {
  if (!localAccounts.value.length) {
    accountStore.getAccounts().then(() => {
      localAccounts.value = accountStore.data.map((acc) => ({
        ...acc,
        selected: false,
      }));
    });
  }
});
</script>
