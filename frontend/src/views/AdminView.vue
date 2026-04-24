<template>
  <div class="max-w-7xl mx-auto px-4 py-4 pb-12 grid grid-cols-12 gap-4">

    <!-- ── LINKE SPALTE: Nav ── -->
    <aside class="col-span-2 space-y-1">
      <button
        v-for="tab in tabs"
        :key="tab.id"
        @click="activeTab = tab.id"
        class="w-full text-left px-3 py-2 rounded-lg text-sm font-medium transition"
        :class="activeTab === tab.id ? 'bg-msc-blue text-white' : 'hover:bg-gray-200 text-gray-700'"
      >
        {{ tab.label }}
      </button>
    </aside>

    <!-- ── HAUPT-BEREICH ── -->
    <section class="col-span-10">

      <!-- ═══ VERANSTALTUNGEN ═══ -->
      <div v-if="activeTab === 'events'" class="grid grid-cols-3 gap-4">
        <div class="col-span-1 space-y-3">
          <div class="flex items-center justify-between">
            <h2 class="font-bold text-gray-800">Veranstaltungen</h2>
            <button @click="openNewEvent" class="text-xs btn-primary px-3 py-1.5">+ Neu</button>
          </div>
          <div
            v-for="e in events"
            :key="e.id"
            @click="selectEvent(e)"
            class="card p-3 cursor-pointer hover:border-msc-blue/40 transition"
            :class="{ 'border-msc-blue border-2 bg-blue-50/40': activeEvent?.id === e.id }"
          >
            <div class="flex items-center justify-between mb-1">
              <span class="text-xs text-gray-400 font-mono">{{ e.date }}</span>
              <div class="flex items-center gap-1.5">
                <span :class="eventBadge(e.status)" class="text-xs font-bold rounded px-1.5 py-0.5">
                  {{ e.status }}
                </span>
                <button
                  @click.stop="deleteEvent(e)"
                  class="text-gray-300 hover:text-red-500 text-xs leading-none transition"
                  title="Veranstaltung löschen"
                >✕</button>
              </div>
            </div>
            <div class="font-semibold text-sm text-gray-800">{{ e.name }}</div>
          </div>
        </div>

        <div class="col-span-2 space-y-4" v-if="showEventForm">
          <!-- Event-Daten -->
          <div class="card p-4">
            <h3 class="font-bold text-gray-800 mb-3">
              {{ activeEvent ? activeEvent.name : 'Neue Veranstaltung' }}
            </h3>
            <div v-if="eventError" class="text-xs text-red-600 bg-red-50 rounded px-2 py-1 mb-3">{{ eventError }}</div>
            <div class="space-y-3">
              <div>
                <label class="text-xs text-gray-500 font-semibold block mb-1">Name *</label>
                <input v-model="eventForm.name" type="text" placeholder="z.B. ADAC Kart-Slalom Kassel 2026" class="input font-semibold">
              </div>
              <div class="grid grid-cols-3 gap-3">
                <div>
                  <label class="text-xs text-gray-500 font-semibold block mb-1">Datum *</label>
                  <input v-model="eventForm.date" type="date" class="input">
                </div>
                <div>
                  <label class="text-xs text-gray-500 font-semibold block mb-1">Ort</label>
                  <input v-model="eventForm.location" type="text" class="input">
                </div>
                <div>
                  <label class="text-xs text-gray-500 font-semibold block mb-1">Status</label>
                  <select v-model="eventForm.status" class="input">
                    <option value="planned">Geplant</option>
                    <option value="active">Aktiv</option>
                    <option value="finished">Beendet</option>
                    <option value="official">Offiziell</option>
                  </select>
                </div>
              </div>
              <div>
                <label class="text-xs text-gray-500 font-semibold block mb-1">Beschreibung / Veranstaltungsinfo</label>
                <textarea v-model="eventForm.description" rows="3" class="input resize-none" placeholder="Programm, Hinweise für Teilnehmer, Treffpunkt…"></textarea>
              </div>
            </div>
            <div class="flex gap-2 mt-3">
              <button @click="saveEvent" :disabled="!eventForm.name || !eventForm.date"
                class="btn-primary px-4 py-2 text-sm disabled:opacity-40">
                {{ activeEvent ? 'Speichern' : 'Anlegen' }}
              </button>
              <button v-if="!activeEvent" @click="cancelNewEvent" class="btn-secondary px-4 py-2 text-sm">
                Abbrechen
              </button>
            </div>
          </div>

          <!-- Klassen-Konfiguration (nur für gespeicherte Veranstaltungen) -->
          <div v-if="activeEvent" class="card overflow-hidden">
            <div class="px-4 py-3 border-b border-gray-100 flex items-center justify-between">
              <h3 class="font-bold text-gray-800">Klassen</h3>
              <button @click="addClassRow" class="text-xs btn-primary px-3 py-1.5">+ Klasse</button>
            </div>
            <table class="w-full text-sm">
              <thead>
                <tr class="bg-gray-50 text-xs text-gray-500 uppercase tracking-wider border-b border-gray-200">
                  <th class="py-2 px-3 text-left">Reihenf.</th>
                  <th class="py-2 px-3 text-left">Name</th>
                  <th class="py-2 px-3 text-left">Kürzel</th>
                  <th class="py-2 px-3 text-left">Jg. von</th>
                  <th class="py-2 px-3 text-left">Jg. bis</th>
                  <th class="py-2 px-3 text-left">Reglement</th>
                  <th class="py-2 px-3 text-center" title="Vorstarter/Showklasse: Zeiteingabe ohne Klassenstart möglich">Vorstart.</th>
                  <th class="py-2 px-3 text-center">Status</th>
                  <th></th>
                </tr>
              </thead>
              <tbody class="divide-y divide-gray-100">
                <tr v-for="(cls, i) in classRows" :key="cls._key" class="hover:bg-gray-50">
                  <td class="py-2 px-3 text-gray-400 text-xs">{{ i + 1 }}</td>
                  <td class="py-2 px-3">
                    <input v-model="cls.name" type="text" class="border border-gray-200 rounded px-2 py-1 text-xs w-24 focus:outline-none focus:ring-1 focus:ring-msc-blue">
                  </td>
                  <td class="py-2 px-3">
                    <input v-model="cls.short_name" type="text" class="border border-gray-200 rounded px-2 py-1 text-xs w-12 focus:outline-none focus:ring-1 focus:ring-msc-blue">
                  </td>
                  <td class="py-2 px-3">
                    <input v-model.number="cls.min_birth_year" type="number" class="border border-gray-200 rounded px-2 py-1 text-xs w-16 font-mono focus:outline-none focus:ring-1 focus:ring-msc-blue">
                  </td>
                  <td class="py-2 px-3">
                    <input v-model.number="cls.max_birth_year" type="number" class="border border-gray-200 rounded px-2 py-1 text-xs w-16 font-mono focus:outline-none focus:ring-1 focus:ring-msc-blue">
                  </td>
                  <td class="py-2 px-3">
                    <select v-model.number="cls.reglement_id" class="border border-gray-200 rounded px-2 py-1 text-xs focus:outline-none focus:ring-1 focus:ring-msc-blue">
                      <option :value="null">–</option>
                      <option v-for="r in store.reglements" :key="r.id" :value="r.id">{{ r.name }}</option>
                    </select>
                  </td>
                  <td class="py-2 px-3 text-center">
                    <input type="checkbox" v-model="cls.is_exhibition"
                      class="h-4 w-4 rounded accent-msc-blue cursor-pointer"
                      title="Vorstarter/Showklasse: Zeiteingabe ohne Klassenstart erlaubt">
                  </td>
                  <td class="py-2 px-3 text-center">
                    <span :class="{
                      'badge-ok':   cls.run_status === 'official',
                      'badge-info': cls.run_status === 'running',
                      'badge-warn': cls.run_status === 'preliminary',
                      'badge-gray': cls.run_status === 'planned',
                    }" :style="cls.run_status === 'paused' ? 'background:#fed7aa;color:#c2410c;font-weight:700;border-radius:4px;padding:1px 6px;font-size:11px' : ''">
                      {{ cls.run_status === 'paused' ? 'Unterbrochen' : cls.run_status }}
                    </span>
                  </td>
                  <td class="py-2 px-2 text-center whitespace-nowrap">
                    <button v-if="cls.id && cls.run_status === 'running'"
                      @click="setClassStatus(cls, 'paused')"
                      class="text-orange-500 hover:text-orange-700 text-xs font-bold mr-1" title="Unterbrechen">⏸</button>
                    <button v-if="cls.id && cls.run_status === 'paused'"
                      @click="setClassStatus(cls, 'running')"
                      class="text-msc-blue hover:text-msc-bluedark text-xs font-bold mr-1" title="Fortsetzen">▶</button>
                    <button @click="classRows.splice(i,1)" class="text-gray-300 hover:text-msc-red text-xs">✕</button>
                  </td>
                </tr>
              </tbody>
            </table>
            <div class="px-4 py-2 border-t border-gray-100 flex justify-end">
              <button @click="saveClasses" class="btn-primary px-4 py-2 text-sm">Klassen speichern</button>
            </div>
          </div>
        </div>
      </div>

      <!-- ═══ VEREINE ═══ -->
      <div v-if="activeTab === 'clubs'" class="grid grid-cols-2 gap-4">
        <div class="card overflow-hidden">
          <div class="px-4 py-3 border-b border-gray-100 flex items-center justify-between">
            <h3 class="font-bold text-gray-800">Vereine <span class="text-gray-400 font-normal text-sm">({{ store.clubs.length }})</span></h3>
            <button @click="openNewClub" class="text-xs btn-primary px-3 py-1.5">+ Verein</button>
          </div>
          <table class="w-full text-sm">
            <thead>
              <tr class="bg-gray-50 text-xs text-gray-500 uppercase tracking-wider border-b border-gray-200">
                <th class="py-2 px-3 text-left">Name</th>
                <th class="py-2 px-3 text-left">Kürzel</th>
                <th class="py-2 px-3 text-left">Ort</th>
                <th></th>
              </tr>
            </thead>
            <tbody class="divide-y divide-gray-100">
              <tr
                v-for="c in store.clubs"
                :key="c.id"
                @click="selectClub(c)"
                class="hover:bg-blue-50 transition cursor-pointer"
                :class="{ 'bg-blue-50': selectedClub?.id === c.id }"
              >
                <td class="py-2.5 px-3 font-semibold text-gray-800">{{ c.name }}</td>
                <td class="py-2.5 px-3 text-gray-500">{{ c.short_name || '–' }}</td>
                <td class="py-2.5 px-3 text-gray-500">{{ c.city || '–' }}</td>
                <td class="py-2 px-2">
                  <button @click.stop="deleteClub(c)" class="text-gray-300 hover:text-msc-red text-xs">✕</button>
                </td>
              </tr>
              <tr v-if="!store.clubs.length">
                <td colspan="4" class="py-4 text-center text-sm text-gray-400">Noch keine Vereine angelegt</td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Verein-Formular -->
        <div v-if="clubForm" class="card p-4 space-y-3 self-start">
          <h3 class="font-bold text-gray-800">{{ selectedClub ? 'Verein bearbeiten' : 'Neuer Verein' }}</h3>
          <div>
            <label class="text-xs text-gray-500 font-semibold block mb-1">Vollständiger Name</label>
            <input v-model="clubForm.name" type="text" placeholder="MSC Braach e.V. im ADAC" class="input">
          </div>
          <div>
            <label class="text-xs text-gray-500 font-semibold block mb-1">Kurzname (für Listen)</label>
            <input v-model="clubForm.short_name" type="text" placeholder="MSC Braach" class="input">
          </div>
          <div>
            <label class="text-xs text-gray-500 font-semibold block mb-1">Ort</label>
            <input v-model="clubForm.city" type="text" placeholder="Braach" class="input">
          </div>
          <div v-if="clubError" class="text-xs text-red-600 bg-red-50 rounded px-2 py-1">{{ clubError }}</div>
          <div class="flex gap-2">
            <button @click="saveClub" class="flex-1 btn-primary py-2">Speichern</button>
            <button @click="cancelClub" class="btn-secondary py-2 px-3 text-sm">Abbrechen</button>
          </div>
        </div>
      </div>

      <!-- ═══ SPONSOREN ═══ -->
      <div v-if="activeTab === 'sponsors'" class="grid grid-cols-2 gap-4">
        <div class="card overflow-hidden">
          <div class="px-4 py-3 border-b border-gray-100 flex items-center justify-between">
            <h3 class="font-bold text-gray-800">Sponsoren <span class="text-gray-400 font-normal text-sm">({{ sponsors.length }})</span></h3>
            <button @click="openNewSponsor" class="text-xs btn-primary px-3 py-1.5">+ Sponsor</button>
          </div>
          <table class="w-full text-sm">
            <thead>
              <tr class="bg-gray-50 text-xs text-gray-500 uppercase tracking-wider border-b border-gray-200">
                <th class="py-2 px-3 text-left">Name</th>
                <th class="py-2 px-3 text-center">Reihenf.</th>
                <th class="py-2 px-3 text-center">Aktiv</th>
                <th></th>
              </tr>
            </thead>
            <tbody class="divide-y divide-gray-100">
              <tr
                v-for="s in sponsors" :key="s.id"
                @click="selectSponsor(s)"
                class="hover:bg-blue-50 transition cursor-pointer"
                :class="{ 'bg-blue-50': selectedSponsor?.id === s.id }"
              >
                <td class="py-2.5 px-3">
                  <div class="flex items-center gap-2">
                    <img v-if="s.logo_url" :src="s.logo_url" class="h-7 w-14 object-contain rounded" :alt="s.name">
                    <div>
                      <div class="font-semibold text-gray-800">{{ s.name }}</div>
                      <div v-if="s.website_url" class="text-xs text-gray-400 truncate max-w-48">{{ s.website_url }}</div>
                    </div>
                  </div>
                </td>
                <td class="py-2.5 px-3 text-center text-gray-500">{{ s.sort_order }}</td>
                <td class="py-2.5 px-3 text-center">
                  <span :class="s.is_active ? 'badge-ok' : 'badge-gray'">{{ s.is_active ? '✓' : '✗' }}</span>
                </td>
                <td class="py-2 px-2">
                  <button @click.stop="deleteSponsor(s)" class="text-gray-300 hover:text-msc-red text-xs">✕</button>
                </td>
              </tr>
              <tr v-if="!sponsors.length">
                <td colspan="4" class="py-4 text-center text-sm text-gray-400">Noch keine Sponsoren angelegt</td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Sponsor-Formular -->
        <div v-if="sponsorForm" class="card p-4 space-y-3 self-start">
          <h3 class="font-bold text-gray-800">{{ selectedSponsor ? 'Sponsor bearbeiten' : 'Neuer Sponsor' }}</h3>
          <div>
            <label class="text-xs text-gray-500 font-semibold block mb-1">Name *</label>
            <input v-model="sponsorForm.name" type="text" placeholder="ACME GmbH" class="input">
          </div>
          <div>
            <label class="text-xs text-gray-500 font-semibold block mb-1">Logo-URL</label>
            <input v-model="sponsorForm.logo_url" type="url" placeholder="https://..." class="input font-mono text-xs">
          </div>
          <div v-if="sponsorForm.logo_url" class="flex justify-center py-1">
            <img :src="sponsorForm.logo_url" class="h-16 object-contain border border-gray-200 rounded p-2" alt="Logo-Vorschau">
          </div>
          <div>
            <label class="text-xs text-gray-500 font-semibold block mb-1">Website</label>
            <input v-model="sponsorForm.website_url" type="url" placeholder="https://..." class="input font-mono text-xs">
          </div>
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="text-xs text-gray-500 font-semibold block mb-1">Reihenfolge</label>
              <input v-model.number="sponsorForm.sort_order" type="number" class="input">
            </div>
            <div class="flex flex-col">
              <label class="text-xs text-gray-500 font-semibold block mb-1">Aktiv</label>
              <button @click="sponsorForm.is_active = !sponsorForm.is_active"
                :class="sponsorForm.is_active ? 'bg-green-500 text-white' : 'bg-gray-200 text-gray-600'"
                class="flex-1 rounded-lg text-sm font-semibold transition px-2">
                {{ sponsorForm.is_active ? 'Aktiv' : 'Inaktiv' }}
              </button>
            </div>
          </div>
          <div v-if="sponsorError" class="text-xs text-red-600 bg-red-50 rounded px-2 py-1">{{ sponsorError }}</div>
          <div class="flex gap-2">
            <button @click="saveSponsor" :disabled="!sponsorForm.name" class="flex-1 btn-primary py-2 disabled:opacity-40">Speichern</button>
            <button @click="cancelSponsor" class="btn-secondary py-2 px-3 text-sm">Abbrechen</button>
          </div>
        </div>
      </div>

      <!-- ═══ BENUTZER ═══ -->
      <div v-if="activeTab === 'users'" class="grid grid-cols-2 gap-4">
        <div class="card overflow-hidden">
          <div class="px-4 py-3 border-b border-gray-100 flex items-center justify-between">
            <h3 class="font-bold text-gray-800">Benutzer</h3>
            <button @click="openNewUser" class="text-xs btn-primary px-3 py-1.5">+ Benutzer</button>
          </div>
          <table class="w-full text-sm">
            <thead>
              <tr class="bg-gray-50 text-xs text-gray-500 uppercase tracking-wider border-b">
                <th class="py-2 px-3 text-left">Benutzername</th>
                <th class="py-2 px-3 text-left">Anzeigename</th>
                <th class="py-2 px-3 text-left">Rolle</th>
                <th class="py-2 px-3 text-center">Aktiv</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-gray-100">
              <tr v-for="u in users" :key="u.id" class="hover:bg-gray-50">
                <td class="py-2.5 px-3 font-mono text-sm text-gray-800">{{ u.username }}</td>
                <td class="py-2.5 px-3 text-gray-600">{{ u.display_name || '–' }}</td>
                <td class="py-2.5 px-3">
                  <span class="badge-info">{{ u.role }}</span>
                </td>
                <td class="py-2.5 px-3 text-center">
                  <span :class="u.is_active ? 'badge-ok' : 'badge-gray'">
                    {{ u.is_active ? '✓' : '✗' }}
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <div v-if="userForm" class="card p-4 space-y-3 self-start">
          <h3 class="font-bold text-gray-800">Neuer Benutzer</h3>
          <div>
            <label class="text-xs text-gray-500 font-semibold block mb-1">Benutzername</label>
            <input v-model="userForm.username" type="text" class="input font-mono">
          </div>
          <div>
            <label class="text-xs text-gray-500 font-semibold block mb-1">Passwort</label>
            <input v-model="userForm.password" type="password" class="input">
          </div>
          <div>
            <label class="text-xs text-gray-500 font-semibold block mb-1">Rolle</label>
            <select v-model="userForm.role" class="input">
              <option value="zeitnahme">Zeitnahme</option>
              <option value="nennung">Nennung</option>
              <option value="schiedsrichter">Schiedsrichter</option>
              <option value="viewer">Viewer</option>
              <option value="admin">Admin</option>
            </select>
          </div>
          <div>
            <label class="text-xs text-gray-500 font-semibold block mb-1">Anzeigename</label>
            <input v-model="userForm.display_name" type="text" class="input">
          </div>
          <div class="flex gap-2">
            <button @click="saveUser" class="flex-1 btn-primary py-2">Anlegen</button>
            <button @click="userForm = null" class="btn-secondary py-2 px-3 text-sm">Abbrechen</button>
          </div>
        </div>
      </div>

      <!-- ═══ SYSTEM ═══ -->
      <div v-if="activeTab === 'system'" class="grid grid-cols-2 gap-4">

        <!-- Veranstalter / Druckvorlage -->
        <div class="card p-4 space-y-4">
          <h3 class="font-bold text-gray-800">Druckvorlage – Nennliste</h3>
          <p class="text-xs text-gray-500">
            Diese Texte erscheinen auf jeder gedruckten Nennliste (Versicherungshinweis, Einverständniserklärung für Eltern).
          </p>
          <div class="space-y-3">
            <div>
              <label class="text-xs text-gray-500 font-semibold block mb-1">Veranstalter</label>
              <input v-model="sysForm.organizer_name" type="text" class="input" placeholder="MSC Braach e.V. im ADAC">
            </div>
            <div>
              <label class="text-xs text-gray-500 font-semibold block mb-1">Adresse</label>
              <input v-model="sysForm.organizer_address" type="text" class="input" placeholder="Musterstraße 1, 12345 Braach">
            </div>
            <div>
              <label class="text-xs text-gray-500 font-semibold block mb-1">Versicherungshinweis</label>
              <textarea v-model="sysForm.insurance_notice" rows="4" class="input resize-none text-xs"
                placeholder="Alle Teilnehmer sind über den ADAC-Motorsport versichert…"></textarea>
            </div>
            <div>
              <label class="text-xs text-gray-500 font-semibold block mb-1">Einverständniserklärung (Eltern/Erziehungsberechtigte)</label>
              <textarea v-model="sysForm.parent_consent_text" rows="3" class="input resize-none text-xs"
                placeholder="Ich bin mit der Teilnahme meines Kindes einverstanden…"></textarea>
            </div>
          </div>
          <div v-if="sysMessage" class="text-xs rounded px-2 py-1.5"
               :class="sysMessage.type === 'ok' ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-600'">
            {{ sysMessage.text }}
          </div>
          <button @click="saveSettings" class="btn-primary px-4 py-2 text-sm">Einstellungen speichern</button>
        </div>

        <!-- Drucker-Info -->
        <div class="card p-4 space-y-3 self-start">
          <h3 class="font-bold text-gray-800">Drucker</h3>
          <p class="text-xs text-gray-500">
            Der Druck erfolgt über den Browser. Klicke im Nennbüro auf <strong>🖨 Nennliste drucken</strong> –
            es öffnet sich ein Druckdialog, in dem du den gewünschten Drucker auswählen kannst.
          </p>
          <div class="rounded-xl bg-blue-50 border border-blue-200 px-3 py-2.5 text-xs text-blue-700 space-y-1">
            <div class="font-bold">Empfohlene Druckeinstellungen</div>
            <div>• Format: A4 Hochformat</div>
            <div>• Ränder: Schmal (12–15 mm)</div>
            <div>• Kopf- & Fußzeilen: Deaktivieren</div>
            <div>• Hintergrundfarben: Aktivieren (für grau hinterlegte Spaltenköpfe)</div>
          </div>
          <div class="rounded-xl bg-gray-50 border border-gray-200 px-3 py-2.5 text-xs text-gray-600 space-y-1">
            <div class="font-bold">Hinweis Elternunterschrift</div>
            <div>
              Die Nennliste enthält eine Unterschriftenspalte.
              Bei minderjährigen Fahrern muss ein Erziehungsberechtigter unterschreiben.
              Die unterzeichnete Liste ist als Veranstaltungsunterlage aufzubewahren.
            </div>
          </div>
        </div>

      </div>

      <!-- ═══ TEST ═══ -->
      <div v-if="activeTab === 'test'" class="space-y-4 max-w-2xl">

        <!-- API Health Check -->
        <div class="card p-4">
          <h3 class="font-bold text-gray-800 mb-1">API Verbindungstest</h3>
          <p class="text-xs text-gray-500 mb-3">
            Prüft ob das Backend erreichbar ist und das JWT-Token noch gültig ist.
          </p>
          <div class="flex items-center gap-3">
            <button @click="runApiCheck" :disabled="apiCheckRunning"
                    class="btn-primary px-4 py-2 text-sm disabled:opacity-40">
              {{ apiCheckRunning ? 'Prüfe…' : 'Verbindung prüfen' }}
            </button>
            <span v-if="apiCheckResult !== null" class="text-sm font-semibold flex items-center gap-1.5"
                  :class="apiCheckResult ? 'text-green-600' : 'text-red-600'">
              <span class="h-2 w-2 rounded-full" :class="apiCheckResult ? 'bg-green-500' : 'bg-red-500'"></span>
              {{ apiCheckResult ? 'Backend erreichbar' : 'Verbindung fehlgeschlagen' }}
            </span>
          </div>
        </div>

        <!-- Reglements-Vorlagen -->
        <div class="card p-4">
          <h3 class="font-bold text-gray-800 mb-1">Reglements-Vorlagen</h3>
          <p class="text-xs text-gray-500 mb-3">
            Legt vordefinierte Reglements mit den offiziellen Straf-Definitionen an.
            Bereits vorhandene Reglements gleichen Namens werden übersprungen.
          </p>
          <div class="flex flex-wrap gap-2 mb-3">
            <button @click="seedKs2000" :disabled="ks2000Running"
                    class="btn-primary px-4 py-2 text-sm disabled:opacity-40">
              {{ ks2000Running ? 'Läuft…' : 'KS 2000 anlegen' }}
            </button>
          </div>
          <div v-if="ks2000Log.length"
               class="bg-gray-900 text-gray-100 font-mono text-xs rounded-lg p-3 max-h-40 overflow-y-auto space-y-0.5">
            <div v-for="(entry, i) in ks2000Log" :key="i" class="flex items-start gap-2 leading-relaxed">
              <span class="shrink-0 w-3"
                    :class="{
                      'text-green-400':  entry.status === 'ok',
                      'text-red-400':    entry.status === 'err',
                      'text-yellow-300': entry.status === 'running',
                    }">
                {{ entry.status === 'ok' ? '✓' : entry.status === 'err' ? '✗' : '›' }}
              </span>
              <span>{{ entry.label }}</span>
            </div>
          </div>
        </div>

        <!-- Testdaten -->
        <div class="card p-4">
          <h3 class="font-bold text-gray-800 mb-1">Testdaten</h3>
          <p class="text-xs text-gray-500 mb-3">
            Legt ein vollständiges Testszenario an: Reglement <em>JKS Demo</em> mit Strafen,
            eine Veranstaltung mit 3 Klassen (Schüler A · Junioren · Senioren) und 6 Teilnehmern.
          </p>
          <div class="flex flex-wrap gap-2 mb-3">
            <button @click="seedTestData" :disabled="seedRunning"
                    class="btn-primary px-4 py-2 text-sm disabled:opacity-40">
              {{ seedRunning ? 'Läuft…' : 'Testumgebung anlegen' }}
            </button>
            <button @click="deleteTestData" :disabled="seedRunning"
                    class="btn-secondary px-4 py-2 text-sm disabled:opacity-40">
              Testdaten entfernen
            </button>
            <button v-if="seedLog.length" @click="seedLog = []"
                    class="text-xs text-gray-400 hover:text-gray-600 px-2 py-1">
              Log löschen
            </button>
          </div>

          <!-- Progress-Log -->
          <div v-if="seedLog.length"
               class="bg-gray-900 text-gray-100 font-mono text-xs rounded-lg p-3 max-h-56 overflow-y-auto space-y-0.5">
            <div v-for="(entry, i) in seedLog" :key="i" class="flex items-start gap-2 leading-relaxed">
              <span class="shrink-0 w-3"
                    :class="{
                      'text-green-400':  entry.status === 'ok',
                      'text-red-400':    entry.status === 'err',
                      'text-yellow-300': entry.status === 'running',
                    }">
                {{ entry.status === 'ok' ? '✓' : entry.status === 'err' ? '✗' : '›' }}
              </span>
              <span>{{ entry.label }}</span>
            </div>
          </div>
        </div>

      </div>

    </section>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '../api/client'
