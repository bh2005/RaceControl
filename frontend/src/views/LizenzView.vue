<template>
  <div class="min-h-screen bg-gray-50 py-10 px-4">
    <div class="max-w-3xl mx-auto space-y-6">

      <!-- Header -->
      <div class="flex items-center gap-4">
        <RouterLink to="/" class="text-sm text-msc-blue hover:underline">← Zurück</RouterLink>
        <h1 class="text-2xl font-bold text-gray-900">Lizenzinformationen</h1>
      </div>

      <!-- Projektinfo -->
      <div class="card p-6 space-y-3">
        <div class="flex items-start justify-between gap-4">
          <div>
            <h2 class="text-lg font-bold text-gray-800">RaceControl Pro</h2>
            <p class="text-sm text-gray-500">Modulare Veranstaltungssoftware für Kart-Slalom</p>
          </div>
          <span class="text-xs font-mono bg-msc-blue/10 text-msc-blue px-2 py-1 rounded">v0.1.0</span>
        </div>
        <dl class="grid grid-cols-2 gap-x-6 gap-y-2 text-sm">
          <div>
            <dt class="text-xs text-gray-400 font-semibold uppercase tracking-wide">Lizenz</dt>
            <dd class="font-semibold text-gray-800">GNU General Public License v2.0</dd>
          </div>
          <div>
            <dt class="text-xs text-gray-400 font-semibold uppercase tracking-wide">Copyright</dt>
            <dd class="text-gray-700">© 2025–2026 MSC Braach e.V. im ADAC</dd>
          </div>
          <div>
            <dt class="text-xs text-gray-400 font-semibold uppercase tracking-wide">Backend</dt>
            <dd class="text-gray-700">Python 3.11 · FastAPI · SQLite</dd>
          </div>
          <div>
            <dt class="text-xs text-gray-400 font-semibold uppercase tracking-wide">Frontend</dt>
            <dd class="text-gray-700">Vue 3 · Vite · Tailwind CSS</dd>
          </div>
        </dl>
      </div>

      <!-- GPL-2.0 Zusammenfassung -->
      <div class="card p-6 space-y-4">
        <h2 class="font-bold text-gray-800">GNU General Public License, Version 2</h2>
        <p class="text-sm text-gray-600 leading-relaxed">
          Diese Software ist freie Software: Sie dürfen sie unter den Bedingungen der
          <strong>GNU General Public License</strong>, wie von der Free Software Foundation
          veröffentlicht, weitergeben und/oder modifizieren — entweder gemäß Version 2 der Lizenz
          oder (nach Ihrer Wahl) einer späteren Version.
        </p>
        <p class="text-sm text-gray-600 leading-relaxed">
          Diese Software wird in der Hoffnung bereitgestellt, dass sie nützlich ist, aber
          <strong>ohne jede Gewährleistung</strong> — sogar ohne die implizite Gewährleistung der
          Marktreife oder der Eignung für einen bestimmten Zweck.
          Details finden Sie in der GNU General Public License.
        </p>

        <div class="rounded-xl bg-blue-50 border border-blue-200 px-4 py-3 text-sm text-blue-800 space-y-1">
          <div class="font-bold">Ihre Rechte unter der GPL-2.0</div>
          <ul class="list-disc list-inside space-y-0.5 text-xs text-blue-700">
            <li>Software für jeden Zweck verwenden</li>
            <li>Quellcode einsehen und studieren</li>
            <li>Software modifizieren und anpassen</li>
            <li>Kopien weitergeben — auch modifizierte Versionen, ebenfalls unter GPL-2.0</li>
          </ul>
        </div>

        <a href="https://www.gnu.org/licenses/old-licenses/gpl-2.0.html"
           target="_blank" rel="noopener noreferrer"
           class="inline-flex items-center gap-1.5 text-sm font-semibold text-msc-blue hover:underline">
          Vollständiger Lizenztext auf gnu.org
          <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
            <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6M15 3h6v6M10 14 21 3"/>
          </svg>
        </a>
      </div>

      <!-- Verwendete Bibliotheken -->
      <div class="card p-6">
        <h2 class="font-bold text-gray-800 mb-3">Verwendete Open-Source-Bibliotheken</h2>
        <table class="w-full text-sm">
          <thead>
            <tr class="text-xs text-gray-400 uppercase tracking-wide border-b border-gray-100">
              <th class="text-left pb-2">Bibliothek</th>
              <th class="text-left pb-2">Lizenz</th>
              <th class="text-left pb-2">Verwendung</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-50">
            <tr v-for="lib in libs" :key="lib.name" class="hover:bg-gray-50">
              <td class="py-2 font-mono text-xs font-semibold text-gray-700">{{ lib.name }}</td>
              <td class="py-2 text-xs text-gray-500">{{ lib.license }}</td>
              <td class="py-2 text-xs text-gray-500">{{ lib.use }}</td>
            </tr>
          </tbody>
        </table>
      </div>

    </div>
  </div>
</template>

<script setup>
const libs = [
  { name: 'FastAPI',          license: 'MIT',         use: 'Backend Web-Framework' },
  { name: 'Uvicorn',          license: 'BSD-3-Clause', use: 'ASGI Server' },
  { name: 'Pydantic',         license: 'MIT',         use: 'Datenvalidierung' },
  { name: 'python-jose',      license: 'MIT',         use: 'JWT-Authentifizierung' },
  { name: 'bcrypt / passlib', license: 'Apache-2.0',  use: 'Passwort-Hashing' },
  { name: 'SQLite',           license: 'Public Domain', use: 'Datenbank' },
  { name: 'Vue 3',            license: 'MIT',         use: 'Frontend Framework' },
  { name: 'Vite',             license: 'MIT',         use: 'Build-Tool' },
  { name: 'Pinia',            license: 'MIT',         use: 'State Management' },
  { name: 'Vue Router',       license: 'MIT',         use: 'Client-seitiges Routing' },
  { name: 'Tailwind CSS',     license: 'MIT',         use: 'CSS-Framework' },
  { name: 'Axios',            license: 'MIT',         use: 'HTTP-Client' },
  { name: 'Workbox',          license: 'MIT',         use: 'Service Worker / PWA' },
]
</script>
