import argparse
import json
import os
import re
import subprocess
import sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IDBRIDGE = os.path.join(ROOT, 'scripts', 'idbridge.py')
FONT_MAP = {}
WEIGHT_CODE = {'Thin': '100', 'ExtraLight': '200', 'Light': '300', 'Regular': '400', 'Medium': '500', 'SemiBold': '600', 'Bold': '700', 'ExtraBold': '800', 'Black': '900'}

def fonts_from_tokens(tokens):
    FONT_MAP.clear()
    for key in ('display', 'body'):
        f = (tokens.get('fonts') or {}).get(key) or {}
        fam = str(f.get('family') or '')
        if not fam:
            continue
        idn = str(f.get('indesign_family') or fam)
        css_names = {fam, fam.replace(' ', ''), str(f.get('css_family') or fam.replace(' ', ''))}
        weights = [str(w) for w in f.get('weights') or ['Regular']]
        for css in css_names:
            FONT_MAP[css] = '%s\t%s' % (idn, weights[0])
            for w in weights:
                code = WEIGHT_CODE.get(w, '')
                if code:
                    FONT_MAP['%s@%s' % (css, code)] = '%s\t%s' % (idn, w)
    return FONT_MAP

def resolve_font(name, weight=None):
    if weight:
        hit = FONT_MAP.get('%s@%s' % (name, weight))
        if hit:
            return hit
    return FONT_MAP.get(name, name)
ALIGN_MAP = {'left': 'LEFT_ALIGN', 'start': 'LEFT_ALIGN', 'right': 'RIGHT_ALIGN', 'end': 'RIGHT_ALIGN', 'center': 'CENTER_ALIGN', 'justify': 'LEFT_JUSTIFIED'}

def idtext(s):
    s = re.sub('[ \\t]+', ' ', s)
    s = re.sub('[ \\t]*\\n[ \\t]*', '\r', s)
    return s.strip()

def rgb(css):
    m = re.findall('[\\d.]+', css or '')
    if not m:
        return None
    v = [float(x) for x in m]
    if len(v) >= 4 and v[3] == 0:
        return None
    return [int(round(v[0])), int(round(v[1])), int(round(v[2]))]

def ex(code, label):
    p = subprocess.run([sys.executable, IDBRIDGE, 'ex', code], capture_output=True, text=True, cwd=ROOT)
    out = (p.stdout or '').strip().splitlines()
    res = out[-1] if out else ''
    if p.returncode != 0 or ('ERROR' in (p.stderr or '').upper() and 'BRIDGE ERROR' in (p.stderr or '')):
        raise RuntimeError('%s FAILED: %s %s' % (label, p.stderr.strip()[:400], res))
    print('  %-22s %s' % (label, res))
    return res

def js_colour_helper():
    return "\n    function swatch(doc, rgbArr, name){\n      if (!rgbArr) return doc.swatches.item(0);\n      var nm = name || ('rgb-' + rgbArr.join('-'));\n      var s = doc.colors.itemByName(nm);\n      if (!s.isValid){ s = doc.colors.add(); s.space = idsn.ColorSpace.RGB; s.colorValue = rgbArr; s.name = nm; }\n      return s;\n    }\n    "

def ground_rect(page_index, doc_name, fill, w, h, colour_names):
    return "\nconst idsn = require('indesign'); const app = idsn.app;\nconst DOC = %s;\nconst doc = app.documents.itemByName(DOC);\nif(!doc.isValid) throw new Error('MY DOC NOT OPEN: ' + DOC);\nconst NAMES = %s;\n%s\nconst pg = doc.pages.item(%d);\nconst pb = pg.bounds; const oy = pb[0], ox = pb[1];\nconst existing = pg.pageItems.itemByName ? null : null;\nfor (let i=pg.pageItems.length-1; i>=0; i--){\n  if (pg.pageItems.item(i).label === 'page-ground') pg.pageItems.item(i).remove();\n}\nconst q = pg.rectangles.add();\nq.geometricBounds = [oy-0.125, ox-0.125, oy+%s+0.125, ox+%s+0.125];\nconst c = %s;\nconst nm = NAMES[c.join(',')] || null;\nq.fillColor = swatch(doc, c, nm);\nq.properties = { strokeColor: 'None', strokeWeight: 0, strokeTint: 0 };\nq.label = 'page-ground';\nq.sendToBack();\nreturn 'ground ' + (nm || c.join(',')) + ' laid + sent to back';" % (json.dumps(doc_name), json.dumps(colour_names), js_colour_helper(), page_index, h, w, json.dumps(fill))

