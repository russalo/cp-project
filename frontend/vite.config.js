import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Port 5173 is already claimed by project-sentinel on this machine, so cp-project
// pins 5174. Both tailnet hostnames are allowlisted so local dev and access from
// the user's Mac / iPad / phone via MagicDNS both work.
export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    port: 5174,
    strictPort: true,
    allowedHosts: [
      'origin-core',
      'origin-core.taild63637.ts.net',
      'srv334254.taild63637.ts.net',
    ],
    proxy: {
      '/api': 'http://localhost:8000',
    },
  },
})
