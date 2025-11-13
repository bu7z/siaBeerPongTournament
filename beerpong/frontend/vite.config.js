import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],

  server: {
    allowedHosts: [
      'butzke.it'
    ],
    host: true,        // wichtig, wenn du von außen zugreifst
    port: 5173,        // oder dein custom-Port
  }
})