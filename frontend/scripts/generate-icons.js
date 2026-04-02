import sharp from 'sharp'
import { readFileSync } from 'fs'
import { fileURLToPath } from 'url'
import { dirname, resolve } from 'path'

const __dirname = dirname(fileURLToPath(import.meta.url))
const svgPath = resolve(__dirname, '../public/favicon.svg')
const svg = readFileSync(svgPath)

const icons = [
  { size: 16,  name: 'favicon-16x16.png' },
  { size: 32,  name: 'favicon-32x32.png' },
  { size: 180, name: 'apple-touch-icon.png' },
  { size: 192, name: 'icon-192x192.png' },
  { size: 512, name: 'icon-512x512.png' },
]

for (const { size, name } of icons) {
  await sharp(svg)
    .resize(size, size)
    .png()
    .toFile(resolve(__dirname, '../public', name))
  console.log(`✓ ${name} (${size}×${size})`)
}
