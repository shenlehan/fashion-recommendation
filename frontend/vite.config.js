import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    port: 6006,
    strictPort: true,
    allowedHosts: [
      'u874872-fw84-354e8a3d.westd.seetacloud.com',
      '.seetacloud.com'
    ],
    proxy: {
      '/api': {
        target: 'http://localhost:6008',
        changeOrigin: true,
      }
    }
  }
})