def setup_document(doc_name, cmyk_by_name, ramp_defs, tokens):
    fonts = tokens.get('fonts') or {}
    styles = []
    for name, st in ramp_defs.items():
        f = fonts.get(st.get('font')) or {}
        idn = str(f.get('indesign_family') or f.get('family') or '')
        styles.append({'name': name, 'font': '%s\t%s' % (idn, st.get('weight') or 'Regular'), 'size': float(st.get('size_pt') or 0), 'lead': float(st.get('leading_pt') or 0)})
    return "\nconst idsn = require('indesign'); const app = idsn.app;\nconst doc = app.documents.itemByName(%s);\nif(!doc.isValid) throw new Error('MY DOC NOT OPEN');\nconst SW = %s; const ST = %s; const made = [];\nfor (const nm in SW){ let c = doc.colors.itemByName(nm);\n  if (!c.isValid){ c = doc.colors.add(); c.name = nm; }\n  c.model = idsn.ColorModel.PROCESS; c.space = idsn.ColorSpace.CMYK; c.colorValue = SW[nm]; made.push(nm); }\nfor (const st of ST){ let p = doc.paragraphStyles.itemByName(st.name);\n  if (!p.isValid){ p = doc.paragraphStyles.add(); p.name = st.name; }\n  try { p.appliedFont = app.fonts.itemByName(st.font); } catch(e) {}\n  p.pointSize = String(st.size) + 'pt'; p.leading = String(st.lead) + 'pt'; p.hyphenation = false; }\nreturn 'swatches ' + made.length + ' | styles ' + ST.length;" % (json.dumps(doc_name), json.dumps(cmyk_by_name), json.dumps(styles))
TEXT_LOSS = []

def stale_labels(existing, wanted):
    wanted = set(wanted)
    out = []
    for label in existing:
        if not label or label == 'page-ground':
            continue
        base = re.sub('-\\d+$', '', label)
        if label not in wanted and base not in wanted:
            out.append(label)
    return out

def wipe_stale_script(page_index, doc_name, wanted):
    return "\nconst app = require('indesign').app;\nconst DOC = %s;\nconst doc = app.documents.itemByName(DOC);\nif(!doc.isValid) throw new Error('MY DOC NOT OPEN: ' + DOC);\nconst WANTED = new Set(%s);\nconst pg = doc.pages.item(%d);\nconst gone = [];\nfor (let i = pg.pageItems.length - 1; i >= 0; i--) {\n  const it = pg.pageItems.item(i);\n  const L = String(it.label || '');\n  if (!L || L === 'page-ground') continue;\n  const base = L.replace(/-\\d+$/, '');\n  if (!WANTED.has(L) && !WANTED.has(base)) { gone.push(L); it.remove(); }\n}\nreturn 'stale removed=' + gone.length + (gone.length ? ' (' + gone.join(', ') + ')' : '');" % (json.dumps(doc_name), json.dumps(sorted(set(wanted))), page_index)