import { useEventStore } from '../stores/event'

const store = useEventStore()

const activeTab  = ref('events')
const tabs = [
  { id: 'events',   label: '📅 Veranstaltungen' },
  { id: 'clubs',    label: '🏁 Vereine' },
  { id: 'users',    label: '👥 Benutzer' },
  { id: 'sponsors', label: '🤝 Sponsoren' },
  { id: 'system',   label: '⚙️ System' },
  { id: 'test',     label: '🧪 Test' },
]

// ── Events ──
const events        = ref([])
const activeEvent   = ref(null)
const showEventForm = ref(false)
const eventForm     = ref({})
const eventError    = ref('')
const classRows     = ref([])

async function loadEvents() {
  const { data } = await api.get('/events/')
  events.value = data
}

function selectEvent(e) {
  activeEvent.value = e
  showEventForm.value = true
  eventForm.value = { ...e }
  eventError.value = ''
  classRows.value = (store.classes.filter(c => c.event_id === e.id)).map(c => ({ ...c, _key: c.id }))
}

function openNewEvent() {
  activeEvent.value = null
  showEventForm.value = true
  eventForm.value = { name: '', date: '', location: '', status: 'planned', description: '' }
  eventError.value = ''
  classRows.value = []
}

function cancelNewEvent() {
  showEventForm.value = false
  activeEvent.value = null
}

