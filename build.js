import {execSync as exec} from 'child_process'
import {apply_repls} from 'components/src/util.js'
import {readFileSync,writeFileSync as write} from 'fs'
import {minify} from 'terser'

import pkg from './package.json' with {type: 'json'}

const r = p => readFileSync(p, 'utf8')
const min_js = (s, conf) => minify(s, {module: true, mangle: {module: true}, compress: {module: true, unsafe: false, global_defs: {'window.__DEBUG__': false}}, format: {comments: false}, ...conf})

// Sentry
// const sentry_url = `https://sentry.nuqayah.com/js-sdk-loader/${pkg.config.sentry_dsn}.min.js`
// const sentry = apply_repls(await (await fetch(sentry_url)).text(), [
//     ['index.min.js', 'index.replay.min.js'],
//     ['.replayIntegration()', '.replayIntegration({maskAllInputs: false, maskAllText: false})'],
//     [/{(?="dsn":)/, `{"release": "${pkg.version}",`],
//     [/("tracesSampleRate"):1/, '$1:0'],
// ]).trim()

// Service worker
// write('dist/sw.js', (await min_js(apply_repls(r('src/util/sw.js'), [
//     ['$TS$', Date.now()],
//     ['$POLYFILLS$', pf_url],
//     ['$SENTRY$', sentry.match(/https:\/\/browser.sentry-cdn.com.*?\.js/)[0]],
// ]))).code)

// Minify
const {code, map} = await min_js({'index.js': r('dist/assets/index.js')}, {sourceMap: {content: r('dist/assets/index.js.map')}})

// Write index and sourcemap
write('dist/assets/index-final.js', code + '\n//# sourceMappingURL=index-final.js.map')
write('dist/assets/index-final.js.map', map)

// Upload to sentry
// exec(`sentry-cli sourcemaps inject -o sentry -p ${pkg.name} -r ${pkg.version} ./dist/assets/index-final.js*`, {stdio: 'inherit'})
// exec(`sentry-cli sourcemaps upload -o sentry -p ${pkg.name} -r ${pkg.version} ./dist/assets/index-final.js*`, {stdio: 'inherit'})

const scripts = [
    // `<script>${sentry};${pf_script}</script>`,
    `<script type=module>${r('dist/assets/index-final.js').replace(/\/\/# sourceMappingURL=.*/, '').trim()}</script>`,
    // `<script defer data-domain="${pkg.config.domain}" src="https://a9s.nuqayah.com/js/script.js"></script>`,
]

// Combine
const pg = apply_repls(r('index.html'), [
    [/\n+ */g, ''], // important for sentry
    [/(?<=<\/title>)/, () => `<style>${r(`dist/assets/index.css`)}</style>`],
    [/<script src.+<\/script>/, () => scripts.join('')],
])
write('dist/index.html', pg)
