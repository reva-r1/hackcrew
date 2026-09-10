import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  base: '/static/',
  plugins: [react()],
  build: {
    outDir: '../static',
    emptyOutDir: false,
    rollupOptions: {
      output: {
        entryFileNames: 'assets/[name].js',
        chunkFileNames: 'assets/[name].js',
        assetFileNames: 'assets/[name].[ext]'
      }
    }
  },
  server: {
    port: 5173,
    proxy: {
      '/query': 'http://localhost:8000',
      '/upload': 'http://localhost:8000',
      '/preview-confidence': 'http://localhost:8000',
      '/chunks': 'http://localhost:8000',
      '/uploaded-files': 'http://localhost:8000',
      '/logs': 'http://localhost:8000',
      '/health': 'http://localhost:8000',
      '/clear-all': 'http://localhost:8000',
      '/uploads': 'http://localhost:8000'
    }
  }
});