async function deleteEvent(e) {
  if (!confirm(`Veranstaltung "${e.name}" wirklich löschen?\n\nAlle Klassen, Teilnehmer und Ergebnisse werden unwiderruflich gelöscht.`)) return
  await api.delete(`/events/${e.id}`)
  if (activeEvent.value?.id === e.id) cancelNewEvent()
  await loadEvents()
  await store.loadEvents()
}

async function saveEvent() {
  eventError.value = ''
  try {
    if (activeEvent.value?.id) {
      await api.patch(`/events/${activeEvent.value.id}`, eventForm.value)
    } else {
      const { data } = await api.post('/events/', eventForm.value)
      await store.loadEvents()
      activeEvent.value = data
      eventForm.value = { ...data }
    }
    await loadEvents()
  } catch (e) {
    eventError.value = e.response?.data?.detail || 'Fehler beim Speichern'
  }
}

function addClassRow() {
  classRows.value.push({
    _key: Date.now(), name: '', short_name: '', min_birth_year: null,
    max_birth_year: null, reglement_id: null, run_status: 'planned', start_order: classRows.value.length,
    is_exhibition: false
  })
}

async function setClassStatus(cls, status) {
  if (!activeEvent.value) return
  await api.patch(`/events/${activeEvent.value.id}/classes/${cls.id}`, { run_status: status })
  await store.selectEvent(activeEvent.value)
  cls.run_status = status
}

