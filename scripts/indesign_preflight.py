import json
import os
import subprocess
import sys
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_STYLES = ('[no paragraph style]', '[basic paragraph]')
BODY_WORDS = 40
LOCAL_FORMAT_MAX = 0.2
OFF_PAGE_TOL = 0.05
FACTS_JS = '\nvar idn=require("indesign"), app=idn.app;\nvar NAME=%s;\nvar d=app.documents.itemByName(NAME);\nif(!d||!d.isValid){ throw new Error("preflight: document not open: "+NAME); }\nvar out={name:d.name, pages:d.pages.length,\n         pw:d.documentPreferences.pageWidth, ph:d.documentPreferences.pageHeight,\n         paragraph_styles:[], layers:[], swatches:[], frames:[]};\nfor(var i=0;i<d.paragraphStyles.length;i++){ out.paragraph_styles.push(d.paragraphStyles.item(i).name); }\nfor(var i=0;i<d.layers.length;i++){ out.layers.push(d.layers.item(i).name); }\nfor(var i=0;i<d.swatches.length;i++){ var s=d.swatches.item(i); var sp="";\n  try{ sp=String(s.space); }catch(e){ sp=""; }\n  out.swatches.push({name:s.name, space:sp}); }\nfor(var p=0;p<d.pages.length;p++){\n  var pg=d.pages.item(p), pb=pg.bounds, tfs=pg.textFrames;\n  for(var i=0;i<tfs.length;i++){\n    var tf=tfs.item(i), g=tf.geometricBounds, c="", st="", nxt=false, prv=false, fill="", fsp="";\n    try{ c=tf.contents; }catch(e){ c=""; } if(typeof c!=="string") c="";\n    try{ st=tf.paragraphs.length? String(tf.paragraphs.item(0).appliedParagraphStyle.name):""; }catch(e){ st=""; }\n    try{ nxt=tf.nextTextFrame&&tf.nextTextFrame.isValid; }catch(e){ nxt=false; }\n    try{ prv=tf.previousTextFrame&&tf.previousTextFrame.isValid; }catch(e){ prv=false; }\n    try{ var fc=tf.fillColor; fill=fc?String(fc.name):""; fsp=fc?String(fc.space):""; }catch(e){}\n    out.frames.push({page:p+1, gb:[g[0]-pb[0], g[1]-pb[1], g[2]-pb[0], g[3]-pb[1]],\n      words:c.split(/\\s+/).filter(function(w){return w.length;}).length,\n      style:st, next:!!nxt, prev:!!prv, fill:fill, fill_space:fsp, over:tf.overflows});\n  }\n}\nreturn JSON.stringify(out);'

def facts(doc_name: str, timeout: int=120) -> dict:
    js = FACTS_JS % json.dumps(os.path.basename(doc_name))
    p = subprocess.run([sys.executable, os.path.join(SCRIPT_DIR, 'idbridge.py'), 'ex', js], capture_output=True, text=True, timeout=timeout)
    for line in reversed((p.stdout or '').strip().splitlines()):
        line = line.strip()
        if line.startswith('{'):
            return json.loads(line)
    raise RuntimeError('idbridge returned no facts: %s' % ((p.stdout or '')[-300:] or (p.stderr or '')[-300:]))

