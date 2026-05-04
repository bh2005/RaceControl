<template>

  <!-- ══════════ DOWNHILL-MODUS ══════════ -->
  <div v-if="isDownhill" class="max-w-7xl mx-auto px-4 py-4 pb-12 space-y-4">

    <!-- Titelleiste: Uhr + Verbindung -->
    <div class="flex items-center gap-4 flex-wrap">
      <div class="card px-5 py-3 flex items-center gap-4 flex-1 min-w-[200px]">
        <div class="font-mono text-4xl font-black text-msc-blue tabnum select-none">{{ dhClock }}</div>
        <div class="text-xs text-gray-400 leading-tight">
          <div class="font-semibold text-gray-600">Downhill-Modus</div>
          <div>{{ store.activeEvent?.name || '–' }}</div>
        </div>
      </div>
      <div class="flex items-center gap-2 text-xs">
        <span class="h-2.5 w-2.5 rounded-full shrink-0 transition-colors duration-500"
              :class="lsConnected ? 'bg-green-500' : 'bg-gray-300'"></span>
        <span :class="lsConnected ? 'text-green-700 font-semibold' : 'text-gray-400'">
          {{ lsConnected ? 'Zielkamera verbunden' : 'Zielkamera nicht verbunden' }}
        </span>
      </div>
    </div>

    <!-- Flash: Zieldurchfahrt -->
    <Transition name="fade">
      <div v-if="dhFinishFlash"
        class="rounded-xl px-4 py-3 flex items-center gap-3 text-sm font-semibold bg-green-100 text-green-800 border border-green-300">
        <span class="text-xl">⚡</span> Zieldurchfahrt registriert
      </div>
    </Transition>

    <div class="grid grid-cols-1 lg:grid-cols-12 gap-4">

      <!-- ── LINKS: Nächster Starter + Upcoming ── -->
      <aside class="col-span-full lg:col-span-4 space-y-3">
        <h2 class="text-xs font-bold uppercase tracking-widest text-gray-500 px-1">Nächster Starter</h2>

        <div v-if="dhNext" class="bg-msc-blue text-white rounded-xl p-4 shadow-md space-y-3">
          <div class="flex items-start justify-between">
            <span class="text-5xl font-black leading-none">#{{ dhNext.start_number }}</span>
            <div class="text-right">
              <div class="text-blue-200 text-xs mb-0.5">Startzeit</div>
              <div class="font-mono text-xl font-black">{{ dhNext.scheduled_start?.slice(11, 19) }}</div>
            </div>
          </div>
          <div class="font-bold text-xl leading-tight">{{ dhNext.first_name }} {{ dhNext.last_name }}</div>

          <div class="bg-white/10 rounded-lg p-3 text-center">
            <div class="text-blue-200 text-xs uppercase tracking-wider mb-1">Start in</div>
            <div class="font-mono font-black leading-none"
                 :class="[
                   dhCountdownSec !== null && dhCountdownSec <= 0
                     ? 'text-4xl text-green-300 animate-pulse'
                     : dhCountdownSec !== null && dhCountdownSec <= 10
                       ? 'text-4xl text-yellow-300 animate-pulse'
                       : 'text-3xl text-white'
                 ]">
              {{ dhCountdownSec !== null && dhCountdownSec <= 0 ? '🚦 START!' : (dhCountdown || '–') }}
            </div>
          </div>
        </div>
        <div v-else class="bg-gray-100 rounded-xl p-6 text-center text-gray-400 text-sm">
          {{ dhSchedule.length ? 'Alle Starter abgeschlossen ✓' : 'Keine Starterliste vorhanden' }}
        </div>

        <h3 class="text-xs font-bold uppercase tracking-widest text-gray-500 px-1">Weitere Starter</h3>
        <div v-for="s in dhUpcoming.slice(1, 6)" :key="s.id"
             class="bg-white rounded-lg px-3 py-2 flex items-center gap-3 shadow-sm border border-gray-100">
          <span class="text-2xl font-black text-gray-700 w-10 shrink-0">#{{ s.start_number }}</span>
          <div class="flex-1 min-w-0">
            <div class="font-semibold text-sm text-gray-800 truncate">{{ s.first_name }} {{ s.last_name }}</div>
          </div>
          <div class="font-mono text-xs text-gray-500 shrink-0">{{ s.scheduled_start?.slice(11, 16) }}</div>
        </div>
        <div v-if="dhUpcoming.length === 0 && dhSchedule.length > 0" class="text-xs text-gray-400 text-center py-2">
          Alle Fahrer abgeschlossen
        </div>
      </aside>

      <!-- ── MITTE: Ergebnisse ── -->
      <section class="col-span-full lg:col-span-4 space-y-3">
        <div class="flex items-center justify-between px-1">
          <h2 class="text-xs font-bold uppercase tracking-widest text-gray-500">Zieldurchfahrten</h2>
          <span class="text-xs text-gray-400">{{ dhFinishResults.length }}</span>
        </div>
        <div class="card overflow-hidden">
          <table class="w-full text-sm">
            <thead>
              <tr class="bg-msc-blue text-white text-xs">
                <th class="py-2 px-3 text-left font-semibold">Nr.</th>
                <th class="py-2 px-3 text-left font-semibold">Fahrer</th>
                <th class="py-2 px-3 text-right font-semibold">Zeit</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="r in dhFinishResults" :key="r.result_id || r.participant_id"
                  class="border-b border-gray-50 even:bg-gray-50/50">
                <td class="py-2 px-3 font-black text-gray-700">{{ r.start_number }}</td>
                <td class="py-2 px-3">
                  <div class="font-semibold text-gray-800 text-xs">{{ r.first_name[0] }}. {{ r.last_name }}</div>
                </td>
                <td class="py-2 px-3 text-right font-mono font-bold text-sm">
                  <span v-if="r.status === 'valid' && r.total_time !== null">{{ dhFormatTime(r.total_time) }}</span>
                  <span v-else class="badge-warn text-xs">{{ r.status?.toUpperCase() }}</span>
                </td>
              </tr>
              <tr v-if="dhFinishResults.length === 0">
                <td colspan="3" class="py-8 text-center text-xs text-gray-400">Noch keine Zieldurchfahrten</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      <!-- ── RECHTS: Komplette Starterliste ── -->
      <aside class="col-span-full lg:col-span-4 space-y-3">
        <div class="flex items-center justify-between px-1">
          <h2 class="text-xs font-bold uppercase tracking-widest text-gray-500">Starterliste</h2>
          <span class="text-xs text-gray-400">
            {{ dhSchedule.filter(s => s.finished).length }}/{{ dhSchedule.length }} fertig
          </span>
        </div>
        <div class="card overflow-hidden" style="max-height: calc(100vh - 240px); overflow-y: auto;">
          <table class="w-full text-xs">
            <tbody class="divide-y divide-gray-100">
              <tr v-for="s in dhSchedule" :key="s.id"
                  class="transition"
                  :class="{
                    'bg-msc-blue/10': s.id === dhNext?.id,
                    'opacity-50 bg-green-50/30': s.finished
                  }">
                <td class="py-1.5 px-3 font-mono text-gray-500 w-14">{{ s.scheduled_start?.slice(11, 16) }}</td>
                <td class="py-1.5 px-2 font-black text-gray-700 w-10">#{{ s.start_number }}</td>
                <td class="py-1.5 px-2 text-gray-800">{{ s.first_name }} {{ s.last_name }}</td>
                <td class="py-1.5 px-2 text-center w-6">
                  <span v-if="s.finished" class="text-green-500">✓</span>
                  <span v-else-if="s.id === dhNext?.id" class="text-msc-blue">→</span>
                </td>
              </tr>
              <tr v-if="!dhSchedule.length">
                <td colspan="4" class="py-6 text-center text-gray-400">Keine Starterliste</td>
              </tr>
            </tbody>
          </table>
        </div>
      </aside>
    </div>
  </div>

  <!-- ══════════ NORMALER ZEITNAHME-MODUS ══════════ -->
  <div v-else class="max-w-7xl mx-auto px-4 py-4 pb-12 grid grid-cols-1 lg:grid-cols-12 gap-4">

    <!-- ── LINKE SPALTE: Startliste ── -->
    <aside class="col-span-full lg:col-span-3 space-y-3">
      <!-- Klassen-Auswahl -->
      <select v-model="selectedClassId" @change="loadClass" class="input font-semibold">
        <option v-for="c in store.classes" :key="c.id" :value="c.id">
          {{ c.name }}
        </option>
      </select>

      <h2 class="text-xs font-bold uppercase tracking-widest text-gray-500 px-1">Startliste</h2>

      <!-- Aktueller Fahrer -->
      <div v-if="currentParticipant" class="bg-msc-blue text-white rounded-xl p-3 shadow-md">
        <div class="flex items-center justify-between mb-1">
          <span class="text-3xl font-black">#{{ currentParticipant.start_number }}</span>
          <span class="bg-white/20 text-xs rounded px-2 py-0.5 font-mono">→ JETZT</span>
        </div>
        <div class="font-bold text-lg leading-tight">
          {{ currentParticipant.first_name }} {{ currentParticipant.last_name }}
        </div>
        <div class="text-blue-200 text-sm">{{ currentParticipant.club_name || 'n.N.' }}</div>
      </div>
      <div v-else class="bg-gray-100 rounded-xl p-3 text-center text-gray-400 text-sm">
        Kein Fahrer ausgewählt
      </div>

      <!-- Warteschlange -->
      <div class="space-y-1.5">
        <div class="flex items-center justify-between px-1">
          <span class="text-xs text-gray-400 font-semibold uppercase tracking-widest">Nächste Starter</span>
          <button v-if="manualOrder.length" @click="manualOrder = []"
            class="text-xs text-orange-600 hover:text-orange-700 font-bold transition">
            ↺ Reihenfolge zurücksetzen
          </button>
        </div>
        <div
          v-for="(p, i) in queue.slice(1, 7)"
          :key="p.id"
          class="bg-white rounded-lg px-3 py-2 flex items-center gap-2 shadow-sm border transition"
          :class="i === 0 ? 'border-blue-200 bg-blue-50/40' : 'border-gray-100'"
        >
          <span class="text-xl font-black text-gray-700 w-8 shrink-0">#{{ p.start_number }}</span>
          <div class="flex-1 min-w-0">
            <div class="font-semibold text-sm text-gray-800 truncate">
              {{ p.first_name }} {{ p.last_name }}
            </div>
            <div class="text-xs text-gray-400">{{ p.club_name || 'n.N.' }}</div>
          </div>
          <div class="flex flex-col items-end gap-0.5 shrink-0">
            <span class="text-xs text-gray-400 font-mono">{{ i + 2 }}.</span>
            <button
              @click="pullForward(p)"
              class="text-xs text-msc-blue hover:text-msc-bluedark font-bold leading-none transition"
              title="Als nächsten starten lassen"
            >↑ Vorziehen</button>
          </div>
        </div>
        <div v-if="queue.length <= 1" class="text-xs text-gray-400 text-center py-2">
          Alle Fahrer abgeschlossen
        </div>
      </div>
    </aside>

    <!-- ── MITTE: Eingabe ── -->
    <section class="col-span-full lg:col-span-6 space-y-4">

      <!-- Auto-Close Toast -->
      <Transition name="fade">
        <div v-if="autoCloseMsg"
          class="rounded-xl px-4 py-3 flex items-center gap-3 text-sm font-semibold bg-green-100 text-green-800 border border-green-300">
          <span class="text-xl">✓</span>
          {{ autoCloseMsg }}
        </div>
      </Transition>

      <!-- Status-Banner: Klasse noch nicht gestartet / offiziell -->
      <div v-if="classBlockReason" class="rounded-xl px-4 py-3 flex items-center gap-3 text-sm font-semibold"
           :class="selectedClass?.run_status === 'official'
             ? 'bg-green-100 text-green-800 border border-green-300'
             : 'bg-amber-100 text-amber-800 border border-amber-300'">
        <span class="text-xl">{{ selectedClass?.run_status === 'official' ? '✓' : '⚠' }}</span>
        {{ classBlockReason }}
      </div>

      <!-- Zeit-Eingabe -->
      <div class="card p-5">
        <div class="flex items-center justify-between mb-3">
          <h2 class="font-bold text-gray-700 text-sm uppercase tracking-widest">
            <span v-if="currentParticipant">
              #{{ currentParticipant.start_number }} · {{ currentParticipant.first_name }} {{ currentParticipant.last_name }}
            </span>
            <span v-else class="text-gray-400">Kein Fahrer</span>
          </h2>
          <div class="flex gap-1.5">
            <button @click="setStatus('dns')" class="px-3 py-1 rounded-lg text-xs font-bold bg-gray-100 hover:bg-gray-200 text-gray-600 transition">DNS</button>
            <button @click="setStatus('dnf')" class="px-3 py-1 rounded-lg text-xs font-bold bg-amber-100 hover:bg-amber-200 text-amber-700 transition">DNF</button>
            <button @click="setStatus('dsq')" class="px-3 py-1 rounded-lg text-xs font-bold bg-red-100 hover:bg-red-200 text-red-700 transition">DSQ</button>
          </div>
        </div>

        <!-- Lichtschranken-Status -->
        <div class="flex items-center gap-2 text-xs mb-3">
          <span class="h-2 w-2 rounded-full shrink-0 transition-colors duration-500"
                :class="lsConnected ? 'bg-green-500' : 'bg-gray-300'"></span>
          <span :class="lsConnected ? 'text-green-700 font-semibold' : 'text-gray-400'">
            {{ lsConnected ? 'Lichtschranke verbunden' : 'Lichtschranke nicht verbunden' }}
          </span>
          <Transition name="fade">
            <span v-if="lsFlash" class="ml-auto text-green-600 font-bold">
              ⚡ Zeit eingetragen
            </span>
          </Transition>
        </div>

        <!-- Zeitfeld -->
        <div class="flex items-center gap-3 mb-3">
          <div class="flex-1 relative">
            <input
              ref="timeInput"
              v-model="rawTime"
              type="text"
              inputmode="decimal"
              placeholder="0.00"
              class="w-full text-center border-2 rounded-xl px-4 py-3 text-6xl font-black tabnum focus:outline-none focus:ring-4 bg-blue-50/30 transition-colors duration-300"
              :class="lsFlash
                ? 'border-green-500 ring-4 ring-green-200 bg-green-50/30 text-green-700'
                : 'border-msc-blue focus:ring-blue-200 text-msc-blue'"
              @keydown.enter.prevent="confirm"
            >
            <span class="absolute right-4 top-1/2 -translate-y-1/2 text-gray-400 text-lg font-semibold">s</span>
          </div>
          <div class="text-right text-sm text-gray-500 shrink-0 w-24">
            <div>Strafen:</div>
            <div class="font-bold text-msc-red text-xl tabnum">+ {{ totalPenalties.toFixed(1) }} s</div>
            <div class="border-t border-gray-200 pt-1 mt-1">Gesamt:</div>
            <div class="font-black text-gray-800 text-xl tabnum">
              {{ totalTime !== null ? totalTime.toFixed(2) + ' s' : '–' }}
            </div>
          </div>
        </div>

        <!-- Aktive Strafen -->
        <div class="flex flex-wrap gap-1.5 min-h-8 mb-3 p-2 bg-gray-50 rounded-lg border border-gray-200">
          <span
            v-for="(pen, i) in activePenalties"
            :key="i"
            class="flex items-center gap-1 bg-msc-red text-white text-xs font-bold rounded-full px-2.5 py-1"
          >
            {{ pen.label }} ×{{ pen.count }}
            <button @click="removePenalty(i)" class="ml-1 hover:text-red-200">✕</button>
          </span>
          <span v-if="activePenalties.length === 0" class="text-xs text-gray-400 self-center ml-1">
            Keine Strafen
          </span>
          <span v-else class="text-xs text-gray-400 self-center ml-1">
            = {{ totalPenalties.toFixed(1) }} s
          </span>
        </div>

        <!-- Bestätigen / Undo -->
        <div class="flex gap-2">
          <button
            @click="confirm"
            :disabled="!currentParticipant || (!rawTime && resultStatus === 'valid') || !!classBlockReason"
            class="flex-1 btn-primary py-3 text-lg disabled:opacity-50 flex items-center justify-center gap-2"
          >
            <span>✓ Bestätigen</span>
            <span class="bg-white/20 text-xs rounded px-1.5 py-0.5 font-mono">Enter</span>
          </button>
          <button
            @click="undo"
            :disabled="history.length === 0"
            class="px-4 py-3 btn-secondary disabled:opacity-40 flex items-center gap-1.5"
          >
            ↩ Undo
            <span class="bg-gray-200 text-xs rounded px-1.5 py-0.5 font-mono">Ctrl+Z</span>
          </button>
        </div>

        <!-- Lauf-Anzeige + manueller Override -->
        <div class="flex items-center gap-3 mt-3 pt-3 border-t border-gray-100">
          <div class="shrink-0">
            <div class="text-xs text-gray-400 leading-none mb-0.5">Aktueller Lauf</div>
            <div class="text-base font-black text-msc-blue leading-none">
              {{ selectedRun === 0 ? 'Training' : 'Lauf ' + selectedRun }}
            </div>
          </div>
          <div class="flex-1 flex items-center gap-1 justify-end">
            <span class="text-xs text-gray-400 mr-0.5">Override:</span>
            <button
              v-for="n in runNumbers"
              :key="n"
              @click="changeRun(n)"
              class="px-2 py-0.5 rounded text-xs font-bold transition border"
              :class="selectedRun === n
                ? 'bg-msc-blue/15 text-msc-blue border-msc-blue/40'
                : 'bg-gray-100 hover:bg-gray-200 text-gray-500 border-transparent'"
            >
              {{ n === 0 ? 'Tr.' : 'L' + n }}
            </button>
          </div>
        </div>
      </div>

      <!-- Marshal-Meldungen (immer sichtbar) -->
      <div
        class="card p-3 border-2 transition-colors duration-300"
        :class="marshalQueue.length
          ? 'border-yellow-400 bg-yellow-50'
          : 'border-gray-200 bg-gray-50/60'"
      >
        <div class="flex items-center gap-2 mb-2">
          <span
            class="font-black text-xs uppercase tracking-widest"
            :class="marshalQueue.length ? 'text-yellow-600' : 'text-gray-400'"
          >🚩 Streckenposten-Meldungen</span>
          <span
            v-if="marshalQueue.length"
            class="ml-1 bg-yellow-500 text-white text-xs font-black rounded-full w-5 h-5 flex items-center justify-center"
          >{{ marshalQueue.length }}</span>
          <span v-else class="ml-auto text-xs text-gray-400">Keine offenen Meldungen</span>
        </div>
        <TransitionGroup name="marshal-list" tag="div" class="space-y-1.5">
          <div
            v-for="m in marshalQueue"
            :key="m._id"
            class="flex items-center gap-2 bg-white rounded-lg px-3 py-2 border border-yellow-200 text-sm shadow-sm"
          >
            <div class="flex-1 min-w-0">
              <div class="flex items-center gap-2">
                <span class="font-black text-yellow-600 tabnum text-base">+{{ m.penalty_seconds.toFixed(0) }} s</span>
                <span class="text-xs font-semibold text-gray-500 truncate">{{ m.station }}</span>
                <span class="text-xs text-gray-400 ml-auto shrink-0 font-mono">{{ m.marshal }}</span>
              </div>
              <div v-if="m.penalty_label && m.penalty_label !== m.penalty_seconds.toFixed(0) + 's'"
                   class="text-xs text-gray-500 mt-0.5">{{ m.penalty_label }}</div>
            </div>
            <div class="flex gap-1.5 shrink-0">
              <button
                @click="acceptMarshalPenalty(m)"
                class="bg-yellow-500 hover:bg-yellow-600 text-white text-xs font-bold rounded-lg px-3 py-1.5 transition active:scale-95"
              >✓ Übernehmen</button>
              <button
                @click="dismissMarshalPenalty(m)"
                class="bg-gray-200 hover:bg-gray-300 text-gray-600 text-xs font-bold rounded-lg px-2 py-1.5 transition"
              >✕</button>
            </div>
          </div>
        </TransitionGroup>
      </div>

      <!-- Straf-Buttons -->
      <div class="card p-4">
        <h2 class="font-bold text-gray-700 text-xs uppercase tracking-widest mb-3">
          Strafen · {{ currentReglement?.name || '–' }}
        </h2>
        <div v-if="penalties.length === 0" class="text-sm text-gray-400">
          Kein Reglement / keine Strafen definiert.
        </div>
        <div class="grid grid-cols-3 gap-2">
          <button
            v-for="pen in penalties"
            :key="pen.id"
            @click="addPenalty(pen)"
            class="relative bg-red-50 hover:bg-msc-red hover:text-white border-2 border-red-200 hover:border-msc-red rounded-xl p-3 text-left transition group active:scale-95"
            :class="{ 'col-span-2': pen.sort_order >= 99 }"
          >
            <div class="text-xs opacity-55 font-semibold mb-1 group-hover:opacity-70">
              {{ pen.shortcut_key ? 'Taste: ' + pen.shortcut_key : '' }}
            </div>
            <div class="font-bold text-sm text-gray-800 group-hover:text-white">{{ pen.label }}</div>
            <div class="text-xs text-gray-500 group-hover:text-white/80">+ {{ pen.seconds.toFixed(1) }} s</div>
          </button>
        </div>
      </div>
    </section>

    <!-- ── RECHTE SPALTE: Ergebnisse ── -->
    <aside class="col-span-full lg:col-span-3 space-y-3">
      <div class="flex items-center justify-between px-1">
        <h2 class="text-xs font-bold uppercase tracking-widest text-gray-500">
          Lauf {{ selectedRun === 0 ? 'Training' : selectedRun }} – Ergebnisse
        </h2>
        <span class="text-xs text-gray-400">{{ runResults.length }}</span>
      </div>

      <div class="card overflow-hidden">
        <table class="w-full text-sm">
          <thead>
            <tr class="bg-msc-blue text-white text-xs">
              <th class="py-2 px-2 text-left font-semibold">#</th>
              <th class="py-2 px-2 text-left font-semibold">Fahrer</th>
              <th class="py-2 px-2 text-right font-semibold">Zeit</th>
              <th class="py-2 px-2 text-right font-semibold">Ges.</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="r in runResults"
              :key="r.result_id"
              class="border-b border-gray-50 even:bg-gray-50/50"
              :class="{ 'bg-blue-50': r.participant_id === currentParticipant?.id }"
            >
              <td class="py-2 px-2 font-black text-gray-600">{{ r.start_number }}</td>
              <td class="py-2 px-2">
                <div class="font-semibold text-gray-800 text-xs">
                  {{ r.first_name[0] }}. {{ r.last_name }}
                </div>
                <div class="text-gray-400" style="font-size:10px">{{ r.club }}</div>
              </td>
              <td class="py-2 px-2 text-right font-mono text-xs text-gray-600">
                <span v-if="r.status === 'valid' && r.raw_time !== null">{{ r.raw_time.toFixed(2) }}</span>
                <span v-else class="badge-warn">{{ r.status.toUpperCase() }}</span>
              </td>
              <td class="py-2 px-2 text-right font-mono font-bold text-xs">
                <span v-if="r.total_time !== null" :class="r.total_penalties > 0 ? 'text-msc-red' : 'text-gray-800'">
                  {{ r.total_time.toFixed(2) }}
                </span>
                <span v-else class="text-gray-300">–</span>
              </td>
            </tr>
            <tr v-if="runResults.length === 0">
              <td colspan="4" class="py-4 text-center text-xs text-gray-400">Noch keine Ergebnisse</td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Klassen-Status -->
      <div class="card p-3 space-y-1.5">
        <h3 class="text-xs font-bold uppercase tracking-widest text-gray-500 mb-2">Klassen-Status</h3>
        <div
          v-for="c in store.classes"
          :key="c.id"
          class="flex items-center justify-between text-xs"
        >
          <span :class="c.id === selectedClassId ? 'font-semibold text-msc-blue' : 'text-gray-600'">
            {{ c.name }}
          </span>
          <span
            class="font-bold rounded px-1.5 py-0.5"
            :class="{
              'bg-green-100 text-green-700': c.run_status === 'official',
              'bg-msc-blue/10 text-msc-blue': c.run_status === 'running',
              'bg-amber-100 text-amber-700': c.run_status === 'preliminary',
              'bg-gray-100 text-gray-500': c.run_status === 'planned',
            }"
          >
            {{ statusLabel(c.run_status) }}
          </span>
        </div>
      </div>
    </aside>

  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import api from '../api/client'
