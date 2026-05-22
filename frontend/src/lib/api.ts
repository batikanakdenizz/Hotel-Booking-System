import axios from "axios";
import { firebaseAuth } from "@/lib/firebase";

const baseURL = import.meta.env.VITE_API_GATEWAY_URL || "/api";

export const api = axios.create({ baseURL, timeout: 30000 });

// Attach Firebase ID token on every request if signed in.
api.interceptors.request.use(async (config) => {
  const user = firebaseAuth.currentUser;
  if (user) {
    const token = await user.getIdToken();
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});