async function saveClasses() {
  if (!activeEvent.value) return
  await store.selectEvent(activeEvent.value)
  const existing = store.classes.filter(c => c.event_id === activeEvent.value.id)
  for (const [i, row] of classRows.value.entries()) {
    const payload = { ...row, event_id: activeEvent.value.id, start_order: i }
    if (row.id) {
      await api.patch(`/events/${activeEvent.value.id}/classes/${row.id}`, payload)
    } else {
      await api.post(`/events/${activeEvent.value.id}/classes`, payload)
    }
  }
  await store.selectEvent(activeEvent.value)
}

// ── Clubs ──
const selectedClub = ref(null)
const clubForm     = ref(null)
const clubError    = ref('')

function selectClub(c) { selectedClub.value = c; clubForm.value = { ...c }; clubError.value = '' }
function openNewClub() { selectedClub.value = null; clubForm.value = { name: '', short_name: '', city: '' }; clubError.value = '' }
function cancelClub() { selectedClub.value = null; clubForm.value = null }

async function saveClub() {
  clubError.value = ''
  try {
    if (selectedClub.value) {
      await api.patch(`/clubs/${selectedClub.value.id}`, clubForm.value)
    } else {
      await api.post('/clubs/', clubForm.value)
    }
    await store.loadClubs()
    cancelClub()
  } catch (e) {
    clubError.value = e.response?.data?.detail || 'Fehler'
  }
}