def judge(f: dict, medium: str='print', waivers: dict | None=None, pages: list | None=None) -> dict:
    waivers = waivers or {}
    rep = {'verdict': 'pass', 'blocking': [], 'warnings': [], 'notes': [], 'examined': 0}
    frames = f.get('frames') or []
    if pages:
        want = {int(p) for p in pages}
        frames = [x for x in frames if int(x.get('page') or 0) in want]
        rep['notes'].append('scoped to page(s) %s (revise job: untouched pages not measured)' % sorted(want))
    text_frames = [x for x in frames if int(x.get('words') or 0) > 0]
    rep['examined'] = len(frames)
    if not frames:
        rep['verdict'] = 'unverifiable'
        rep['blocking'].append({'rule': 'zero_frames', 'why': 'no frames examined; measuring nothing is not measuring clean'})
        return rep

    def hit(rule, why):
        if rule in waivers:
            rep['warnings'].append({'rule': rule, 'why': why, 'waived': waivers[rule]})
        else:
            rep['blocking'].append({'rule': rule, 'why': why})
    custom = [s for s in f.get('paragraph_styles') or [] if s.strip().lower() not in DEFAULT_STYLES]
    on_default = [x for x in text_frames if (x.get('style') or '').strip().lower() in DEFAULT_STYLES or not x.get('style')]
    if text_frames:
        share = len(on_default) / float(len(text_frames))
        if not custom:
            hit('type_system', 'no paragraph styles beyond the defaults; %d text frames are locally formatted (change the body size and you touch every frame by hand)' % len(text_frames))
        elif share > LOCAL_FORMAT_MAX:
            hit('type_system', '%d of %d text frames (%.0f%%) sit on a default style instead of the type system' % (len(on_default), len(text_frames), share * 100))
        else:
            rep['notes'].append('type system: %d styles, %d of %d frames on them' % (len(custom), len(text_frames) - len(on_default), len(text_frames)))
    body = [x for x in text_frames if int(x.get('words') or 0) >= BODY_WORDS]
    body_pages = {x.get('page') for x in body}
    if len(body) >= 2 and len(body_pages) >= 2:
        threaded = [x for x in body if x.get('next') or x.get('prev')]
        if not threaded:
            hit('threaded_body', '%d body frames across %d pages and none is threaded (body copy is one story; titles and captions are the discrete frames)' % (len(body), len(body_pages)))
        else:
            rep['notes'].append('threading: %d of %d body frames threaded' % (len(threaded), len(body)))
    if (medium or '').lower() in ('print', 'indesign'):
        rgb = [s.get('name') for s in f.get('swatches') or [] if 'rgb' in str(s.get('space') or '').lower() and (not str(s.get('name', '')).startswith(('[', 'Paper', 'Registration')))]
        used_rgb = [x for x in frames if 'rgb' in str(x.get('fill_space') or '').lower()]
        if rgb or used_rgb:
            hit('rgb_on_print', '%d RGB swatch(es) on a print job (%s); waive only when the piece is mostly presented on screen, and say so' % (len(rgb), ', '.join(map(str, rgb[:6]))))
    pw, ph = (float(f.get('pw') or 0), float(f.get('ph') or 0))
    off = []
    if pw and ph:
        for x in frames:
            t, l, b, r = [float(v) for v in x.get('gb') or [0, 0, 0, 0]]
            if r < -OFF_PAGE_TOL or l > pw + OFF_PAGE_TOL or b < -OFF_PAGE_TOL or (t > ph + OFF_PAGE_TOL):
                off.append(x)
    if off:
        pages = sorted({x.get('page') for x in off})
        hit('off_page_content', "%d frame(s) lie outside their own page rectangle on page(s) %s (the facing-pages offset trap: a recto's content placed with a verso's origin)" % (len(off), pages))
    layers = f.get('layers') or []
    if len(layers) == 1:
        rep['notes'].append('one working layer (%s)' % layers[0])
    if rep['blocking']:
        rep['verdict'] = 'block'
    return rep

def preflight(doc_name: str, medium: str='print', waivers: dict | None=None, pages: list | None=None) -> dict:
    try:
        f = facts(doc_name)
    except Exception as e:
        return {'verdict': 'unverifiable', 'blocking': [{'rule': 'bridge', 'why': str(e)}], 'warnings': [], 'notes': [], 'examined': 0}
    rep = judge(f, medium, waivers, pages=pages)
    rep['doc'] = f.get('name', doc_name)
    return rep

def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('doc', help="open document name, e.g. 'Brand - Proposal - V1.indd'")
    ap.add_argument('--medium', default='print')
    a = ap.parse_args()
    rep = preflight(a.doc, a.medium)
    print(json.dumps(rep, indent=2))
    return {'pass': 0, 'block': 1, 'unverifiable': 2}[rep['verdict']]
if __name__ == '__main__':
    sys.exit(main())
