import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    hot: true,
    watch: {
      usePolling: true,
    },
    allowedHosts: ['sunshine.cise.ufl.edu'],
    proxy: {
      '/api': {
        target: 'https://app:5000', // The backend API endpoint
        changeOrigin: true,
        secure: false,
        // Optional: If you need to rewrite paths, do it here
        // rewrite: (path) => path.replace(/^\/api/, '')
      },
    },
    // allowedHosts is optional here
  },
});
