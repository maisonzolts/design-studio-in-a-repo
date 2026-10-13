import argparse
import json
import os
import sys
from playwright.sync_api import sync_playwright
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'scripts', 'temp_vision')
PROBE = '\n() => {\n  const IN = 96;\n  const r = el => { const b = el.getBoundingClientRect(); const p = el.closest(\'.page\').getBoundingClientRect();\n    return [ +((b.top-p.top)/IN).toFixed(4), +((b.left-p.left)/IN).toFixed(4),\n             +((b.bottom-p.top)/IN).toFixed(4), +((b.right-p.left)/IN).toFixed(4) ]; };\n  const pages = [...document.querySelectorAll(\'.page\')];\n  return pages.map((pg, pi) => {\n    const frames = [...pg.querySelectorAll(\'.f\')];\n    const boxes = frames.map(el => {\n      const b = el.getBoundingClientRect();\n      const cs = getComputedStyle(el);\n      const lh = parseFloat(cs.lineHeight) || parseFloat(cs.fontSize) * 1.2;\n      const txt = el.innerText ? el.innerText.trim() : \'\';\n      const lines = txt ? Math.round(b.height / lh) : 0;\n      const words = txt ? txt.split(/\\s+/) : [];\n      const img = el.querySelector(\'img\');\n      const kids = [...el.children].filter(c => c.tagName !== \'IMG\' && c.innerText);\n      const runs = kids.map(c => {\n        const kb = c.getBoundingClientRect(); const kc = getComputedStyle(c);\n        const klh = parseFloat(kc.lineHeight) || parseFloat(kc.fontSize) * 1.2;\n        return { gb: r(c), text: c.innerText.trim(), full: c.innerText.trim(),\n                 font: kc.fontFamily.split(\',\')[0].replace(/["\']/g,\'\'),\n                 weight: String(kc.fontWeight || \'400\'),\n                 sizePt: +(parseFloat(kc.fontSize)*0.75).toFixed(2),\n                 leadPt: +(klh*0.75).toFixed(2),\n                 trackEm: kc.letterSpacing === \'normal\' ? 0\n                          : +(parseFloat(kc.letterSpacing)/parseFloat(kc.fontSize)).toFixed(3),\n                 color: kc.color, align: kc.textAlign,\n                 lines: Math.round(kb.height/klh) };\n      });\n      return {\n        id: el.id || el.className,\n        role: el.dataset.role || null,\n        anchor: el.dataset.anchor || null,\n        gb: r(el),\n        bg: cs.backgroundColor,\n        opacity: +cs.opacity,\n        img: img ? img.getAttribute(\'src\') : null,\n        imgFit: img ? getComputedStyle(img).objectFit : null,\n        imgPos: img ? getComputedStyle(img).objectPosition : null,\n        runs: runs,\n        wIn: +(b.width/IN).toFixed(4), hIn: +(b.height/IN).toFixed(4),\n        font: cs.fontFamily.split(\',\')[0].replace(/["\']/g,\'\'),\n        weight: String(cs.fontWeight || \'400\'),\n        sizePt: +(parseFloat(cs.fontSize)*0.75).toFixed(2),\n        leadPt: +(lh*0.75).toFixed(2),\n        trackEm: cs.letterSpacing === \'normal\' ? 0\n                 : +(parseFloat(cs.letterSpacing)/parseFloat(cs.fontSize)).toFixed(3),\n        color: cs.color,\n        align: cs.textAlign,\n        lines: lines,\n        tail: words.length ? words[words.length-1] : \'\',\n        runt: (lines > 1 && words.length && words[words.length-1].length <= 4) ? words[words.length-1] : null,\n        overflowY: el.scrollHeight - el.clientHeight,\n        full: txt,\n        text: txt.slice(0, 120)\n      };\n    });\n    const ov = [];\n    for (let i=0;i<frames.length;i++) for (let j=i+1;j<frames.length;j++) {\n      if (!boxes[i].text || !boxes[j].text) continue;\n      const a=frames[i].getBoundingClientRect(), b=frames[j].getBoundingClientRect();\n      const w=Math.min(a.right,b.right)-Math.max(a.left,b.left);\n      const h=Math.min(a.bottom,b.bottom)-Math.max(a.top,b.top);\n      if (w>0.5 && h>0.5) ov.push([boxes[i].id, boxes[j].id, +(w).toFixed(1), +(h).toFixed(1)]);\n    }\n    return {\n      page: pi+1,\n      id: pg.id || null,\n      pageBg: getComputedStyle(pg).backgroundColor,\n      trimIn: [+(pg.clientWidth/IN).toFixed(4), +(pg.clientHeight/IN).toFixed(4)],\n      overflow: pg.scrollHeight - pg.clientHeight,\n      overflowX: pg.scrollWidth - pg.clientWidth,\n      overlaps: ov,\n      frames: boxes\n    };\n  });\n}'

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('html')
    ap.add_argument('--out', default=None, help='basename for the PNGs')
    ap.add_argument('--scale', type=int, default=2, help='deviceScaleFactor for LOOKING only')
    a = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    src = os.path.abspath(a.html)
    name = a.out or os.path.splitext(os.path.basename(src))[0]
    with sync_playwright() as p:
        br = p.chromium.launch()
        pg = br.new_page(viewport={'width': 1600, 'height': 1200}, device_scale_factor=a.scale)
        pg.goto('file:///' + src.replace('\\', '/'))
        pg.wait_for_timeout(700)
        try:
            pg.evaluate('document.fonts.ready')
            pg.wait_for_timeout(300)
        except Exception:
            pass
        data = pg.evaluate(PROBE)
        shots = []
        for i, el in enumerate(pg.query_selector_all('.page')):
            f = os.path.join(OUT, '%s_p%02d.png' % (name, i + 1))
            el.screenshot(path=f)
            shots.append(f)
        br.close()
    for d in data:
        d['png'] = shots[d['page'] - 1] if d['page'] - 1 < len(shots) else None
    print(json.dumps(data, indent=1))
    bad = [d['page'] for d in data if d['overflow'] or d['overflowX']]
    ov = [(d['page'], d['overlaps']) for d in data if d['overlaps']]
    fo = [(d['page'], f['id']) for d in data for f in d['frames'] if f['overflowY'] > 0]
    sys.stderr.write('\n== %s: %d page(s) ==' % (name, len(data)))
    sys.stderr.write('page overflow: %s' % (bad or 'CLEAN (0)'))
    sys.stderr.write('frame overset: %s' % (fo or 'CLEAN (0)'))
    sys.stderr.write('overlaps:      %s' % (ov or 'CLEAN (0)'))
    sys.stderr.write('pngs: %s' % '\n      '.join(shots))
    return 1 if bad or ov or fo else 0
if __name__ == '__main__':
    sys.exit(main())