import { useEventStore } from '../stores/event'
import { useRealtimeUpdate } from '../composables/useRealtimeUpdate'

const store = useEventStore()

const selectedClassId  = ref(null)
const selectedRun      = ref(1)
const rawTime          = ref('')
const resultStatus     = ref('valid')
const activePenalties  = ref([])  // [{ id, label, seconds, count }]
const penalties        = ref([])
const participants     = ref([])
const runResults       = ref([])
const allClassResults  = ref([])   // alle Läufe der Klasse (für Auto-Advance)
const history          = ref([])  // für Undo
const currentReglement = ref(null)
const timeInput        = ref(null)
const manualOrder      = ref([])  // participant IDs in user-defined sequence

// ── Downhill-Modus ────────────────────────────────────────────────────────────
const isDownhill      = computed(() => store.activeEvent?.timing_mode === 'downhill')
const dhSchedule      = ref([])
const dhFinishResults = ref([])
const dhClock         = ref('')
const dhFinishFlash   = ref(false)
let   dhTickId        = null
let   dhFlashTimer    = null

const dhNext = computed(() => dhSchedule.value.find(s => !s.finished) ?? null)
const dhUpcoming = computed(() => dhSchedule.value.filter(s => !s.finished))

const dhCountdownSec = computed(() => {
  if (!dhNext.value?.scheduled_start) return null
  return Math.round((new Date(dhNext.value.scheduled_start).getTime() - Date.now()) / 1000)
})