async function deleteClub(c) {
  if (!confirm(`Verein "${c.name}" löschen?`)) return
  await api.delete(`/clubs/${c.id}`)
  await store.loadClubs()
}

// ── Sponsors ──
const sponsors        = ref([])
const selectedSponsor = ref(null)
const sponsorForm     = ref(null)
const sponsorError    = ref('')

async function loadSponsors() {
  const { data } = await api.get('/sponsors/')
  sponsors.value = data
}

function selectSponsor(s) {
  selectedSponsor.value = s
  sponsorForm.value = { ...s }
  sponsorError.value = ''
}

function openNewSponsor() {
  selectedSponsor.value = null
  sponsorForm.value = { name: '', logo_url: '', website_url: '', sort_order: 0, is_active: true }
  sponsorError.value = ''
}

function cancelSponsor() {
  selectedSponsor.value = null
  sponsorForm.value = null
}

async function saveSponsor() {
  sponsorError.value = ''
  try {
    if (selectedSponsor.value) {
      await api.patch(`/sponsors/${selectedSponsor.value.id}`, sponsorForm.value)
    } else {
      await api.post('/sponsors/', sponsorForm.value)
    }
    await loadSponsors()
    cancelSponsor()
  } catch (e) {
    sponsorError.value = e.response?.data?.detail || 'Fehler beim Speichern'
  }
}

