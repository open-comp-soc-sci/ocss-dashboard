import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
    plugins: [react()],
    server: {
        hot: true, // Ensure HMR is enabled
        watch: {
            usePolling: true, // Helps with file watching issues (optional)
        },
    },
});
