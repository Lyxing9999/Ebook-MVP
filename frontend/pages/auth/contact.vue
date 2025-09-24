<template>
  <div class="contact-page">
    <el-card class="contact-card" shadow="hover">
      <h2 class="contact-title">Contact Us</h2>

      <div class="contact-info">
        <p><strong>Phone:</strong> 012 440 122</p>
        <p><strong>Telegram:</strong> @KAINGBUNCHHAY</p>
        <img src="/t_me-kaingbunchhay.jpg" alt="Telegram QR Code" />
      </div>

      <el-button
        type="primary"
        size="large"
        @click="goToLogin"
        class="back-btn"
      >
        Back to Login
      </el-button>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from "vue-router";

const router = useRouter();

const goToLogin = () => {
  router.push("/auth/login");
};
</script>

<style scoped>
.contact-page {
  min-height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  background: linear-gradient(135deg, #f0f4f8, #d9e2ec);
}

.contact-card {
  width: 100%;
  max-width: 400px;
  padding: 40px 30px;
  border-radius: 12px;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
  text-align: center;
}

.contact-title {
  font-size: 28px;
  font-weight: 600;
  margin-bottom: 30px;
  color: #2c3e50;
}

.contact-info p {
  font-size: 16px;
  margin-bottom: 10px;
}

.qr-code {
  width: 200px;
  height: 200px;
  margin: 20px 0;
  border-radius: 12px;
}

.back-btn {
  width: 100%;
  margin-top: 20px;
}
</style>
