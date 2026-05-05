export const esc = (s) =>
  String(s ?? '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')

export function fmtDate(d) {
  if (!d) return ''
  const [y, m, day] = d.split('-')
  return `${day}.${m}.${y}`
}

export function printOpen(title, html) {
  const w = window.open('', '_blank', 'width=1100,height=800')
  if (!w) { alert('Popup wurde blockiert – bitte Popups für diese Seite erlauben.'); return }
  w.document.write(`<!DOCTYPE html><html lang="de"><head>
<meta charset="UTF-8"><title>${esc(title)}</title>
<style>
  * { box-sizing: border-box; }
  body { font-family: Arial, Helvetica, sans-serif; font-size: 10pt; color: #000; margin: 0; }
  .ev-header { border-bottom: 3px solid #1a3fa0; padding-bottom: 6px; margin-bottom: 14px; }
  .ev-header h1 { margin: 0; font-size: 15pt; color: #1a3fa0; letter-spacing: 1px; }
  .ev-header h2 { margin: 2px 0 0; font-size: 10pt; font-weight: normal; color: #444; }
  .ev-header .org { font-size: 8pt; color: #777; margin-top: 2px; }
  .cls-section { margin-bottom: 18px; break-inside: avoid; }
  .cls-header { background: #1a3fa0; color: #fff; font-size: 10pt; font-weight: bold;
                padding: 4px 8px; margin-bottom: 3px; display: flex; align-items: center; gap: 8px; }
  table { width: 100%; border-collapse: collapse; font-size: 8.5pt; }
  th { background: #e8edf6; border: 1px solid #b0b8d0; padding: 3px 5px; font-size: 8pt; }
  td { border: 1px solid #ddd; padding: 2.5px 5px; }
  tr:nth-child(even) td { background: #fafafa; }
  .tr { text-align: right; font-family: 'Courier New', monospace; }
  .rank-1 td { background: #fffce6 !important; }
  .rank-2 td { background: #f5f5f5 !important; }
  .rank-3 td { background: #fdf2e6 !important; }
  .badge { display: inline-block; font-size: 7pt; font-weight: bold; padding: 1px 5px; border-radius: 4px; }
  .b-ok    { background: #d4edda; color: #155724; }
  .b-pre   { background: #fff3cd; color: #856404; }
  .protest { font-size: 7.5pt; color: #777; text-align: right; margin-top: 3px; }
  footer   { position: fixed; bottom: 6px; left: 0; right: 0; text-align: center;
             font-size: 7pt; color: #aaa; border-top: 1px solid #eee; padding-top: 3px; }
</style>
</head><body>${html}</body></html>`)
  w.document.close()
  setTimeout(() => w.print(), 400)
}
