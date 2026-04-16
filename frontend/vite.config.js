import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    allowedHosts: ["srv334254.taild63637.ts.net"],
    proxy: {
      '/api': 'http://localhost:8000',
    },
  },
})