async function deleteSponsor(s) {
  if (!confirm(`Sponsor "${s.name}" löschen?`)) return
  await api.delete(`/sponsors/${s.id}`)
  await loadSponsors()
  if (selectedSponsor.value?.id === s.id) cancelSponsor()
}

// ── Users ──
const users    = ref([])
const userForm = ref(null)

async function loadUsers() {
  const { data } = await api.get('/users/')
  users.value = data
}

function openNewUser() {
  userForm.value = { username: '', password: '', role: 'zeitnahme', display_name: '' }
}

async function saveUser() {
  await api.post('/users/', userForm.value)
  await loadUsers()
  userForm.value = null
}

// ── System / Settings ──
const sysForm    = ref({ organizer_name: '', organizer_address: '', insurance_notice: '', parent_consent_text: '' })
const sysMessage = ref(null)

async function loadSettings() {
  const { data } = await api.get('/settings/')
  sysForm.value = { ...sysForm.value, ...data }
}

async function saveSettings() {
  sysMessage.value = null
  try {
    await api.patch('/settings/', sysForm.value)
    sysMessage.value = { type: 'ok', text: 'Einstellungen gespeichert.' }
    setTimeout(() => { sysMessage.value = null }, 3000)
  } catch (e) {
    sysMessage.value = { type: 'err', text: e.response?.data?.detail || 'Fehler beim Speichern' }
  }
}

