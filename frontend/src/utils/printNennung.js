import { esc, fmtDate } from './print'

export async function printNennungsformular(api, event, classes, p) {
  let cfg = {}
  try { const { data } = await api.get('/settings/'); cfg = data } catch { /* ignore */ }

  const cls = classes.find(c => c.id === p.class_id)

  const page1 = `
<div class="page">
  <div class="form-header">
    <div class="form-title">NENNUNGSFORMULAR</div>
    <div class="form-subtitle">für Jugendsport-Veranstaltungen beim ADAC Hessen-Thüringen e.V.</div>
  </div>

  <div class="section-box">
    <div class="section-label">Veranstaltungsdaten:</div>
    <div class="va-types">
      <label><input type="checkbox" checked disabled> <strong>Kartslalom</strong></label>
      <label><input type="checkbox" disabled> Kart-Turnier</label>
      <label><input type="checkbox" disabled> KS 2000</label>
      <label><input type="checkbox" disabled> Mot-Turnier</label>
      <label><input type="checkbox" disabled> Tretcar</label>
      <label><input type="checkbox" disabled> Wassersport</label>
    </div>
    <div class="ev-row">
      <span class="fl">Veranstalter:</span><span class="fv">${esc(cfg.organizer_name || 'MSC Braach e.V. im ADAC')}</span>
      <span class="fl" style="margin-left:16px">Datum:</span><span class="fv">${fmtDate(event.date)}</span>
    </div>
    <div class="ev-row">
      <span class="fl">Veranstaltungsort:</span><span class="fv">${esc(event.location || '')}</span>
    </div>
  </div>

  <div class="two-col">
    <div class="pdata">
      <div class="fr"><div class="lbl">Vorname:</div><div class="vbox">${esc(p.first_name)}</div></div>
      <div class="fr"><div class="lbl">Name:</div><div class="vbox">${esc(p.last_name)}</div></div>
      <div class="fr"><div class="lbl">Straße, Hausnr.:</div><div class="vbox"></div></div>
      <div class="fr"><div class="lbl">PLZ/Wohnort:</div><div class="vbox"></div></div>
      <div class="fr">
        <div class="lbl">Geb.-Datum:</div><div class="vbox short">${p.birth_year ? 'Jg.&nbsp;' + p.birth_year : ''}</div>
        <div class="lbl" style="margin-left:6px">Jugend/Ü18-Ausw.-Nr.:</div><div class="vbox">${esc(p.license_number || '')}</div>
      </div>
      <div class="fr"><div class="lbl">Mitglied im ADAC Ortsclub:</div><div class="vbox">${esc(p.club_name || '')}</div></div>
      <div class="fr"><div class="lbl">Jugendleiter des Ortsclubs:</div><div class="vbox"></div></div>
    </div>

    <div class="vbox-right">
      <div class="vbox-title">Vom Veranstalter auszufüllen:</div>
      <div class="vr-field"><span class="big-lbl">START-NR.</span><span class="big-val">${p.start_number ? '#' + p.start_number : '–'}</span></div>
      <div class="vr-field"><span class="big-lbl">KLASSE</span><span class="big-val">${esc(cls?.short_name || cls?.name || '')}</span></div>
      <div class="vr-check"><label><input type="checkbox" checked disabled> ADAC Jugend/Ü18-Ausweis kontrolliert: <strong>✓</strong></label></div>
      <div class="vr-check"><label><input type="checkbox" checked disabled> Helm homologiert: <strong>✓</strong></label></div>
      <div class="vr-field small"><span class="lbl">Bemerkung:</span><span class="sline"></span></div>
      <div class="vr-field small" style="margin-top:10px"><span class="lbl">Unterschrift:</span><span class="sline"></span></div>
    </div>
  </div>

  <div class="legal">
    <p><strong>Ausschreibung:</strong> Ich/Wir habe/n die Rahmenausschreibung des ADAC Hessen-Thüringen für die oben angekreuzte Veranstaltungsart im Wortlaut zur Kenntnis genommen und genehmige/n die Teilnahme.</p>
    <p><strong>Datenschutz:</strong> Mit Abgabe dieser Nennung und Teilnahme an dieser Veranstaltung erklärt sich der Teilnehmer bzw. seine Erziehungsberechtigten mit der elektronischen Speicherung der wettkampfrelevanten Daten und der Veröffentlichung der Startlisten und Ergebnisse in Aushängen, im Internet und in den Publikationen des Vereins/Verbandes sowie in Pressemitteilungen einverstanden.</p>
    <p><strong>Fotos:</strong> Ich habe / wir haben zur Kenntnis genommen, dass – sollte ich / sollten wir nicht wünschen, dass Fotos von meinem/unserem Kind im Rahmen der Veranstaltung veröffentlicht werden – dies zusammen mit dieser Nennung auf einem gesonderten Schriftstück erklärt werden muss.</p>
  </div>

  <div class="sig-section">
    <div class="sig-row">
      <div class="si"><div class="sline-l"></div><div class="sc">Datum</div></div>
      <div class="si"><div class="sline-l"></div><div class="sc">Unterschrift des Teilnehmers</div></div>
      <div class="si"><div class="sline-l"></div><div class="sc">Unterschrift des/der Erziehungsberechtigten</div></div>
    </div>
  </div>

  <table class="res-table">
    <thead>
      <tr><th colspan="3">1. Lauf</th><th colspan="3">2. Lauf</th><th>Fahrzeit insgesamt</th></tr>
      <tr><th>Fahrzeit</th><th>Fehlerpunkte</th><th>Gesamt</th><th>Fahrzeit</th><th>Fehlerpunkte</th><th>Gesamt</th><th></th></tr>
    </thead>
    <tbody><tr><td class="rt"></td><td class="rt"></td><td class="rt"></td><td class="rt"></td><td class="rt"></td><td class="rt"></td><td class="rt"></td></tr></tbody>
  </table>
</div>`

  const page2 = `
<div class="page page-break">
  <div class="form-header">
    <div class="form-title" style="font-size:13pt">Haftungsausschluss</div>
  </div>
  <div class="haftung-fields">
    <div><strong>Titel der Veranstaltung:</strong> ${esc(event.name)}</div>
    <div><strong>Name des Fahrers/Bewerbers:</strong> ${esc(p.last_name)}, ${esc(p.first_name)}</div>
  </div>
  <div class="haftung-text">
    <p>Die Teilnehmer nehmen auf eigene Gefahr an den Veranstaltungen teil. Sie tragen die alleinige zivil- und strafrechtliche Verantwortung für alle von ihnen oder dem von ihnen benutzten Fahrzeug verursachten Schäden. Sie erklären den Verzicht auf Ansprüche jeder Art für Schäden, die im Zusammenhang mit der Veranstaltung entstehen, und zwar gegenüber</p>
    <ul>
      <li>den eigenen Teilnehmer (anderslautende Vereinbarungen zwischen den Teilnehmer gehen vor!) und Helfern,</li>
      <li>den jeweils anderen Teilnehmern, den Eigentümern und Haltern aller an der Veranstaltung teilnehmenden Fahrzeuge (soweit die Veranstaltung auf einer permanenten oder temporär geschlossenen Strecke stattfindet) und deren Helfern,</li>
      <li>der FIA, der CIK, dem DMSB, den Mitgliedsorganisationen des DMSB, deren Präsidenten, Organen, Geschäftsführern und Generalsekretären,</li>
      <li>dem ADAC e.V., den ADAC Regionalclubs, den ADAC Ortsclubs und den mit dem ADAC e.V. verbundenen Unternehmen, deren Präsidenten, Organen, Geschäftsführern, Generalsekretären, den Mitarbeitern und Mitgliedern,</li>
      <li>dem Promotor/Serienorganisator,</li>
      <li>dem Veranstalter, den Sportwarten, den Rennstreckeneigentümern, den Rechtsträgern der Behörden, Renndiensten und allen anderen Personen, die mit der Organisation der Veranstaltung in Verbindung stehen,</li>
      <li>den Straßenbaulastträgern und</li>
      <li>der Erfüllungs- und Verrichtungsgehilfen, den gesetzlichen Vertretern, den haupt- und ehrenamtlichen Mitarbeitern aller zuvor genannten Personen und Stellen sowie deren Mitgliedern.</li>
    </ul>
    <p>Der Haftungsverzicht gilt nicht für Schäden aus der Verletzung des Lebens, des Körpers oder der Gesundheit, für sonstige Schäden, die auf einer vorsätzlichen oder grob fahrlässigen Pflichtverletzung beruhen sowie nicht für Schäden aus der Verletzung einer wesentlichen Vertragspflicht durch den enthafteten Personenkreis. Bei Schäden, die auf einer leicht fahrlässigen Pflichtverletzung von wesentlichen Vertragspflichten beruhen ist die Haftung für Vermögens- und Sachschäden der Höhe nach auf den typischen, vorhersehbaren Schaden beschränkt.</p>
    <p>Der Haftungsverzicht gilt für Ansprüche aus jeglichem Rechtsgrund, insbesondere also für Schadensersatzansprüche aus vertraglicher und ausservertraglicher Haftung und für Ansprüche aus unerlaubter Handlung. Stillschweigende Haftungsausschlüsse bleiben von vorstehender Haftungsausschlussklausel unberührt.</p>
    <p>Mit Abgabe der Nennung nimmt der Teilnehmer davon Kenntnis, dass Versicherungsschutz im Rahmen der Kraftverkehrsversicherungen (Kfz-Haftpflicht, Kasko-Versicherung etc.) für Schäden, die im Rahmen der Veranstaltungen entstehen, nicht gewährt wird. Er verpflichtet sich, auch den Halter und den Eigentümer des eingesetzten Fahrzeugs davon zu unterrichten.</p>
    <p>Im Falle einer im Laufe der Veranstaltung eintretenden oder festgestellten Verletzung bzw. im Falle von gesundheitlichen Schäden, die die automobilsportliche Tauglichkeit auf Dauer oder vorübergehend in Frage stellen können, entbindet der Teilnehmer alle behandelnden Ärzte – im Hinblick auf das sich daraus unter Umständen auch für Dritte ergebende Sicherheitsrisiko – von der ärztlichen Schweigepflicht gegenüber dem DMSB, dem ADAC (ADAC e.V., ADAC Regionalverbände und ADAC Ortsclubs) gegenüber den Rennärzten, Slalomleitern, Schiedsgerichten.</p>
    <p><strong>Mit meiner Unterschrift erkenne ich den o.a. Haftungsausschluss an.</strong></p>
  </div>
  <div class="haftung-sig">
    <div class="sig-row">
      <div class="si"><div class="sline-l"></div><div class="sc">Ort</div></div>
      <div class="si"><div class="sline-l"></div><div class="sc">Datum</div></div>
      <div class="si" style="flex:2"><div class="sline-l"></div><div class="sc">Unterschrift Fahrer/Fahrerin</div></div>
    </div>
    <div class="sig-row" style="margin-top:18px">
      <div class="si" style="flex:2"><div class="sline-l"></div><div class="sc">Unterschrift des/der Erziehungsberechtigten</div></div>
      <div class="si" style="flex:1"><div class="sline-l"></div><div class="sc">/</div></div>
    </div>
    <p class="small-note">Bei Unterschrift nur eines Erziehungsberechtigten bestätigt dieser damit, dass er alleiniger Erziehungsberechtigter ist, bzw. dass das Einverständnis des zweiten Elternteils vorliegt. Bei Alleinigem Sorgerecht ist immer eine entsprechende Bescheinigung mitzuführen und auf Verlangen vorzulegen.</p>
    <p class="small-note" style="margin-top:8px">Stand 2024</p>
  </div>
</div>`

  const html = `<!DOCTYPE html><html lang="de"><head><meta charset="UTF-8">
<title>Nennungsformular – ${esc(p.last_name)}, ${esc(p.first_name)}</title>
<style>
  * { box-sizing: border-box; }
  body { font-family: Arial, Helvetica, sans-serif; font-size: 9.5pt; color: #000; margin: 0; }
  @page { size: A4 portrait; margin: 12mm 14mm; }
  .page { padding: 0; }
  .page-break { page-break-before: always; }
  .form-header { text-align: center; border-bottom: 2px solid #000; padding-bottom: 5px; margin-bottom: 8px; }
  .form-title { font-size: 16pt; font-weight: bold; letter-spacing: 1px; }
  .form-subtitle { font-size: 10pt; }
  .section-box { border: 1px solid #888; padding: 5px 8px; margin-bottom: 8px; }
  .section-label { font-size: 8pt; font-weight: bold; margin-bottom: 3px; }
  .va-types { display: flex; gap: 14px; flex-wrap: wrap; margin-bottom: 5px; font-size: 9pt; }
  .va-types label { display: flex; align-items: center; gap: 3px; }
  .ev-row { display: flex; align-items: baseline; gap: 4px; margin-top: 3px; font-size: 9pt; flex-wrap: wrap; }
  .fl { font-size: 8pt; color: #555; white-space: nowrap; }
  .fv { font-weight: bold; border-bottom: 1px solid #555; min-width: 80px; padding: 0 3px; }
  .two-col { display: flex; gap: 10px; margin-bottom: 8px; }
  .pdata { flex: 1; }
  .fr { display: flex; align-items: baseline; gap: 3px; margin-bottom: 4px; flex-wrap: wrap; }
  .lbl { font-size: 8pt; color: #555; white-space: nowrap; }
  .vbox { flex: 1; border-bottom: 1px solid #555; min-width: 60px; font-weight: bold; padding: 0 3px; font-size: 9.5pt; min-height: 14px; }
  .vbox.short { flex: 0 0 60px; min-width: 60px; }
  .vbox-right { width: 145px; border: 1.5px solid #333; padding: 6px 8px; flex-shrink: 0; }
  .vbox-title { font-size: 7.5pt; font-weight: bold; border-bottom: 1px solid #333; padding-bottom: 3px; margin-bottom: 5px; }
  .vr-field { margin-bottom: 5px; }
  .big-lbl { display: block; font-size: 7.5pt; color: #555; font-weight: bold; }
  .big-val { display: block; font-size: 14pt; font-weight: black; border-bottom: 1px solid #555; min-height: 18px; padding: 0 2px; }
  .vr-check { font-size: 8pt; margin-bottom: 4px; }
  .vr-check input[type=checkbox] { margin-right: 3px; }
  .small .lbl { font-size: 8pt; }
  .sline { display: inline-block; border-bottom: 1px solid #555; flex: 1; min-width: 80px; }
  .legal { font-size: 7.5pt; line-height: 1.4; margin-bottom: 8px; border-top: 1px solid #ccc; padding-top: 5px; }
  .legal p { margin: 0 0 4px; }
  .sig-section { margin-bottom: 8px; }
  .sig-row { display: flex; gap: 12px; }
  .si { flex: 1; }
  .sline-l { border-bottom: 1px solid #333; height: 18px; margin-bottom: 2px; }
  .sc { font-size: 7.5pt; color: #555; text-align: center; }
  .res-table { width: 100%; border-collapse: collapse; margin-top: 6px; font-size: 8.5pt; }
  .res-table th { border: 1px solid #888; background: #e8e8e8; padding: 3px 5px; text-align: center; }
  .res-table td { border: 1px solid #bbb; padding: 0; height: 14mm; }
  .rt { text-align: center; }
  .haftung-fields { font-size: 9pt; border: 1px solid #888; padding: 5px 8px; margin-bottom: 8px; display: flex; gap: 20px; }
  .haftung-text { font-size: 8.5pt; line-height: 1.5; }
  .haftung-text p { margin: 0 0 5px; }
  .haftung-text ul { margin: 3px 0 5px 18px; padding: 0; }
  .haftung-text li { margin-bottom: 2px; }
  .haftung-sig { margin-top: 12px; }
  .small-note { font-size: 7.5pt; color: #444; margin-top: 6px; line-height: 1.4; }
</style>
</head><body>${page1}${page2}</body></html>`

  const w = window.open('', '_blank', 'width=900,height=750')
  if (!w) { alert('Popup wurde blockiert – bitte Popups für diese Seite erlauben.'); return }
  w.document.write(html)
  w.document.close()
  w.focus()
  setTimeout(() => w.print(), 400)
}

