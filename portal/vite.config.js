import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    watch: { usePolling: true }, // necesario para recargar en Windows con Docker
  },
})
