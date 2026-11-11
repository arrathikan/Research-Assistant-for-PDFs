// Copy only the installed PDF.js version's fonts/CMaps; no CDN or new build plugin.
import { cpSync, mkdirSync, readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
const root = new URL('../node_modules/pdfjs-dist/', import.meta.url);
const { version } = JSON.parse(readFileSync(new URL('package.json', root), 'utf8'));
if (!/^[0-9]+\.[0-9]+\.[0-9]+$/.test(version)) throw new Error('Unexpected PDF.js version');
for (const folder of ['cmaps', 'standard_fonts']) {
  const destination = new URL(`../public/pdfjs/${version}/${folder}/`, import.meta.url);
  mkdirSync(destination, { recursive: true });
  cpSync(fileURLToPath(new URL(folder, root)), fileURLToPath(destination), { recursive: true });
}
