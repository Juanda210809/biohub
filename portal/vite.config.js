import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  // Pruebas (npm test): jsdom da window, sessionStorage y location.hash como en el navegador.
  test: { environment: 'jsdom' },
  server: {
    watch: { usePolling: true }, // necesario para recargar en Windows con Docker
  },
})
