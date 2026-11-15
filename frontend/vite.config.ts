import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    // Bind to IPv4 loopback so both http://localhost:5173 and
    // http://127.0.0.1:5173 work. Vite otherwise binds to ::1 on Windows,
    // which makes 127.0.0.1 refuse connections.
    host: '127.0.0.1',
    port: 5173,
  },
})