def build_frames(frames, page_index, doc_name, assets_dir, colour_names):
    items = []
    for f in frames:
        gb = f['gb']
        entry = {'id': f['id'], 'gb': gb, 'opacity': f.get('opacity', 1)}
        if f.get('img'):
            src = f['img']
            local = os.path.normpath(os.path.join(assets_dir, src)).replace('\\', '/')
            pdf = re.sub('\\.png$', '-print.pdf', local)
            entry['kind'] = 'image'
            entry['src'] = pdf if os.path.exists(pdf) else local
            entry['fill_frame'] = f.get('imgFit') == 'cover'
        elif f.get('runs'):
            entry['kind'] = 'runs'
            entry['runs'] = [{'gb': r['gb'], 'text': idtext(r.get('full') or r['text']), 'font': resolve_font(r['font'], r.get('weight')), 'size': r['sizePt'], 'lead': r['leadPt'], 'track': int(round(r['trackEm'] * 1000)), 'colour': rgb(r['color']), 'align': ALIGN_MAP.get(r['align'], 'LEFT_ALIGN'), 'lines': r['lines'], 'style': r.get('style') or ''} for r in f['runs']]
            _joined = re.sub('\\s+', '', ''.join((r['text'] for r in entry['runs'])))
            _whole = re.sub('\\s+', '', idtext(f.get('full') or f.get('text') or ''))
            if _whole and _joined != _whole:
                TEXT_LOSS.append({'page': page_index + 1, 'id': entry['id'], 'placed_chars': len(_joined), 'expected_chars': len(_whole), 'missing': _whole[len(_joined):][:70] if len(_whole) > len(_joined) else '(reordered/altered)'})
        elif f.get('text'):
            entry['kind'] = 'text'
            entry['text'] = idtext(f.get('full') or f['text'])
            entry['font'] = resolve_font(f['font'], f.get('weight'))
            entry['size'] = f['sizePt']
            entry['lead'] = f['leadPt']
            entry['track'] = int(round(f['trackEm'] * 1000))
            entry['colour'] = rgb(f['color'])
            entry['align'] = ALIGN_MAP.get(f['align'], 'LEFT_ALIGN')
            entry['lines'] = f['lines']
            entry['style'] = f.get('style') or ''
        else:
            entry['kind'] = 'rect'
            entry['fill'] = rgb(f.get('bg'))
            if entry['fill'] is None:
                continue
        items.append(entry)
    payload = json.dumps(items)
    names = json.dumps(colour_names)
    return "\nconst idsn = require('indesign'); const app = idsn.app;\nconst DOC = %s;\nconst doc = app.documents.itemByName(DOC);\nif(!doc.isValid) throw new Error('MY DOC NOT OPEN: ' + DOC);\nconst NAMES = %s;\n%s\nconst pg = doc.pages.item(%d);\nconst pb = pg.bounds;               // page-local -> spread coords for facing docs\nconst oy = pb[0], ox = pb[1];\nconst ITEMS = %s;\nconst NONE = doc.swatches.item(0);\nfunction shift(gb){ return [oy+gb[0], ox+gb[1], oy+gb[2], ox+gb[3]]; }\nfunction nameFor(c){ if(!c) return null; const k = c.join(','); return NAMES[k] || null; }\nfunction noStroke(it){ it.properties = { strokeColor: 'None', strokeWeight: 0, strokeTint: 0 }; }\nfunction wipe(label){\n  for (let i=pg.pageItems.length-1;i>=0;i--){\n    const L = String(pg.pageItems.item(i).label || '');\n    if (L === label || L.indexOf(label + '-') === 0) pg.pageItems.item(i).remove();\n  }\n}\nfunction mkText(gb, r, label){\n  const tf = pg.textFrames.add();\n  tf.geometricBounds = shift(gb);\n  tf.fillColor = NONE; noStroke(tf); tf.label = label;\n  const tp = tf.textFramePreferences;\n  tp.insetSpacing=[0,0,0,0];\n  tp.verticalJustification = idsn.VerticalJustification.TOP_ALIGN;\n  tp.firstBaselineOffset = idsn.FirstBaseline.ASCENT_OFFSET;\n  tp.autoSizingReferencePoint = idsn.AutoSizingReferenceEnum.TOP_LEFT_POINT;\n  tp.autoSizingType = idsn.AutoSizingTypeEnum.HEIGHT_ONLY;\n  tf.contents = r.text;\n  const ps = r.style ? doc.paragraphStyles.itemByName(r.style) : null;\n  for (let i=0;i<tf.paragraphs.length;i++){\n    const p = tf.paragraphs.item(i);\n    if (ps && ps.isValid) { p.appliedParagraphStyle = ps; }\n    else { p.appliedFont = app.fonts.itemByName(r.font); }\n    if (!(ps && ps.isValid)) { p.pointSize = String(r.size) + 'pt'; p.leading = String(r.lead) + 'pt'; }\n    p.tracking = r.track;   // tracking is unitless (1/1000 em), no suffix\n    p.justification = idsn.Justification[r.align];\n    p.hyphenation = false;\n    p.fillColor = swatch(doc, r.colour, nameFor(r.colour));\n  }\n  return tf;\n}\nconst report = [];\nfor (const it of ITEMS){\n  wipe(it.id);                       // idempotent: a partial batch can be re-run safely\n  if (it.kind === 'rect'){\n    const q = pg.rectangles.add();\n    q.geometricBounds = shift(it.gb);\n    q.fillColor = swatch(doc, it.fill, nameFor(it.fill));\n    if (it.opacity < 1) q.transparencySettings.blendingSettings.opacity = it.opacity*100;\n    noStroke(q); q.label = it.id;\n  } else if (it.kind === 'image'){\n    const q = pg.rectangles.add();\n    q.geometricBounds = shift(it.gb);\n    q.fillColor = NONE; noStroke(q); q.label = it.id;\n    app.pdfPlacePreferences.pdfCrop = idsn.PDFCrop.CROP_PDF;\n    q.place(it.src);\n    q.fit(it.fill_frame ? idsn.FitOptions.FILL_PROPORTIONALLY : idsn.FitOptions.PROPORTIONALLY);\n    q.fit(idsn.FitOptions.CENTER_CONTENT);\n    const g = q.allGraphics[0];\n    if (g && Math.abs(g.horizontalScale - g.verticalScale) > 0.01)\n      throw new Error('STRETCHED ARTWORK on ' + it.id);\n    report.push(it.id + ':img' + (g ? ' scale=' + g.horizontalScale.toFixed(2) : ''));\n  } else if (it.kind === 'text'){\n    const tf = mkText(it.gb, it, it.id);\n    if (it.lines === 1 && tf.lines.length !== 1) report.push('!WRAP ' + it.id);\n    if (tf.overflows) report.push('!OVERSET ' + it.id);\n  } else if (it.kind === 'runs'){\n    let n = 0;\n    for (const r of it.runs){\n      const tf = mkText(r.gb, r, it.id + '-' + (++n));\n      if (r.lines === 1 && tf.lines.length !== 1) report.push('!WRAP ' + it.id + '-' + n);\n      if (tf.overflows) report.push('!OVERSET ' + it.id + '-' + n);\n    }\n  }\n}\nreturn 'placed=' + ITEMS.length + (report.length ? ' | ' + report.join(' ; ') : ' | no wrap/overset flags');" % (json.dumps(doc_name), names, js_colour_helper(), page_index, payload)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('html')
    ap.add_argument('--doc', required=True, help='exact InDesign document name')
    ap.add_argument('--tokens', required=True, help='brand-identities/<CLIENT>/<BRAND>/brand-tokens.yaml (the operator-confirmed token file the transfer must match)')
    ap.add_argument('--medium', default='print', help='print (default) or web: which builds the tokens must carry')
    ap.add_argument('--colourway', default='', help='the colourway that leads (must be one the brand declares)')
    ap.add_argument('--batch', type=int, default=14, help='frames per bridge call')
    ap.add_argument('--from-page', type=int, default=1, help='resume at this comp page (1-based) after a bridge timeout; a failed batch rolls back whole, so re-running its page is safe')
    ap.add_argument('--to-page', type=int, default=None, help='last comp page to transfer (1-based, inclusive). With --from-page this re-does ONE corrected page instead of every page after it, which matters when a late copy fix would otherwise re-place 18 pages. Transfer is idempotent (wipe-by-label), so the range is safe.')
    ap.add_argument('--receipt-dir', default='', help='write transfer-receipt.json {tool, doc, pages, placed} and section-calls.json [{section, page, doc, ok}] here')
    a = ap.parse_args()
    src = os.path.abspath(a.html)
    assets_dir = os.path.dirname(src)
    p = subprocess.run([sys.executable, os.path.join(ROOT, 'scripts', 'comp_measure.py'), src, '--out', 'transfer'], capture_output=True, text=True, cwd=ROOT)
    data = json.loads(p.stdout)
    sys.path.insert(0, os.path.join(ROOT, 'scripts'))
    import brand_tokens
    import comp_rules
    tokens = brand_tokens.load(a.tokens)
    _ok, _problems = brand_tokens.verify(tokens, a.medium, a.colourway)
    if not _ok:
        print('REFUSED: the tokens file is not usable for a %s transfer (nothing written):' % a.medium)
        for _pr in _problems:
            print('  - ' + _pr)
        sys.exit(5)
    fonts_from_tokens(tokens)
    brand = {}
    cmyk_by_name = {}
    for e in brand_tokens.all_colour_entries(tokens):
        if e.get('rgb'):
            brand[','.join((str(int(x)) for x in e['rgb']))] = str(e['name'])
            if e.get('cmyk'):
                cmyk_by_name[str(e['name'])] = [float(x) for x in e['cmyk']]
    ramp_styles, fam = comp_rules.ramp_styles(tokens)
    ramp_defs = (tokens.get('type_ramp') or {}).get('styles') or {}
    print('Transferring %d page(s) into %s' % (len(data), a.doc))
    for pgdata in data:
        for f in pgdata.get('frames', []):
            if not f.get('runs'):
                continue
            joined = re.sub('\\s+', '', ''.join((idtext(r.get('full') or r.get('text') or '') for r in f['runs'])))
            whole = re.sub('\\s+', '', idtext(f.get('full') or f.get('text') or ''))
            if whole and joined != whole:
                TEXT_LOSS.append({'page': pgdata['page'], 'id': f.get('id'), 'placed': len(joined), 'expected': len(whole), 'missing': whole[len(joined):][:70] if len(whole) > len(joined) else '(reordered or altered)'})
    OFF = []
    for pgdata in data:
        cols = [('ground', rgb(pgdata.get('pageBg')))]
        for f in pgdata.get('frames', []):
            cols.append((f.get('id'), rgb(f.get('bg'))))
            units = f.get('runs') or ([f] if (f.get('text') or '').strip() else [])
            for u in units:
                cols.append((f.get('id'), rgb(u.get('color'))))
                name, why = comp_rules._style_match(u, ramp_styles, fam)
                if not name:
                    OFF.append('page %s %s: %s' % (pgdata['page'], f.get('id'), why))
                else:
                    u['style'] = name
        for who, c in cols:
            if not c:
                continue
            nm = brand.get(','.join((str(x) for x in c)))
            if not nm:
                nm = brand_tokens.match_rgb(tokens, c)
                if nm:
                    brand[','.join((str(x) for x in c))] = nm
            if not nm:
                OFF.append('page %s %s: rgb(%s) is not a brand token' % (pgdata['page'], who, ','.join((str(x) for x in c))))
            elif nm not in cmyk_by_name:
                OFF.append("page %s %s: %s has no print build in the tokens file (a text variant needs the operator's CMYK)" % (pgdata['page'], who, nm))
    if OFF:
        print('\nREFUSED: the comp is off the brand tokens. Nothing was written.')
        for line in OFF[:40]:
            print('  ' + line)
        sys.exit(4)
    if TEXT_LOSS:
        print("\nREFUSED: a 'runs' frame does not account for its own paragraph text.")
        print('A mixed-weight paragraph (inline <b>/<em> inside body copy) transfers as')
        print('ONE FRAME PER RUN, so the un-emphasised remainder is dropped SILENTLY --')
        print('no overset, no error, and it reaches the exported client PDF.')
        print('Fix the COMP: give the emphasis its own frame (a label), not an inline tag.')
        for t in TEXT_LOSS:
            print('  page %-3s %-10s placed %d of %d chars | missing: %r' % (t['page'], t['id'], t['placed'], t['expected'], t['missing']))
        sys.exit(3)
    ex(setup_document(a.doc, cmyk_by_name, ramp_defs, tokens), 'tokens setup')
    calls, placed_total, pages_done = ([], 0, 0)
    for pgdata in data:
        if pgdata['page'] < a.from_page:
            continue
        if a.to_page is not None and pgdata['page'] > a.to_page:
            continue
        idx = pgdata['page'] - 1
        frames = pgdata['frames']
        print(' page %d: %d frames, trim %s' % (pgdata['page'], len(frames), pgdata['trimIn']))
        ground = rgb(pgdata.get('pageBg'))
        if ground:
            w, h = pgdata['trimIn']
            ex(ground_rect(idx, a.doc, ground, w, h, brand), 'p%d ground' % pgdata['page'])
        ex(wipe_stale_script(idx, a.doc, [f['id'] for f in frames]), 'p%d stale' % pgdata['page'])
        placed_page = 0
        for i in range(0, len(frames), a.batch):
            chunk = frames[i:i + a.batch]
            code = build_frames(chunk, idx, a.doc, assets_dir, brand)
            res = ex(code, 'p%d batch %d' % (pgdata['page'], i // a.batch + 1))
            m = re.search('placed=(\\d+)', str(res))
            placed_page += int(m.group(1)) if m else 0
        calls.append({'section': 'p%02d' % pgdata['page'], 'page': pgdata['page'], 'doc': a.doc, 'frames': len(frames), 'placed': placed_page, 'ok': placed_page >= len(frames)})
        placed_total += placed_page
        pages_done += 1
    print('transfer complete: %d page(s), %d item(s) placed' % (pages_done, placed_total))
    if a.receipt_dir:
        os.makedirs(a.receipt_dir, exist_ok=True)
        with open(os.path.join(a.receipt_dir, 'transfer-receipt.json'), 'w', encoding='utf-8') as f:
            json.dump({'tool': 'comp_to_indesign.py', 'doc': a.doc, 'pages': pages_done, 'placed': placed_total, 'comp': src}, f, indent=1)
        with open(os.path.join(a.receipt_dir, 'section-calls.json'), 'w', encoding='utf-8') as f:
            json.dump(calls, f, indent=1)
        print('receipts written to %s' % a.receipt_dir)
if __name__ == '__main__':
    main()
