import { defineStore } from "pinia";
import { ref } from "vue";
import axios from "axios";

export enum AccountStatus {
  normal = "normal",
  banned = "banned",
}

export type Account = {
  _id: string;
  index: number;
  username: string;
  password: string;
  status: AccountStatus;
};

export const useAccountStore = defineStore("account", () => {
  // State
  const data = ref<Account[]>([]);
  const loading = ref(false);
  const dialogVisible = ref(false);
  const form = ref({ username: "", password: "" });
  const isEnabled = ref(true); // Flag to enable/disable accounts

  // Actions
  const addIndexToData = (data: Account[]) => {
    return data.map((item, index) => ({
      ...item,
      index: index + 1, // Add index field to each row (1-based index)
    }));
  };

  const clearAccounts = () => {
    data.value = [];
  };

  const getAccounts = async () => {
    try {
      loading.value = true;
      const res = await axios.get(
        "http://localhost:5000/facebook/get_accounts"
      );
      data.value = addIndexToData(res.data);
    } catch (err) {
      console.error(err);
    } finally {
      loading.value = false;
    }
  };

  const addAccount = async () => {
    try {
      loading.value = true;
      await axios.post(
        "http://localhost:5000/facebook/save_account",
        form.value
      );
      form.value.username = "";
      form.value.password = "";
      dialogVisible.value = false;
      await getAccounts();
    } catch (err) {
      console.error(err);
    } finally {
      loading.value = false;
    }
  };

  const deleteAccount = async (id: string) => {
    try {
      loading.value = true;
      await axios.delete(`http://localhost:5000/facebook/delete_account/${id}`);
      await getAccounts();
    } catch (err) {
      console.error(err);
    } finally {
      loading.value = false;
    }
  };

  // Toggle the accounts usage (enabled/disabled)
  const toggleAccounts = async () => {
    isEnabled.value = !isEnabled.value;

    if (!isEnabled.value) {
      clearAccounts(); // Clear accounts if disabled
    } else {
      // Fetch accounts only if they haven't been fetched yet or if you want to always fetch new data
      if (data.value.length === 0) {
        await getAccounts(); // Fetch accounts if they are empty
      }
    }
  };

  return {
    data,
    loading,
    dialogVisible,
    form,
    isEnabled, // Make this accessible to the component
    getAccounts,
    addAccount,
    deleteAccount,
    clearAccounts,
    toggleAccounts, // Action to toggle accounts
  };
});
