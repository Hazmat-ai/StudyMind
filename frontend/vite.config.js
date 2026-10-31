import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
const proxy = {
  "/api": { target: "http://localhost:8000", changeOrigin: true },
};
export default defineConfig({
  plugins: [react()],
  server: { proxy },
  preview: { proxy },
});
