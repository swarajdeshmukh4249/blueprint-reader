import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tsconfigPaths from "vite-tsconfig-paths";

export default defineConfig({
  build: {
    sourcemap: 'hidden',
  },
  plugins: [
    react({
      babel: {
        plugins: [
          'react-dev-locator',
        ],
      },
    }),
    tsconfigPaths()
  ],
  server: {
    // Proxy API calls through Vite so the browser always talks to the same
    // origin (avoids localhost vs 127.0.0.1 and CORS issues in local dev).
    proxy: {
      '/api/v1': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      '/analyze-blueprint': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      '/export': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
    },
  },
})