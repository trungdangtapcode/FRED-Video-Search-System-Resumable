import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import path from "path"

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(),
    tailwindcss(),
  ],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  server: {
    host: '127.0.0.1',
    port: 5174,
    strictPort: true,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:50313',
        changeOrigin: true,
        rewrite: (requestPath) => requestPath.replace(/^\/api/, ''),
      },
      '/media': {
        target: 'http://127.0.0.1:8069',
        changeOrigin: true,
        rewrite: (requestPath) => requestPath.replace(/^\/media/, ''),
      },
      '/submit-api': {
        target: 'http://127.0.0.1:13022',
        changeOrigin: true,
        rewrite: (requestPath) => requestPath.replace(/^\/submit-api/, ''),
      },
    },
  },
})