onMounted(async () => {
  await Promise.all([loadEvents(), store.loadReglements(), store.loadClubs(), loadUsers(), loadSponsors(), loadSettings()])
})

// ── Test ──────────────────────────────────────────────────────────────────────

const ks2000Running = ref(false)
const ks2000Log     = ref([])

async function seedKs2000() {
  ks2000Running.value = true
  ks2000Log.value = []
  const _l = (label, status = 'running') => ks2000Log.value.push({ label, status })
  const _u = (status, label) => {
    const last = ks2000Log.value[ks2000Log.value.length - 1]
    if (last) { last.status = status; if (label) last.label = label }
  }
  try {
    _l('Reglement "KS 2000" prüfen / anlegen…')
    let reg = (await api.get('/reglements/')).data.find(r => r.name === 'KS 2000')
    if (!reg) {
      reg = (await api.post('/reglements/', {
        name: 'KS 2000', scoring_type: 'sum_all', runs_per_class: 2, has_training: true,
      })).data
      _u('ok', `Reglement "KS 2000" angelegt (ID ${reg.id})`)
    } else {
      _u('ok', `Reglement "KS 2000" bereits vorhanden (ID ${reg.id})`)
    }

    _l('Straf-Definitionen anlegen…')
    const penalties = [
      { label: 'Pylone umwerfen/verschieben',                        seconds:  3, shortcut_key: 'P', sort_order: 0 },
      { label: 'Pylonentore/Schweizer auslassen',                    seconds: 10, shortcut_key: 'T', sort_order: 1 },
      { label: 'Gasse auslassen',                                    seconds: 15, shortcut_key: 'G', sort_order: 2 },
      { label: 'Begrenzungslinie überschreiten/Klötzchen verschieben', seconds:  3, shortcut_key: 'L', sort_order: 3 },
      { label: 'Fahrtrichtung nicht eingehalten nach Zieldurchfahrt', seconds: 10, shortcut_key: null, sort_order: 4 },
      { label: 'Unkorrektes Verhalten gg. Veranstalter/Funktionäre', seconds: 20, shortcut_key: null, sort_order: 5 },
    ]
    let added = 0
    for (const p of penalties) {
      try { await api.post(`/reglements/${reg.id}/penalties`, p); added++ } catch { /* skip duplicates */ }
    }
    _u('ok', `${added} Straf-Definitionen angelegt`)
    ks2000Log.value.push({ status: 'ok', label: 'KS 2000 fertig.' })
    await store.loadReglements()
  } catch (e) {
    _u('err', e.response?.data?.detail || e.message || 'Fehler')
  } finally {
    ks2000Running.value = false
  }
}

const apiCheckRunning = ref(false)
const apiCheckResult  = ref(null)
const seedRunning     = ref(false)
const seedLog         = ref([])

