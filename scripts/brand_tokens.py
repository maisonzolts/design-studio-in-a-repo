from __future__ import annotations
import argparse
import glob
import json
import os
import re
import sys
import yaml
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(SCRIPT_DIR)
ROLES = ('main', 'secondary', 'accent', 'light', 'neutral', 'dark')

def source_exists(src, root: str='') -> bool:
    s = str(src or '').strip()
    if not s:
        return False
    s = re.split('\\s{2,}\\(|\\s\\(', s)[0].strip()
    if os.path.isabs(s) and os.path.exists(s):
        return True
    if root and os.path.exists(os.path.join(root, s)):
        return True
    return False
_CMYK_K = re.compile('([\\d.]+) ([\\d.]+) ([\\d.]+) ([\\d.]+) k\\b')

class TokensError(ValueError):
    pass

def load(path: str) -> dict:
    with open(path, encoding='utf-8') as f:
        data = yaml.safe_load(f) or {}
    if not isinstance(data, dict):
        raise TokensError('tokens file is not a mapping')
    return data

def _hex(rgb):
    return '#%02x%02x%02x' % tuple((int(x) for x in rgb))

def palette_by_name(tokens: dict) -> dict:
    return {str(p.get('name')): p for p in tokens.get('palette') or [] if isinstance(p, dict)}

def all_colour_entries(tokens: dict) -> list:
    out = []
    for p in tokens.get('palette') or []:
        out.append(p)
    for v in tokens.get('text_variants') or []:
        e = dict(v)
        if 'rgb' not in e and e.get('hex'):
            h = e['hex'].lstrip('#')
            e['rgb'] = [int(h[i:i + 2], 16) for i in (0, 2, 4)]
        out.append(e)
    return out

def rgb_index(tokens: dict) -> dict:
    idx = {}
    for e in all_colour_entries(tokens):
        rgb = e.get('rgb')
        if rgb and len(rgb) == 3:
            idx[','.join((str(int(x)) for x in rgb))] = str(e.get('name'))
    return idx

def match_rgb(tokens: dict, rgb, tolerance: int=3):
    best = None
    for e in all_colour_entries(tokens):
        t = e.get('rgb')
        if not t or len(t) != 3:
            continue
        if all((abs(int(a) - int(b)) <= tolerance for a, b in zip(t, rgb))):
            best = str(e.get('name'))
            break
    return best

def verify(tokens: dict, medium: str, colourway: str='', ramp: str='', scale: str='') -> tuple[bool, list]:
    problems = []
    if not (tokens.get('brand') or '').strip():
        problems.append('brand name missing')
    root = str(tokens.get('sources_root') or '')
    if root and (not os.path.isdir(root)):
        problems.append('sources_root does not exist: %s' % root)
    pal = tokens.get('palette') or []
    if not pal:
        problems.append('palette is empty')
    names = set()
    for p in pal:
        n = str(p.get('name') or '')
        if not n:
            problems.append('a palette entry has no name')
            continue
        names.add(n)
        if not source_exists(p.get('source'), root):
            problems.append('palette %s: source is missing or names no file (%r)' % (n, p.get('source')))
        if not p.get('rgb') or len(p.get('rgb')) != 3:
            problems.append('palette %s has no rgb' % n)
        if p.get('role') not in ROLES:
            problems.append('palette %s has no role (one of %s)' % (n, ', '.join(ROLES)))
        if medium in ('print', 'indesign') and (not p.get('cmyk') or len(p.get('cmyk')) != 4):
            problems.append('palette %s has no print build (cmyk) for a %s job' % (n, medium))
    for v in tokens.get('text_variants') or []:
        if not source_exists(v.get('source'), root):
            problems.append('text variant %s: source is missing or names no file (%r); a derived ink is not a brand colour' % (v.get('name'), v.get('source')))
    ways = [str(w) for w in tokens.get('colourways') or []]
    if colourway:
        if colourway not in ways and colourway not in names:
            problems.append('colourway %r is not one the brand declares (%s)' % (colourway, ', '.join(ways) or 'none'))
    elif len(ways) > 1 and (not (tokens.get('default_colourway') or '').strip()):
        problems.append('the brand offers %d colourways and none was declared for this job' % len(ways))
    fonts = tokens.get('fonts') or {}
    if not fonts.get('display') or not fonts.get('body'):
        problems.append('fonts.display and fonts.body are required')
    tr = tokens.get('type_ramp') or {}
    if ramp:
        if str(tr.get('name') or '') != ramp:
            problems.append('type ramp %r is not the one in the file (%r)' % (ramp, tr.get('name')))
    if not tr.get('styles'):
        problems.append('type_ramp.styles is empty')
    if tr and (not source_exists(tr.get('source'), root)):
        problems.append('type_ramp: source is missing or names no file (it must be measured from a prior deliverable)')
    ss = tokens.get('spacing_scale') or {}
    if scale and str(ss.get('name') or '') != scale:
        problems.append('spacing scale %r is not the one in the file (%r)' % (scale, ss.get('name')))
    if not ss.get('values_in') and (not ss.get('values_px')):
        problems.append('spacing_scale has no values')
    if ss and (not source_exists(ss.get('source'), root)):
        problems.append('spacing_scale: source is missing or names no file (it must be measured from a prior deliverable)')
    for where, blk in (('spacing_scale', ss), ('type_ramp', tr)):
        if blk and blk.get('derived'):
            problems.append('%s is marked derived; derived values are not brand values. Measure it or leave it out.' % where)
    page = (tokens.get('page') or {}).get('print' if medium == 'indesign' else medium) or {}
    if medium in ('print', 'indesign') and (not (page.get('margins_in') and page.get('bleed_in') is not None)):
        problems.append('page.print needs margins_in and bleed_in')
    if page and (not source_exists(page.get('source'), root)):
        problems.append('page.%s: source is missing or names no file' % medium)
    return (not problems, problems)

