import { esc, fmtDate, printOpen } from './print'
import { PROTEST_WINDOW_MIN } from '../constants/contest'

export async function printErgebnisliste(api, event, classes) {
  const eventId = event.id
  const [stRes, runRes, setRes, partRes] = await Promise.all([
    api.get(`/events/${eventId}/standings`),
    api.get(`/events/${eventId}/run-results`),
    api.get('/settings/'),
    api.get(`/events/${eventId}/participants`),
  ])

  const settings = setRes.data

  const byYear = {}
  for (const p of partRes.data) {
    byYear[`${p.class_id}_${p.start_number}`] = p.birth_year
  }

  const runMap = {}
  for (const r of runRes.data) {
    if (r.run_number === 0) continue
    ;(runMap[r.class_id] ??= {})[r.start_number] ??= {}
    runMap[r.class_id][r.start_number][r.run_number] = r
  }

  const byClass = {}
  for (const row of stRes.data) {
    ;(byClass[row.class_id] ??= []).push(row)
  }

  const maxRun = runRes.data.reduce((m, r) => Math.max(m, r.run_number), 0) || 2

  function fmtT(v)   { return v != null ? Number(v).toFixed(2) : '' }
  function fmtP(v)   { return v != null && v > 0 ? '+' + Number(v).toFixed(1) : (v === 0 ? '0' : '') }
  function fmtTot(t) { return t != null ? t.toFixed(2) : '–' }

  function runCells(r) {
    if (!r) return ['–', '', '']
    if (r.status !== 'valid') return [`<em>${r.status.toUpperCase()}</em>`, '', '']
    return [fmtT(r.raw_time), fmtP(r.total_penalties), fmtT(r.total_time)]
  }

  const now       = new Date()
  const printDate = now.toLocaleString('de-DE', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' })

  const runGroupHeaders = Array.from({ length: maxRun }, (_, i) =>
    `<th colspan="3" class="run-group">${i + 1}. Lauf</th>`
  ).join('')
  const runSubHeaders = Array.from({ length: maxRun }, () =>
    `<th class="tr">Fahrzeit</th><th class="tr">Fehlerpkt.</th><th class="tr">Gesamt</th>`
  ).join('')

  const classesHtml = classes
    .filter(cls => byClass[cls.id]?.length)
    .map(cls => {
      const rows   = byClass[cls.id]
      const leader = rows.find(r => r.total_time != null)
      const cRuns  = runMap[cls.id] || {}
      const isOk   = cls.run_status === 'official'
      const badge  = `<span class="badge ${isOk ? 'b-ok' : 'b-pre'}">${isOk ? 'OFFIZIELL' : 'VORLÄUFIG'}</span>`
      const deadline = cls.end_time
        ? new Date(new Date(cls.end_time).getTime() + PROTEST_WINDOW_MIN * 60_000)
            .toLocaleTimeString('de-DE', { hour: '2-digit', minute: '2-digit' }) + ' Uhr'
        : '–'

      const rowsHtml = rows.map((row, i) => {
        const runs      = cRuns[row.start_number] || {}
        const birthYear = byYear[`${cls.id}_${row.start_number}`] || ''
        const hasTime   = row.total_time != null
        const diff      = (!hasTime || !leader?.total_time || row.total_time === leader.total_time)
          ? '–'
          : '+' + (row.total_time - leader.total_time).toFixed(2)

        const runTdHtml = Array.from({ length: maxRun }, (_, ri) => {
          const [z, s, g] = runCells(runs[ri + 1])
          return `<td class="tr">${z}</td><td class="tr straf">${s}</td><td class="tr">${g}</td>`
        }).join('')

        const rowCls = i === 0 && hasTime ? 'rank-1' : i === 1 && hasTime ? 'rank-2' : i === 2 && hasTime ? 'rank-3' : ''
        return `<tr class="${rowCls}">
          <td class="tc bold">${row.rank}</td>
          <td class="tc bold">#${row.start_number}</td>
          <td><strong>${esc(row.last_name)}</strong>, ${esc(row.first_name)}</td>
          <td class="tc">${birthYear}</td>
          <td>${esc(row.club || '–')}</td>
          ${runTdHtml}
          <td class="tr bold">${fmtTot(row.total_time)}</td>
          <td class="tr">${diff}</td>
        </tr>`
      }).join('')

      return `<div class="cls-section">
        <div class="cls-header">${esc(cls.name)} ${badge}</div>
        <table>
          <thead>
            <tr>
              <th rowspan="2" style="width:20px">Pl.</th>
              <th rowspan="2" style="width:28px">St.Nr.</th>
              <th rowspan="2">Name, Vorname</th>
              <th rowspan="2" style="width:22px">Jg.</th>
              <th rowspan="2" style="width:26mm">Verein</th>
              ${runGroupHeaders}
              <th rowspan="2" class="tr" style="width:16mm">Summe</th>
              <th rowspan="2" class="tr" style="width:14mm">Diff.</th>
            </tr>
            <tr>${runSubHeaders}</tr>
          </thead>
          <tbody>${rowsHtml}</tbody>
        </table>
        <div class="class-footer">
          <span>Einspruchfrist ${PROTEST_WINDOW_MIN} Min. ab Aushang · bis: <strong>${deadline}</strong></span>
          <span class="sig-block">Schiedsrichter/Sportkommissär: <span class="sig-line"></span></span>
        </div>
      </div>`
    }).join('')

  const html = `
    <style>@page { size: A4 landscape; margin: 1.0cm 1.4cm; }</style>
    <header class="ev-header">
      <div>
        <div class="ev-tag">ADAC Hessen-Thüringen e.V. · Kart-Slalom</div>
        <h1>ERGEBNISLISTE</h1>
        <h2>${esc(event.name)}</h2>
        <div class="ev-meta">${fmtDate(event.date)} &nbsp;·&nbsp; ${esc(event.location || '')} &nbsp;·&nbsp; Veranstalter: ${esc(settings.organizer_name || 'MSC Braach e.V. im ADAC')}</div>
      </div>
      <div class="ev-print">Ausdruck: ${printDate}</div>
    </header>
    ${classesHtml}
    <footer>RaceControl Pro · ${esc(settings.organizer_name || 'MSC Braach e.V. im ADAC')}</footer>`

  const w = window.open('', '_blank', 'width=1200,height=800')
  if (!w) { alert('Popup wurde blockiert – bitte Popups für diese Seite erlauben.'); return }
  w.document.write(`<!DOCTYPE html><html lang="de"><head>
<meta charset="UTF-8"><title>Ergebnisliste – ${esc(event.name)}</title>
<style>
  * { box-sizing: border-box; }
  body { font-family: Arial, Helvetica, sans-serif; font-size: 8.5pt; color: #000; margin: 0; }
  @page { size: A4 landscape; margin: 1.0cm 1.4cm; }
  .ev-header { display: flex; justify-content: space-between; align-items: flex-start;
               border-bottom: 3px solid #1a3fa0; padding-bottom: 5px; margin-bottom: 10px; }
  .ev-tag  { font-size: 7.5pt; color: #1a3fa0; font-weight: bold; letter-spacing: 0.5px; margin-bottom: 1px; }
  h1 { margin: 0; font-size: 15pt; color: #1a3fa0; letter-spacing: 1px; }
  h2 { margin: 1px 0 0; font-size: 10pt; font-weight: normal; }
  .ev-meta { font-size: 8pt; color: #555; margin-top: 2px; }
  .ev-print { font-size: 7.5pt; color: #aaa; align-self: flex-end; }
  .cls-section { margin-bottom: 14px; break-inside: avoid; }
  .cls-header  { background: #1a3fa0; color: #fff; font-size: 9.5pt; font-weight: bold;
                 padding: 3px 7px; margin-bottom: 0; display: flex; align-items: center; gap: 8px; }
  table { width: 100%; border-collapse: collapse; font-size: 8pt; }
  th { border: 1px solid #888; background: #e0e6f0; padding: 2px 4px; text-align: center;
       font-size: 7.5pt; vertical-align: middle; }
  .run-group { background: #c8d4ea; font-weight: bold; }
  td { border: 1px solid #ccc; padding: 2px 4px; vertical-align: middle; }
  .tr   { text-align: right; font-family: 'Courier New', monospace; }
  .tc   { text-align: center; }
  .bold { font-weight: bold; }
  .straf { color: #c00; font-size: 7.5pt; }
  tr:nth-child(even) td { background: #fafafa; }
  .rank-1 td { background: #fffce6 !important; }
  .rank-2 td { background: #f0f0f0 !important; }
  .rank-3 td { background: #fdf2e6 !important; }
  .badge { display: inline-block; font-size: 7pt; font-weight: bold; padding: 1px 5px;
           border-radius: 3px; }
  .b-ok  { background: #d4edda; color: #155724; }
  .b-pre { background: #fff3cd; color: #856404; }
  .class-footer { display: flex; justify-content: space-between; align-items: baseline;
                  font-size: 7.5pt; color: #555; border: 1px solid #ccc; border-top: none;
                  padding: 3px 6px; background: #f9f9f9; }
  .sig-block { display: flex; align-items: baseline; gap: 6px; }
  .sig-line  { display: inline-block; border-bottom: 1px solid #555; width: 80mm; }
  footer { position: fixed; bottom: 4px; left: 0; right: 0; text-align: center;
           font-size: 7pt; color: #bbb; border-top: 1px solid #eee; padding-top: 2px; }
</style>
</head><body>${html}</body></html>`)
  w.document.close()
  setTimeout(() => w.print(), 400)
}

export async function printSprecherliste(api, event, classes) {
  const eventId = event.id
  const [partRes, setRes] = await Promise.all([
    api.get(`/events/${eventId}/participants`),
    api.get('/settings/'),
  ])

  const settings     = setRes.data
  const participants = partRes.data

  const byClass = {}
  for (const p of participants) {
    ;(byClass[p.class_id ?? 0] ??= []).push(p)
  }

  const now       = new Date()
  const printDate = now.toLocaleString('de-DE', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' })

  const classesHtml = [
    ...classes,
    ...(byClass[0]?.length ? [{ id: 0, name: 'Ohne Klasse', start_order: 999 }] : []),
  ]
    .filter(cls => byClass[cls.id]?.length)
    .map(cls => {
      const rows = [...(byClass[cls.id] || [])].sort((a, b) => (a.start_number || 0) - (b.start_number || 0))
      const rowsHtml = rows.map((p, i) => `<tr>
        <td style="text-align:center">${i + 1}</td>
        <td style="text-align:center;font-weight:bold">#${p.start_number ?? '–'}</td>
        <td><strong>${esc(p.last_name)}</strong>, ${esc(p.first_name)}</td>
        <td>${esc(p.club_name || '–')}</td>
        <td style="text-align:center">${p.birth_year ?? '–'}</td>
        <td></td>
      </tr>`).join('')
      return `<div class="cls-section">
        <div class="cls-header">${esc(cls.name)}
          <span style="font-weight:normal;font-size:8pt">(${rows.length} Teilnehmer)</span>
        </div>
        <table>
          <thead><tr>
            <th style="width:28px">Lfd.</th><th style="width:40px">St.Nr.</th>
            <th>Name, Vorname</th><th>Verein</th>
            <th style="width:38px;text-align:center">Jg.</th>
            <th style="width:65px">Notiz</th>
          </tr></thead>
          <tbody>${rowsHtml}</tbody>
        </table>
      </div>`
    }).join('')

  const html = `
    <header class="ev-header">
      <h1>SPRECHERLISTE</h1>
      <h2>${esc(event.name)} · ${fmtDate(event.date)} · ${esc(event.location || '')}</h2>
      <div class="org">Veranstalter: ${esc(settings.organizer_name || 'MSC Braach e.V. im ADAC')}</div>
    </header>
    <style>@page { size: A4 portrait; margin: 1.2cm 1.5cm; }</style>
    ${classesHtml}
    <footer>RaceControl Pro · ${esc(settings.organizer_name || 'MSC Braach e.V. im ADAC')} · Ausdruck: ${printDate}</footer>`

  printOpen(`Sprecherliste – ${event.name}`, html)
}

export async function printUrkunden(api, event, classes, template) {
  const eventId = event.id
  const [stRes, setRes] = await Promise.all([
    api.get(`/events/${eventId}/standings`),
    api.get('/settings/'),
  ])
  const settings = setRes.data

  const RANK_STYLE = {
    1: { bg: '#FFD700', border: '#B8860B', text: '#4A3000', label: '1. Platz' },
    2: { bg: '#D8D8D8', border: '#888',    text: '#2A2A2A', label: '2. Platz' },
    3: { bg: '#CD8040', border: '#8B5020', text: '#fff',    label: '3. Platz' },
  }

  function clubPage(row, cls) {
    const rs  = RANK_STYLE[row.rank] || { bg: '#1a3fa0', border: '#122d78', text: '#fff', label: `${row.rank}. Platz` }
    const org = esc(settings.organizer_name || 'MSC Braach e.V. im ADAC')
    return `
<div class="page">
  <div class="hdr">
    <div class="hdr-org">${org}</div>
    <div class="hdr-sub">Kart-Slalom · ADAC Hessen-Thüringen</div>
  </div>
  <div class="frame">
    <div class="title-block">
      <div class="title-line"></div>
      <div class="title-text">U&nbsp;R&nbsp;K&nbsp;U&nbsp;N&nbsp;D&nbsp;E</div>
      <div class="title-line"></div>
    </div>
    <div class="rank-badge" style="background:${rs.bg};border-color:${rs.border};color:${rs.text}">
      ${rs.label}
    </div>
    <div class="p-name">${esc(row.first_name)}&nbsp;${esc(row.last_name)}</div>
    <div class="p-club">${esc(row.club || '')}</div>
    <div class="achievement">
      hat in der Klasse <span class="hl">${esc(cls.name)}</span> bei der<br>
      <span class="ev-name">${esc(event.name)}</span><br>
      am <span class="hl">${fmtDate(event.date)}</span>
      in <span class="hl">${esc(event.location || '')}</span><br>
      den <span class="hl">${row.rank}. Platz</span> belegt.
    </div>
    ${row.total_time != null
      ? `<div class="time-result">Gesamtzeit: ${row.total_time.toFixed(2)}&thinsp;s</div>`
      : ''}
  </div>
  <div class="cert-footer">
    <div class="foot-place">${esc(event.location || '')}, den ${fmtDate(event.date)}</div>
    <div class="sig-row">
      <div class="sig-col"><div class="sig-line"></div><div class="sig-lbl">Schiedsrichter / Sportkommissär</div></div>
      <div class="sig-col"><div class="sig-line"></div><div class="sig-lbl">Veranstalter</div></div>
    </div>
  </div>
</div>`
  }

  function adacOverlayPage(row, cls) {
    return `
<div class="page overlay-page">
  <div class="guide" style="top:98mm">Veranstaltung</div>
  <div class="guide" style="top:118mm">Klasse / Disziplin</div>
  <div class="guide" style="top:148mm">Name</div>
  <div class="guide" style="top:172mm">Platz</div>
  <div class="guide" style="top:225mm">Datum</div>
  <div class="ol-field ev-field"    style="top:101mm">${esc(event.name)} · ${esc(event.location || '')}</div>
  <div class="ol-field cls-field"   style="top:121mm">${esc(cls.name)}</div>
  <div class="ol-field name-field"  style="top:151mm">${esc(row.first_name)} ${esc(row.last_name)}</div>
  <div class="ol-field rank-field"  style="top:175mm">${row.rank}.</div>
  <div class="ol-field date-field"  style="top:228mm">${fmtDate(event.date)}</div>
</div>`
  }

  const pages = []
  for (const cls of classes) {
    const podium = stRes.data
      .filter(r => r.class_id === cls.id && r.rank <= 3 && r.total_time != null)
      .sort((a, b) => a.rank - b.rank)
    for (const row of podium) {
      pages.push(template === 'club' ? clubPage(row, cls) : adacOverlayPage(row, cls))
    }
  }
  if (!pages.length) {
    alert('Noch keine platzierten Ergebnisse vorhanden.')
    return
  }

  const w = window.open('', '_blank', 'width=900,height=700')
  if (!w) { alert('Popup blockiert.'); return }
  w.document.write(`<!DOCTYPE html><html lang="de"><head>
<meta charset="UTF-8"><title>Urkunden – ${esc(event.name)}</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  @page { size: A4 portrait; margin: 0; }
  body { font-family: 'Georgia', 'Times New Roman', serif; background: #ccc; }
  .page { width: 210mm; height: 297mm; position: relative; overflow: hidden;
          page-break-after: always; background: #fff; margin: 0 auto; }
  .page:last-child { page-break-after: avoid; }
  .hdr { background: #1a3fa0; color: #fff; text-align: center;
         padding: 14mm 12mm 10mm; }
  .hdr-org  { font-size: 15pt; font-weight: bold; letter-spacing: 1px; }
  .hdr-sub  { font-size: 8.5pt; opacity: .75; margin-top: 3px; letter-spacing: 2px; text-transform: uppercase; }
  .frame { margin: 7mm 10mm; border: 3px double #1a3fa0;
           padding: 8mm 12mm; min-height: 185mm;
           display: flex; flex-direction: column; align-items: center; gap: 7mm; }
  .title-block { display: flex; align-items: center; gap: 5mm; width: 100%; }
  .title-line  { flex: 1; border-top: 1.5px solid #1a3fa0; }
  .title-text  { font-size: 22pt; font-weight: bold; color: #1a3fa0; letter-spacing: 4px;
                 white-space: nowrap; }
  .rank-badge  { font-size: 14pt; font-weight: bold; padding: 5px 22px;
                 border: 3px solid; border-radius: 6px; letter-spacing: 1px; }
  .p-name { font-size: 20pt; font-weight: bold; text-align: center;
            color: #111; border-bottom: 1.5px solid #ccc; padding-bottom: 4px; width: 100%; }
  .p-club { font-size: 10pt; color: #666; text-align: center; }
  .achievement { font-size: 11.5pt; text-align: center; line-height: 1.8; color: #222; }
  .hl      { font-weight: bold; color: #1a3fa0; }
  .ev-name { font-style: italic; font-size: 12pt; }
  .time-result { font-size: 10pt; color: #555; font-family: 'Courier New', monospace;
                 background: #f0f4fb; border: 1px solid #c5d0e8; padding: 3px 12px; border-radius: 4px; }
  .cert-footer { position: absolute; bottom: 10mm; left: 10mm; right: 10mm; }
  .foot-place  { font-size: 9pt; color: #555; margin-bottom: 6mm; font-family: Arial, sans-serif; }
  .sig-row     { display: flex; gap: 15mm; }
  .sig-col     { flex: 1; }
  .sig-line    { border-bottom: 1px solid #333; height: 8mm; margin-bottom: 2mm; }
  .sig-lbl     { font-size: 8pt; color: #666; text-align: center; font-family: Arial, sans-serif; }
  .overlay-page { background: transparent; }
  .ol-field     { position: absolute; left: 25mm; right: 20mm; font-family: Arial, sans-serif;
                  font-size: 12pt; font-weight: bold; color: #000; }
  .name-field   { font-size: 16pt; }
  .rank-field   { font-size: 20pt; left: 95mm; }
  .guide        { position: absolute; left: 25mm; right: 20mm; height: 6mm;
                  border: 1px dashed #f90; background: rgba(255,180,0,.08);
                  font-size: 7pt; color: #c70; display: flex; align-items: center; padding-left: 3px; }
  @media print { .guide { display: none !important; } .overlay-page { background: transparent !important; } }
</style>
</head><body>${pages.join('\n')}</body></html>`)
  w.document.close()
  setTimeout(() => w.print(), 500)
}
