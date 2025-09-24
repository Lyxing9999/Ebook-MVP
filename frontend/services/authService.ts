// services/authService.ts
import type { AxiosInstance } from "axios";
import { jwtDecode } from "jwt-decode";
import { useRouter } from "nuxt/app";
import { ElMessage } from "element-plus";

interface UserForm {
  email: string;
  password: string;
}

interface AuthResponse {
  access_token: string;
  refresh_token: string;
}

interface UserBaseDataDTO {
  email: string;
  role: string;
  sub?: string;
}

export class AuthService {
  private router = useRouter();
  private message = ElMessage;
  private baseURL = "/api/iam";

  constructor(private $api: AxiosInstance) {}

  private validate(form: UserForm): boolean {
    if (!form.email || !form.password) {
      this.message.warning("Please fill in all fields");
      return false;
    }
    return true;
  }

  // ===== Register =====
  async register(form: UserForm) {
    if (!this.validate(form)) return;
    try {
      const res = await this.$api.post<AuthResponse>(
        `${this.baseURL}/register`,
        form
      );
      this.message.success("Registered successfully, please login");
      await this.router.push("/auth/login");
    } catch (err: any) {
      this.message.error(err?.response?.data?.detail || "Registration failed");
    }
  }

  // ===== Login =====
  async login(form: UserForm) {
    if (!this.validate(form)) return;
    try {
      const res = await this.$api.post<AuthResponse>(
        `${this.baseURL}/login`,
        form
      );
      const token = res.data.access_token;
      if (!token) return this.message.error("No token returned");

      const user = jwtDecode(token) as UserBaseDataDTO;

      // Store in localStorage directly
      localStorage.setItem("access_token", token);
      localStorage.setItem("user", JSON.stringify(user));

      this.message.success("Login successful");
      await this.router.push("/dashboard");
      return res;
    } catch (err: any) {
      this.message.error(err?.response?.data?.detail || "Login failed");
    }
  }

  // ===== Logout =====
  logout() {
    localStorage.removeItem("access_token");
    localStorage.removeItem("user");
    this.router.push("/auth/login");
    this.message.success("Logged out successfully");
  }

  // ===== Get current user =====
  getCurrentUser(): UserBaseDataDTO | null {
    const user = localStorage.getItem("user");
    return user ? JSON.parse(user) : null;
  }

  // ===== Check login =====
  isLoggedIn(): boolean {
    return !!localStorage.getItem("access_token");
  }

  // ===== Google Login (optional MVP) =====
  loginWithGoogle() {
    window.location.href = `${this.baseURL}/auth/google/login`;
  }
}
