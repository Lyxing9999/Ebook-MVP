<template>
  <div class="login-page">
    <el-card class="login-card" shadow="hover">
      <h2 class="login-title">Login</h2>
      <el-input
        v-model="email"
        type="email"
        placeholder="Email"
        size="large"
        class="login-input"
      />
      <el-input
        v-model="password"
        type="password"
        placeholder="Password"
        size="large"
        show-password
        class="login-input"
      />

      <el-button
        type="primary"
        size="large"
        :loading="loading"
        @click="handleLogin"
        class="login-btn"
      >
        Login
      </el-button>

      <div class="register-container">
        <span>Don't have an account?</span>
        <el-button type="text" @click="goToContact" class="register-btn">
          Contact us
        </el-button>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";
import axios from "axios";
import { AuthService } from "~/services/authService";
import { jwtDecode } from "jwt-decode";
import { useRouter } from "vue-router";
import { ElMessage } from "element-plus";

const email = ref("");
const password = ref("");
const loading = ref(false);

const router = useRouter();
const $api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || "http://localhost:5000",
});
const authService = new AuthService($api);

const handleLogin = async () => {
  if (!email.value || !password.value) {
    ElMessage.warning("Please enter email and password");
    return;
  }

  loading.value = true;
  try {
    const res = await authService.login({
      email: email.value,
      password: password.value,
    });
  } catch (err: any) {
    console.error(err);
  } finally {
    loading.value = false;
  }
};

const goToContact = () => router.push("/auth/contact");
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  background: linear-gradient(135deg, #f0f4f8, #d9e2ec);
}

.login-card {
  width: 100%;
  max-width: 400px;
  padding: 40px 30px;
  border-radius: 12px;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
  background-color: #ffffff;
}

.login-title {
  text-align: center;
  margin-bottom: 30px;
  font-size: 28px;
  color: #2c3e50;
  font-weight: 600;
}

.login-input {
  margin-bottom: 20px;
}

.login-btn {
  width: 100%;
  margin-bottom: 20px;
  background-color: #409eff;
  border-color: #409eff;
  font-weight: 500;
}

.login-btn:hover {
  background-color: #66b1ff;
  border-color: #66b1ff;
}

.register-container {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 5px;
  font-size: 14px;
  color: #606266;
}

.register-btn {
  color: #409eff;
  font-weight: 500;
  padding: 0;
}

.register-btn:hover {
  color: #66b1ff;
}
</style>
