import {svelte} from '@sveltejs/vite-plugin-svelte'
import tailwindcss from '@tailwindcss/vite'
import path from 'path'
import {defineConfig} from 'vite'

// https://vite.dev/config/
export default defineConfig({
    plugins: [svelte(), tailwindcss()],
    resolve: {
        alias: {
            $lib: path.resolve('./src/lib'),
        },
    },
    server: {
        proxy: {
            '/api': {
                target: 'http://localhost:8000',
                changeOrigin: true,
            },
        },
    },
})
