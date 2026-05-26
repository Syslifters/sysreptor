/**
 * Self-hosted Iconify data via installed @iconify-json sets (bundled by Vite).
 * Uses @iconify/vue/offline — no Iconify API requests.
 */
import { addCollection } from '@iconify/vue/offline'
import mdi from '@iconify-json/mdi/icons.json'
import octicons from '@iconify-json/octicon/icons.json'

addCollection(octicons)
addCollection(mdi)