def extract_palette_from_print_vectors(root: str) -> list:
    import fitz
    out = []
    for way in sorted(os.listdir(root)):
        files = sorted(glob.glob(os.path.join(root, way, '*.pdf')))
        if not files:
            continue
        cmyk, rgb, src = (None, None, None)
        for f in files:
            d = fitz.open(f)
            pg = d[0]
            raw = pg.read_contents().decode('latin-1')
            ks = _CMYK_K.findall(raw)
            fills = [it for it in pg.get_drawings() if it.get('fill')]
            d.close()
            if ks and fills:
                vals = [tuple((round(float(x) * 100) for x in m)) for m in ks]
                cmyk = max(set(vals), key=vals.count)
                rgb = tuple((int(round(x * 255)) for x in fills[0]['fill']))
                src = f
                break
        if cmyk and rgb:
            out.append({'name': way, 'hex': _hex(rgb), 'rgb': list(rgb), 'cmyk': list(cmyk), 'role': '', 'source': os.path.relpath(src, os.path.dirname(root)).replace('\\', '/')})
    return out

def observe_type_in_indesign(doc_path: str) -> dict:
    sys.path.insert(0, SCRIPT_DIR)
    import idbridge
    name = os.path.basename(doc_path)
    js_open = "const idsn=require('indesign'); const app=idsn.app; let d=app.documents.itemByName(%s); const was=d.isValid; if(!was) d=app.open(%s); const hu=d.viewPreferences.horizontalMeasurementUnits, vu=d.viewPreferences.verticalMeasurementUnits, tu=d.viewPreferences.textSizeMeasurementUnits; d.viewPreferences.horizontalMeasurementUnits=idsn.MeasurementUnits.POINTS; d.viewPreferences.verticalMeasurementUnits=idsn.MeasurementUnits.POINTS; d.viewPreferences.textSizeMeasurementUnits=idsn.MeasurementUnits.POINTS; const st=[]; for(let i=0;i<d.paragraphStyles.length;i++){const s=d.paragraphStyles.item(i); try{ st.push({name:s.name, font:String(s.appliedFont.fontFamily), weight:String(s.appliedFont.fontStyleName), size:Number(s.pointSize), leading:String(s.leading), tracking:Number(s.tracking), spaceAfter:Number(s.spaceAfter), spaceBefore:Number(s.spaceBefore)}); }catch(e){} } const sizes={}; for(let i=0;i<d.stories.length;i++){ const s=d.stories.item(i); for(let j=0;j<s.paragraphs.length && j<400;j++){ const p=s.paragraphs.item(j); const ps=Number(p.pointSize); const pt=(ps<3? ps*72: ps); const ldr=parseFloat(p.leading); const ld=isNaN(ldr)? String(p.leading) : ((ldr<5? ldr*72: ldr).toFixed(1)); const k=String(p.appliedFont.fontFamily)+'|'+String(p.appliedFont.fontStyleName)+'|'+pt.toFixed(1)+'|'+ld; sizes[k]=(sizes[k]||0)+1; } } d.viewPreferences.horizontalMeasurementUnits=idsn.MeasurementUnits.INCHES; d.viewPreferences.verticalMeasurementUnits=idsn.MeasurementUnits.INCHES; const mp=d.marginPreferences; const dp=d.documentPreferences; const out={styles:st, sizes:sizes, margins_in:{top:mp.top,bottom:mp.bottom,inside:mp.left,outside:mp.right}, bleed_in:dp.documentBleedTopOffset, pages:d.pages.length, w:dp.pageWidth, h:dp.pageHeight}; d.viewPreferences.horizontalMeasurementUnits=hu; d.viewPreferences.verticalMeasurementUnits=vu; d.viewPreferences.textSizeMeasurementUnits=tu; if(!was) d.close(idsn.SaveOptions.NO); return JSON.stringify(out);" % (json.dumps(name), json.dumps(os.path.abspath(doc_path).replace('\\', '/')))
    raw = str(idbridge.ex(js_open, timeout=180))
    j = raw[raw.find('{'):raw.rfind('}') + 1]
    data = json.loads(j)
    data['source'] = doc_path.replace('\\', '/')
    return data

def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest='cmd', required=True)
    e = sub.add_parser('extract-palette')
    e.add_argument('root')
    e.add_argument('--out', default='')
    o = sub.add_parser('observe-type')
    o.add_argument('indd')
    o.add_argument('--out', default='')
    v = sub.add_parser('verify')
    v.add_argument('tokens')
    v.add_argument('--medium', required=True)
    v.add_argument('--colourway', default='')
    v.add_argument('--ramp', default='')
    v.add_argument('--scale', default='')
    a = ap.parse_args(argv)
    if a.cmd == 'extract-palette':
        pal = extract_palette_from_print_vectors(a.root)
        txt = yaml.safe_dump({'palette': pal}, sort_keys=False, allow_unicode=True)
        if a.out:
            with open(a.out, 'w', encoding='utf-8') as f:
                f.write(txt)
        print(txt)
        return 0
    if a.cmd == 'observe-type':
        data = observe_type_in_indesign(a.indd)
        txt = json.dumps(data, indent=1)
        if a.out:
            with open(a.out, 'w', encoding='utf-8') as f:
                f.write(txt)
        print(txt)
        return 0
    ok, problems = verify(load(a.tokens), a.medium, a.colourway, a.ramp, a.scale)
    print('OK' if ok else 'REFUSED')
    for p in problems:
        print('  - ' + p)
    return 0 if ok else 2
if __name__ == '__main__':
    sys.exit(main())
