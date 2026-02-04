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
      '.gpuhub.com',
      '.seetacloud.com',
      '.autodl.com'
    ],
    proxy: {
      '/api': {
        target: 'http://localhost:6008',
        changeOrigin: true,
        configure: (proxy, options) => {
          proxy.on('error', (err, req, res) => {
            console.log('proxy error', err);
          });
          proxy.on('proxyReq', (proxyReq, req, res) => {
            console.log('Proxying:', req.method, req.url, '-> http://localhost:6008' + req.url);
          });
        }
      },
      '/uploads': {
        target: 'http://localhost:6008',
        changeOrigin: true
      }
    }
  }
})