export async function printNennliste(api, event, classes, participants) {
  let cfg = {}
  try { const { data } = await api.get('/settings/'); cfg = data } catch { /* ignore */ }

  const printDate = new Date().toLocaleString('de-DE', { dateStyle: 'short', timeStyle: 'short' })

  const classPages = classes.map((cls, idx) => {
    const ps = participants
      .filter(p => p.class_id === cls.id)
      .sort((a, b) => (a.start_number ?? 9999) - (b.start_number ?? 9999) || a.last_name.localeCompare(b.last_name))

    const rows = ps.map((p, i) => `
      <tr>
        <td class="center">${i + 1}</td>
        <td class="center mono">${p.start_number ? '#' + p.start_number : '–'}</td>
        <td><strong>${esc(p.last_name)}</strong>, ${esc(p.first_name)}</td>
        <td>${esc(p.club_name || 'n.N.')}</td>
        <td class="center">${p.birth_year || '–'}</td>
        <td class="center check">${p.fee_paid ? '✓' : '□'}</td>
        <td class="center check">${p.helmet_ok ? '✓' : '□'}</td>
        <td class="sig"></td>
      </tr>`).join('')

    return `
      <div class="${idx > 0 ? 'page-break' : ''}">
        <div class="event-header">
          <div>
            <h1>${esc(event.name)}</h1>
            <div class="meta">${esc(event.date.split('-').reverse().join('.'))} · ${esc(event.location || '')}</div>
          </div>
          <div class="org">
            <div>${esc(cfg.organizer_name || '')}</div>
            <div style="font-size:8pt;color:#666">${esc(cfg.organizer_address || '')}</div>
            <div style="font-size:8pt;color:#999;margin-top:4px">Druck: ${printDate}</div>
          </div>
        </div>
        <h2>${esc(cls.name)}</h2>
        <table>
          <thead>
            <tr>
              <th class="center" style="width:24px">Nr.</th>
              <th class="center" style="width:36px">St.Nr.</th>
              <th>Name</th>
              <th style="width:90px">Verein</th>
              <th class="center" style="width:36px">Jg.</th>
              <th class="center" style="width:24px">€</th>
              <th class="center" style="width:28px">Helm</th>
              <th style="width:55mm">Unterschrift Fahrer/Erziehungsber.</th>
            </tr>
          </thead>
          <tbody>${rows || '<tr><td colspan="8" style="text-align:center;color:#999">Keine Teilnehmer</td></tr>'}</tbody>
        </table>
        <div class="footer">
          <p><strong>Versicherungshinweis:</strong> ${esc(cfg.insurance_notice || '')}</p>
          <p style="margin-top:6px"><strong>Einverständniserklärung:</strong> ${esc(cfg.parent_consent_text || '')}</p>
        </div>
      </div>`
  }).join('')

  const html = `<!DOCTYPE html>
<html lang="de"><head><meta charset="UTF-8">
<title>Nennliste – ${esc(event.name)}</title>
<style>
  @page { size: A4 portrait; margin: 12mm 15mm; }
  * { box-sizing: border-box; }
  body { font-family: Arial, Helvetica, sans-serif; font-size: 10pt; color: #222; }
  h1 { font-size: 13pt; margin: 0 0 2px; }
  h2 { font-size: 11pt; margin: 14px 0 6px; border-bottom: 1.5px solid #333; padding-bottom: 3px; }
  .event-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 4px; }
  .meta { font-size: 9pt; color: #555; }
  .org { text-align: right; font-size: 9pt; }
  table { width: 100%; border-collapse: collapse; font-size: 9pt; }
  th { background: #e8e8e8; border: 1px solid #888; padding: 3px 5px; text-align: left; font-size: 8.5pt; }
  td { border: 1px solid #bbb; padding: 3px 5px; vertical-align: middle; }
  .center { text-align: center; }
  .mono { font-family: monospace; font-weight: bold; }
  .check { font-size: 12pt; }
  .sig { height: 10mm; }
  .footer { margin-top: 10px; border-top: 1px solid #ccc; padding-top: 6px; font-size: 8pt; color: #444; }
  .page-break { page-break-before: always; }
</style>
</head><body>${classPages}</body></html>`

  const w = window.open('', '_blank', 'width=900,height=700')
  if (!w) { alert('Popup wurde blockiert – bitte Popups für diese Seite erlauben.'); return }
  w.document.write(html)
  w.document.close()
  w.focus()
  setTimeout(() => w.print(), 400)
}