async function runApiCheck() {
  apiCheckRunning.value = true
  apiCheckResult.value  = null
  try {
    await api.get('/events/')
    apiCheckResult.value = true
  } catch {
    apiCheckResult.value = false
  } finally {
    apiCheckRunning.value = false
  }
}

function _log(label, status = 'running') {
  seedLog.value.push({ label, status })
}

function _updateLast(status, label) {
  const last = seedLog.value[seedLog.value.length - 1]
  if (last) { last.status = status; if (label) last.label = label }
}

async function seedTestData() {
  seedRunning.value = true
  seedLog.value = []
  try {
    // 1. Reglement
    _log('Reglement "JKS Demo" anlegen…')
    let reg
    try {
      reg = (await api.post('/reglements/', {
        name: 'JKS Demo', scoring_type: 'sum_all', runs_per_class: 2, has_training: true,
      })).data
    } catch {
      reg = (await api.get('/reglements/')).data.find(r => r.name === 'JKS Demo')
      if (!reg) { _updateLast('err', 'Reglement konnte nicht angelegt werden'); return }
    }
    _updateLast('ok', `Reglement "${reg.name}" (ID ${reg.id})`)

    // 2. Strafen
    _log('Strafen anlegen (Pylone 5 s · Torfehler 10 s · Ausbruch 20 s)…')
    const penalties = [
      { label: 'Pylone',    seconds: 5,  shortcut_key: 'P', sort_order: 0 },
      { label: 'Torfehler', seconds: 10, shortcut_key: 'T', sort_order: 1 },
      { label: 'Ausbruch',  seconds: 20, shortcut_key: 'A', sort_order: 2 },
    ]
    for (const p of penalties) {
      await api.post(`/reglements/${reg.id}/penalties`, p).catch(() => {})
    }
    _updateLast('ok', '3 Strafen angelegt')

    // 3. Veranstaltung
    const today = new Date().toISOString().slice(0, 10)
    const year  = new Date().getFullYear()
    _log(`Veranstaltung "Testlauf ${year}" anlegen…`)
    const event = (await api.post('/events/', {
      name: `Testlauf ${year}`, date: today,
      location: 'Testgelände', reglement_id: reg.id, status: 'active',
    })).data
    _updateLast('ok', `Veranstaltung ID ${event.id} angelegt (${today})`)

    // 4. Klassen
    const classDefs = [
      { name: 'Schüler A', short_name: 'SA',  min_birth_year: 2015, max_birth_year: 2018, start_order: 0 },
      { name: 'Junioren',  short_name: 'JUN', min_birth_year: 2010, max_birth_year: 2014, start_order: 1 },
      { name: 'Senioren',  short_name: 'SEN', min_birth_year: null,  max_birth_year: 2009, start_order: 2 },
    ]
    const created = []
    for (const def of classDefs) {
      _log(`Klasse "${def.name}" anlegen…`)
      const c = (await api.post(`/events/${event.id}/classes`, {
        ...def, reglement_id: reg.id, run_status: 'planned',
      })).data
      created.push(c)
      _updateLast('ok', `Klasse "${c.name}" (ID ${c.id})`)
    }

    // 5. Teilnehmer
    const pDefs = [
      { first_name: 'Tim',   last_name: 'Fischer', birth_year: 2016, start_number: 1, ci: 0 },
      { first_name: 'Lena',  last_name: 'Braun',   birth_year: 2017, start_number: 2, ci: 0 },
      { first_name: 'Jonas', last_name: 'Weber',   birth_year: 2012, start_number: 3, ci: 1 },
      { first_name: 'Anna',  last_name: 'Koch',    birth_year: 2013, start_number: 4, ci: 1 },
      { first_name: 'Max',   last_name: 'Schulz',  birth_year: 2006, start_number: 5, ci: 2 },
      { first_name: 'Petra', last_name: 'Mayer',   birth_year: 2005, start_number: 6, ci: 2 },
    ]
    _log('6 Testteilnehmer anlegen…')
    for (const p of pDefs) {
      await api.post(`/events/${event.id}/participants`, {
        first_name: p.first_name, last_name: p.last_name,
        birth_year: p.birth_year, start_number: p.start_number,
        class_id: created[p.ci].id,
      })
    }
    _updateLast('ok', '6 Testteilnehmer angelegt')

    _log('Testumgebung vollständig angelegt.', 'ok')
    await loadEvents()
    await store.loadEvents()
  } catch (e) {
    _updateLast('err', e.response?.data?.detail || e.message || 'Unbekannter Fehler')
  } finally {
    seedRunning.value = false
  }
}

async function deleteTestData() {
  const year = new Date().getFullYear()
  const name = `Testlauf ${year}`
  const evt  = events.value.find(e => e.name === name)
  if (!evt) {
    seedLog.value = [{ status: 'err', label: `Keine Veranstaltung "${name}" gefunden.` }]
    return
  }
  if (!confirm(`Testveranstaltung "${evt.name}" und alle zugehörigen Daten löschen?`)) return
  await api.delete(`/events/${evt.id}`)
  seedLog.value = [{ status: 'ok', label: `"${evt.name}" gelöscht.` }]
  await loadEvents()
  await store.loadEvents()
}

function eventBadge(s) {
  return { planned: 'bg-gray-100 text-gray-500', active: 'bg-green-100 text-green-700',
           finished: 'bg-blue-100 text-blue-700', official: 'bg-green-100 text-green-700' }[s] || ''
}
</script>
