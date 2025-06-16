import {svelte} from '@sveltejs/vite-plugin-svelte'
import tailwindcss from '@tailwindcss/vite'
import path from 'path'

/** @type {import('vite').UserConfig}*/
export default {
    build: {
        rollupOptions: {
            output: {
                entryFileNames: `assets/[name].js`,
                chunkFileNames: `assets/[name].js`,
                assetFileNames: `assets/[name].[ext]`,
                inlineDynamicImports: true,
            },
        },
        sourcemap: true,
    },
    plugins: [svelte(), tailwindcss()],
    resolve: {
        alias: {
            $lib: path.resolve('./src/lib'),
        },
    },
    server: {
        proxy: {
            '/api': {
                target: 'http://localhost:' + process.env.GRANIAN_PORT,
                changeOrigin: true,
            },
        },
    },
}