const dhCountdown = computed(() => {
  const sec = dhCountdownSec.value
  if (sec === null || sec <= 0) return null
  const m = Math.floor(sec / 60)
  const s = sec % 60
  return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`
})

function dhFormatTime(secs) {
  if (secs == null) return '–'
  const m = Math.floor(secs / 60)
  const s = (secs % 60).toFixed(2).padStart(5, '0')
  return m > 0 ? `${m}:${s}` : `${Number(secs).toFixed(2)} s`
}

async function loadDhSchedule() {
  if (!store.activeEvent) return
  try {
    const { data } = await api.get(`/events/${store.activeEvent.id}/schedule`)
    dhSchedule.value = data
  } catch { dhSchedule.value = [] }
}

async function loadDhResults() {
  if (!store.activeEvent) return
  try {
    const { data } = await api.get(`/events/${store.activeEvent.id}/run-results`, {
      params: { run_number: 1 },
    })
    dhFinishResults.value = [...data]
      .sort((a, b) => (a.start_number ?? 0) - (b.start_number ?? 0))
      .slice(0, 30)
  } catch { dhFinishResults.value = [] }
}

// ── Lichtschranke / Timing-Device ─────────────────────────────────────────────
const lsConnected  = ref(false)   // Raspi aktuell verbunden
const lsFlash      = ref(false)   // kurzes Aufleuchten wenn Zeit ankommt
let lsFlashTimer   = null

// ── Auto-Close ────────────────────────────────────────────────────────────────
const autoCloseMsg  = ref('')     // Toast-Text wenn Klasse automatisch geschlossen

// ── Marshal-Meldungen ──────────────────────────────────────────────────────────
const marshalQueue   = ref([])    // eingehende Streckenposten-Meldungen
let _marshalSeq      = 0
const _marshalTimers = new Map()
const _seenReportIds = new Set()  // report_id (DB) — einmal gesehen/verworfen, nicht wieder laden
const _seenReportTs  = new Set()  // ts — Fallback für WS-only-Meldungen ohne report_id

function _markSeen(m) {
  if (m.report_id != null) _seenReportIds.add(m.report_id)
  if (m.ts)                _seenReportTs.add(m.ts)
}

function acceptMarshalPenalty(m) {
  if (m.penalty_id) {
    const pen = penalties.value.find(p => p.id === m.penalty_id)
    if (pen) { addPenalty(pen); dismissMarshalPenalty(m); return }
  }
  // Ad-hoc: Fehlerpunkte direkt hinzufügen
  const adHocId = `marshal_${m.penalty_seconds}`
  const existing = activePenalties.value.find(p => p.id === adHocId)
  if (existing) existing.count++
  else activePenalties.value.push({ id: adHocId, label: `Posten (${m.station})`, seconds: m.penalty_seconds, count: 1 })
  dismissMarshalPenalty(m)
}

function dismissMarshalPenalty(m) {
  clearTimeout(_marshalTimers.get(m._id))
  _marshalTimers.delete(m._id)
  marshalQueue.value = marshalQueue.value.filter(x => x._id !== m._id)
  _markSeen(m)
}

function isClassComplete() {
  const reg = currentReglement.value
  const cls = selectedClass.value
  if (!reg || !participants.value.length) return false
  if (!cls || !['running', 'paused'].includes(cls.run_status)) return false
  for (let rn = 1; rn <= reg.runs_per_class; rn++) {
    const done = new Set(
      allClassResults.value.filter(r => r.run_number === rn).map(r => r.participant_id)
    )
    if (done.size < participants.value.length) return false
  }
  return true
}

async function tryAutoCloseClass() {
  if (!isClassComplete() || !store.activeEvent) return
  try {
    await api.post(`/events/${store.activeEvent.id}/classes/${selectedClassId.value}/auto-close`)
    await store.selectEvent(store.activeEvent)
    const cls = selectedClass.value
    autoCloseMsg.value = `Klasse "${cls?.name ?? ''}" automatisch auf Vorläufig gesetzt.`
    setTimeout(() => { autoCloseMsg.value = '' }, 6000)
  } catch {
    // Kein Admin/Schiri-Recht oder falscher Status — still ignorieren
  }
}

async function loadPendingMarshalReports() {
  if (!store.activeEvent) return
  try {
    const { data } = await api.get('/marshal/reports', {
      params: { event_id: store.activeEvent.id, cancelled: 0, limit: 20 },
    })
    // Nur Reports der letzten 30 Minuten und nur solche die noch nicht in der Queue sind
    const cutoff = Date.now() - 30 * 60 * 1000
    for (const r of data) {
      if (_seenReportIds.has(r.id)) continue
      if (_seenReportTs.has(r.ts))  continue
      if (marshalQueue.value.some(m => m.ts === r.ts)) continue  // schon in Queue
      if (new Date(r.ts).getTime() < cutoff) continue
      const entry = {
        _id:             ++_marshalSeq,
        ts:              r.ts,
        report_id:       r.id,
        penalty_seconds: r.penalty_seconds,
        penalty_label:   r.penalty_label,
        penalty_id:      null,
        station:         r.station,
        class_id:        r.class_id,
        marshal:         r.marshal_user,
      }
      marshalQueue.value.push(entry)
      const t = setTimeout(() => dismissMarshalPenalty(entry), 60_000)
      _marshalTimers.set(entry._id, t)
    }
  } catch {
    // Zeitnahme-Rolle hat evtl. keinen Zugriff — still ignorieren
  }
}

async function handleWsMessage(data) {
  if (data.type === 'timing_device_status') {
    lsConnected.value = data.connected
  }
  if (data.type === 'timing_device_heartbeat') {
    lsConnected.value = true
  }
  if (data.type === 'timing_result' && typeof data.raw_time === 'number') {
    rawTime.value      = data.raw_time.toFixed(2)
    resultStatus.value = 'valid'
    lsFlash.value      = true
    clearTimeout(lsFlashTimer)
    lsFlashTimer = setTimeout(() => { lsFlash.value = false }, 1800)
    timeInput.value?.focus()
  }
  // Downhill: Zieldurchfahrt oder Ergebnis-Update
  if (data.type === 'timing_finish' || (data.type === 'results' && isDownhill.value)) {
    dhFinishFlash.value = true
    clearTimeout(dhFlashTimer)
    dhFlashTimer = setTimeout(() => { dhFinishFlash.value = false }, 2500)
    await loadDhSchedule()
    await loadDhResults()
  }
  // Normal: Reload results if another client confirmed a result
  if (data.type === 'results' && !isDownhill.value && data.class_id === selectedClassId.value) {
    loadRunResults()
  }
  // Eingehende Streckenposten-Meldung (class_id optional — zeige immer wenn passend oder kein Filter)
  if (data.type === 'marshal_penalty' &&
      (data.class_id == null || data.class_id === selectedClassId.value)) {
    const entry = { ...data, _id: ++_marshalSeq }
    marshalQueue.value.push(entry)
    const t = setTimeout(() => dismissMarshalPenalty(entry), 60_000)
    _marshalTimers.set(entry._id, t)
  }
  // Streckenposten hat Meldung storniert — aus Queue entfernen
  if (data.type === 'marshal_cancel') {
    const target = marshalQueue.value.find(m => m.ts === data.ts)
    if (target) dismissMarshalPenalty(target)
  }
}

useRealtimeUpdate(handleWsMessage)

const selectedClass = computed(() =>
  store.classes.find(c => c.id === selectedClassId.value) || null
)

// null = OK; string = Grund warum Eingabe gesperrt
const classBlockReason = computed(() => {
  const cls = selectedClass.value
  if (!cls) return null
  if (cls.is_exhibition) return null
  if (cls.run_status === 'official')
    return 'Klasse ist offiziell freigegeben – keine Zeiteingaben mehr möglich.'
  if (cls.run_status === 'planned')
    return 'Klasse noch nicht gestartet – bitte Schiedsrichter den Start bestätigen lassen.'
  if (cls.run_status === 'preliminary')
    return 'Klasse abgeschlossen (vorläufig) – keine neuen Zeiteingaben.'
  return null  // running / paused → OK
})

const runNumbers = computed(() => {
  const reg = currentReglement.value
  if (!reg) return [1]
  const nums = []
  if (reg.has_training) nums.push(0)
  for (let i = 1; i <= reg.runs_per_class; i++) nums.push(i)
  return nums
})

// Fahrerliste — pending vor done; pending kann per manualOrder umsortiert werden
const queue = computed(() => {
  if (!participants.value.length) return []
  const doneIds = new Set(runResults.value.map(r => r.participant_id))
  const done    = participants.value.filter(p =>  doneIds.has(p.id))
  let   pending = participants.value.filter(p => !doneIds.has(p.id))

  if (manualOrder.value.length) {
    const rank = new Map(manualOrder.value.map((id, i) => [id, i]))
    pending = [...pending].sort((a, b) => {
      const ra = rank.has(a.id) ? rank.get(a.id) : Infinity
      const rb = rank.has(b.id) ? rank.get(b.id) : Infinity
      return ra !== rb ? ra - rb : (a.start_number ?? 9999) - (b.start_number ?? 9999)
    })
  } else {
    pending = [...pending].sort((a, b) => (a.start_number ?? 9999) - (b.start_number ?? 9999))
  }
  return [...pending, ...done]
})

// Einen Fahrer ganz nach vorne ziehen (wird sofort als nächster angezeigt)
function pullForward(p) {
  const doneIds = new Set(runResults.value.map(r => r.participant_id))
  const pending = queue.value.filter(pp => !doneIds.has(pp.id))
  manualOrder.value = [p.id, ...pending.filter(pp => pp.id !== p.id).map(pp => pp.id)]
}

const currentParticipant = computed(() => queue.value[0] || null)

const totalPenalties = computed(() =>
  activePenalties.value.reduce((s, p) => s + p.seconds * p.count, 0)
)

const totalTime = computed(() => {
  const t = parseFloat(rawTime.value)
  if (isNaN(t) || resultStatus.value !== 'valid') return null
  return t + totalPenalties.value
})

// Ermittelt automatisch den aktuellen Lauf (erster Lauf, der noch nicht alle Fahrer hat)
function computeAutoRun() {
  const reg = currentReglement.value
  if (!reg || !participants.value.length) return selectedRun.value
  const nums = []
  if (reg.has_training) nums.push(0)
  for (let i = 1; i <= reg.runs_per_class; i++) nums.push(i)
  for (const rn of nums) {
    const done = new Set(allClassResults.value.filter(r => r.run_number === rn).map(r => r.participant_id))
    if (done.size < participants.value.length) return rn
  }
  return nums[nums.length - 1]
}

// Strafen laden wenn Klasse gewechselt
async function loadClass() {
  if (!selectedClassId.value || !store.activeEvent) return
  manualOrder.value = []
  const eid = store.activeEvent.id
  const cid = selectedClassId.value
  const cls = store.classes.find(c => c.id === cid)
  const regId = cls?.reglement_id
  if (regId) {
    const [regRes, penRes] = await Promise.all([
      api.get(`/reglements/${regId}`),
      api.get(`/reglements/${regId}/penalties`)
    ])
    currentReglement.value = regRes.data
    penalties.value = penRes.data
  } else {
    currentReglement.value = null
    penalties.value = []
  }
  const [partRes, allRes] = await Promise.all([
    api.get(`/events/${eid}/participants`),
    api.get(`/events/${eid}/run-results`, { params: { class_id: cid } }),
  ])
  participants.value = partRes.data.filter(p => p.class_id === cid)
  allClassResults.value = allRes.data
  selectedRun.value = computeAutoRun()
  await loadRunResults()
  await loadPendingMarshalReports()
  resetInput()
}

async function loadRunResults() {
  if (!store.activeEvent || !selectedClassId.value) return
  const { data } = await api.get(`/events/${store.activeEvent.id}/run-results`, {
    params: { class_id: selectedClassId.value, run_number: selectedRun.value }
  })
  runResults.value = data
}

async function changeRun(n) {
  selectedRun.value = n
  manualOrder.value = []
  await loadRunResults()
}

function resetInput() {
  rawTime.value = ''
  resultStatus.value = 'valid'
  activePenalties.value = []
  // Alle noch offenen Marshal-Meldungen als "gesehen" markieren und Queue leeren
  marshalQueue.value.forEach(_markSeen)
  _marshalTimers.forEach(t => clearTimeout(t))
  _marshalTimers.clear()
  marshalQueue.value = []
  timeInput.value?.focus()
}

function addPenalty(pen) {
  const existing = activePenalties.value.find(p => p.id === pen.id)
  if (existing) existing.count++
  else activePenalties.value.push({ id: pen.id, label: pen.label, seconds: pen.seconds, count: 1 })
}

function removePenalty(index) {
  const pen = activePenalties.value[index]
  if (pen.count > 1) pen.count--
  else activePenalties.value.splice(index, 1)
}

function setStatus(s) {
  resultStatus.value = s
  if (s !== 'valid') rawTime.value = ''
}

async function confirm() {
  if (!currentParticipant.value || !store.activeEvent) return
  const p = currentParticipant.value

  // Trenne definierte Strafen (integer ID) von Ad-hoc-Marshal-Strafen (string ID)
  const definedPenalties = activePenalties.value.filter(pen => typeof pen.id === 'number')
  const adHocSeconds     = activePenalties.value
    .filter(pen => typeof pen.id !== 'number')
    .reduce((s, pen) => s + pen.seconds * pen.count, 0)

  // Ad-hoc-Sekunden in raw_time einrechnen (keine penalty_definition_id vorhanden)
  const baseTime = resultStatus.value === 'valid' ? parseFloat(rawTime.value) : null
  const rt = (baseTime !== null && !isNaN(baseTime)) ? baseTime + adHocSeconds : null

  // ── Schritt 1: Ergebnis speichern (kritisch — bei Fehler abbrechen) ──
  let result
  try {
    const res = await api.post(
      `/events/${store.activeEvent.id}/results`,
      {
        event_id:       store.activeEvent.id,
        participant_id: p.id,
        class_id:       selectedClassId.value,
        run_number:     selectedRun.value,
        raw_time:       rt === null ? null : rt,
        status:         resultStatus.value,
      }
    )
    result = res.data
  } catch (e) {
    alert(e.response?.data?.detail || 'Fehler beim Speichern')
    return  // Nur hier abbrechen — Ergebnis noch nicht gespeichert
  }

  // ── Schritt 2: Strafen speichern (unkritisch — Fehler blockieren nicht) ──
  for (const pen of definedPenalties) {
    try {
      await api.post(
        `/events/${store.activeEvent.id}/results/${result.id}/penalties`,
        { result_id: result.id, penalty_definition_id: pen.id, count: pen.count }
      )
    } catch (e) {
      console.warn('Strafe konnte nicht gespeichert werden:', pen.label, e?.response?.data?.detail)
    }
  }

  // ── Schritt 3: Weiterschalten — läuft immer durch ──
  history.value.push({ resultId: result.id, participantId: p.id })
  const { data: allRes } = await api.get(
    `/events/${store.activeEvent.id}/run-results`,
    { params: { class_id: selectedClassId.value } }
  )
  allClassResults.value = allRes
  const ar = computeAutoRun()
  if (ar !== selectedRun.value) {
    selectedRun.value = ar
    manualOrder.value = []
  }
  await loadRunResults()
  await tryAutoCloseClass()
  resetInput()
}

async function undo() {
  const last = history.value.pop()
  if (!last || !store.activeEvent) return
  // Ergebnis löschen ist nicht direkt vorgesehen — Status auf DSQ setzen als Notlösung
  // In echter Implementierung: DELETE /results/{id}
  await loadRunResults()
}

// Keyboard shortcuts
function onKey(e) {
  if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') {
    return  // Enter auf dem Zeitfeld wird per @keydown.enter im Template behandelt
  }
  if (e.ctrlKey && e.key === 'z') { undo(); return }
  const pen = penalties.value.find(p => p.shortcut_key === e.key.toUpperCase())
  if (pen) addPenalty(pen)
}

onMounted(async () => {
  if (isDownhill.value) {
    await loadDhSchedule()
    await loadDhResults()
    dhClock.value = new Date().toTimeString().slice(0, 8)
    dhTickId = setInterval(() => {
      dhClock.value = new Date().toTimeString().slice(0, 8)
    }, 500)
  } else if (store.classes.length) {
    const running = store.classes.find(c => c.run_status === 'running')
    selectedClassId.value = (running ?? store.classes[0]).id
    await loadClass()
  } else {
    await loadPendingMarshalReports()
  }
  window.addEventListener('keydown', onKey)
})

onUnmounted(() => {
  window.removeEventListener('keydown', onKey)
  _marshalTimers.forEach(t => clearTimeout(t))
  if (dhTickId) clearInterval(dhTickId)
  clearTimeout(dhFlashTimer)
})

watch(rawTime, (val) => {
  if (typeof val === 'string' && val.includes(','))
    rawTime.value = val.replace(/,/g, '.')
})

watch(() => store.classes, async (v) => {
  if (isDownhill.value) return
  if (v.length && !selectedClassId.value) {
    const running = v.find(c => c.run_status === 'running')
    selectedClassId.value = (running ?? v[0]).id
    await loadClass()
  }
})

function statusLabel(s) {
  return { planned: 'Geplant', running: 'Läuft', paused: 'Unterbrochen', preliminary: 'Vorläufig', official: 'Offiziell' }[s] || s
}
</script>

<style scoped>
.fade-enter-active, .fade-leave-active { transition: opacity 0.4s ease; }
.fade-enter-from, .fade-leave-to       { opacity: 0; }

.marshal-list-enter-active { transition: all 0.25s ease; }
.marshal-list-leave-active { transition: all 0.2s ease; }
.marshal-list-enter-from   { opacity: 0; transform: translateY(-8px); }
.marshal-list-leave-to     { opacity: 0; transform: translateX(20px); }
</style>
