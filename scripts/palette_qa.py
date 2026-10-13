from __future__ import annotations
import argparse
import json
import math
import sys
AA_NORMAL = 4.5
AA_LARGE = 3.0
AAA_NORMAL = 7.0
AAA_LARGE = 4.5

def parse_hex(h: str) -> tuple[int, int, int]:
    h = h.strip().lstrip('#')
    if len(h) == 3:
        h = ''.join((c * 2 for c in h))
    if len(h) != 6:
        raise ValueError('bad hex: %r' % h)
    return tuple((int(h[i:i + 2], 16) for i in (0, 2, 4)))

def to_hex(rgb: tuple[int, int, int]) -> str:
    return '#%02X%02X%02X' % rgb

def _chan_lin(c8: int) -> float:
    c = c8 / 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

def rel_luminance(rgb: tuple[int, int, int]) -> float:
    r, g, b = (_chan_lin(c) for c in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b

def contrast_ratio(fg: tuple[int, int, int], bg: tuple[int, int, int]) -> float:
    l1, l2 = (rel_luminance(fg), rel_luminance(bg))
    if l1 < l2:
        l1, l2 = (l2, l1)
    return (l1 + 0.05) / (l2 + 0.05)

def _srgb_to_xyz(rgb):
    r, g, b = (_chan_lin(c) for c in rgb)
    return (0.4124564 * r + 0.3575761 * g + 0.1804375 * b, 0.2126729 * r + 0.7151522 * g + 0.072175 * b, 0.0193339 * r + 0.119192 * g + 0.9503041 * b)
_WHITE = (0.95047, 1.0, 1.08883)

def _f(t):
    return t ** (1 / 3) if t > (6 / 29) ** 3 else t / (3 * (6 / 29) ** 2) + 4 / 29

def _finv(t):
    return t ** 3 if t > 6 / 29 else 3 * (6 / 29) ** 2 * (t - 4 / 29)

def rgb_to_lch(rgb):
    x, y, z = _srgb_to_xyz(rgb)
    fx, fy, fz = (_f(x / _WHITE[0]), _f(y / _WHITE[1]), _f(z / _WHITE[2]))
    L = 116 * fy - 16
    a = 500 * (fx - fy)
    b = 200 * (fy - fz)
    C = math.hypot(a, b)
    h = math.degrees(math.atan2(b, a)) % 360
    return (L, C, h)

def lch_to_rgb(L, C, h):
    a = C * math.cos(math.radians(h))
    b = C * math.sin(math.radians(h))
    fy = (L + 16) / 116
    fx, fz = (fy + a / 500, fy - b / 200)
    x, y, z = (_WHITE[0] * _finv(fx), _WHITE[1] * _finv(fy), _WHITE[2] * _finv(fz))
    rl = 3.2404542 * x - 1.5371385 * y - 0.4985314 * z
    gl = -0.969266 * x + 1.8760108 * y + 0.041556 * z
    bl = 0.0556434 * x - 0.2040259 * y + 1.0572252 * z

    def enc(c):
        c = max(0.0, min(1.0, c))
        return 12.92 * c if c <= 0.0031308 else 1.055 * c ** (1 / 2.4) - 0.055
    in_gamut = all((-0.001 <= c <= 1.001 for c in (rl, gl, bl)))
    rgb = tuple((round(enc(c) * 255) for c in (rl, gl, bl)))
    return (rgb, in_gamut)

def _lch_to_rgb_gamut(L, C, h):
    lo, hi = (0.0, C)
    rgb, ok = lch_to_rgb(L, C, h)
    if ok:
        return rgb
    for _ in range(20):
        mid = (lo + hi) / 2
        rgb, ok = lch_to_rgb(L, mid, h)
        if ok:
            lo = mid
        else:
            hi = mid
    rgb, _ = lch_to_rgb(L, lo, h)
    return rgb

def suggest_fix(fg: tuple[int, int, int], bg: tuple[int, int, int], target: float=AA_NORMAL):
    L0, C0, h0 = rgb_to_lch(fg)
    bg_lum = rel_luminance(bg)
    directions = (1, -1) if rel_luminance(fg) >= bg_lum else (-1, 1)
    best = None
    for direction in directions:
        lo, hi = (L0, 100.0) if direction > 0 else (0.0, L0)
        ext_rgb = _lch_to_rgb_gamut(hi if direction > 0 else lo, C0, h0)
        if contrast_ratio(ext_rgb, bg) < target:
            continue
        for _ in range(28):
            mid = (lo + hi) / 2
            rgb = _lch_to_rgb_gamut(mid, C0, h0)
            if contrast_ratio(rgb, bg) >= target:
                if direction > 0:
                    hi = mid
                else:
                    lo = mid
            elif direction > 0:
                lo = mid
            else:
                hi = mid
        L_final = hi if direction > 0 else lo
        rgb = _lch_to_rgb_gamut(L_final, C0, h0)
        ratio = contrast_ratio(rgb, bg)
        if ratio >= target:
            move = abs(L_final - L0)
            if best is None or move < best[2]:
                best = (rgb, ratio, move)
    if best is None:
        return None
    return (best[0], best[1])

def verdict(ratio: float, large: bool) -> str:
    aa = AA_LARGE if large else AA_NORMAL
    aaa = AAA_LARGE if large else AAA_NORMAL
    if ratio >= aaa:
        return 'AAA'
    if ratio >= aa:
        return 'AA'
    return 'FAIL'

def run_qa(palette: dict[str, str], light_bg: str, dark_bg: str, large: bool):
    names = list(palette)
    rgbs = {n: parse_hex(palette[n]) for n in names}
    modes = [('LIGHT MODE (bg %s)' % light_bg, parse_hex(light_bg)), ('DARK MODE (bg %s)' % dark_bg, parse_hex(dark_bg))]
    aa = AA_LARGE if large else AA_NORMAL
    report = {'palette': palette, 'large_text': large, 'modes': []}
    for label, bg in modes:
        rows = []
        for n in names:
            ratio = contrast_ratio(rgbs[n], bg)
            row = {'fg': n, 'hex': to_hex(rgbs[n]), 'ratio': round(ratio, 2), 'verdict': verdict(ratio, large)}
            if ratio < aa:
                fix = suggest_fix(rgbs[n], bg, aa)
                if fix:
                    row['suggestion'] = {'hex': to_hex(fix[0]), 'ratio': round(fix[1], 2), 'note': 'same hue, lightness adjusted (LCh)'}
                else:
                    row['suggestion'] = None
            rows.append(row)
        report['modes'].append({'mode': label, 'bg': to_hex(bg), 'pairs': rows})
    intra = []
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            ratio = contrast_ratio(rgbs[a], rgbs[b])
            row = {'pair': '%s on %s' % (a, b), 'ratio': round(ratio, 2), 'verdict': verdict(ratio, large)}
            if ratio < aa:
                fix = suggest_fix(rgbs[a], rgbs[b], aa)
                if fix:
                    row['suggestion'] = {'fg': a, 'hex': to_hex(fix[0]), 'ratio': round(fix[1], 2), 'note': 'same hue, lightness adjusted (LCh)'}
            intra.append(row)
    report['intra_palette'] = intra
    return report

def print_report(report):
    print('PALETTE QA — WCAG 2.x contrast (%s text thresholds)' % ('large' if report['large_text'] else 'normal'))
    for c, h in report['palette'].items():
        print('  %s %s' % (h, c))
    for mode in report['modes']:
        print('\n%s' % mode['mode'])
        for r in mode['pairs']:
            line = '  %-6s %5.2f  %s (%s)' % (r['verdict'], r['ratio'], r['fg'], r['hex'])
            print(line)
            if r.get('suggestion'):
                s = r['suggestion']
                print('         -> suggest %s (ratio %.2f, %s)' % (s['hex'], s['ratio'], s['note']))
            elif r['verdict'] == 'FAIL' and r.get('suggestion', 'x') is None:
                print('         -> no hue-preserving fix reaches target; flag to the operator')
    print('\nINTRA-PALETTE PAIRS')
    for r in report['intra_palette']:
        print('  %-6s %5.2f  %s' % (r['verdict'], r['ratio'], r['pair']))
        if r.get('suggestion'):
            s = r['suggestion']
            print('         -> suggest %s for %s (ratio %.2f, %s)' % (s['hex'], s['fg'], s['ratio'], s['note']))
    fails = sum((1 for m in report['modes'] for r in m['pairs'] if r['verdict'] == 'FAIL'))
    fails += sum((1 for r in report['intra_palette'] if r['verdict'] == 'FAIL'))
    print('\nRESULT: %s' % ('ALL PASS' if fails == 0 else '%d failing pair(s) — see suggestions' % fails))

def main(argv=None) -> int:
    p = argparse.ArgumentParser(description='WCAG palette QA with hue-preserving suggestions.')
    p.add_argument('--colors', help='e.g. "Ink=#1A1A2E,Sage=#9CAF88" (names optional: "#1A1A2E,#9CAF88")')
    p.add_argument('--colors-file', help='JSON dict {name: hex} or list [hex,...]')
    p.add_argument('--light', default='#FFFFFF', help='light-mode background (default #FFFFFF)')
    p.add_argument('--dark', default='#111111', help='dark-mode background (default #111111)')
    p.add_argument('--large', action='store_true', help='use large-text thresholds (3.0/4.5)')
    p.add_argument('--json', action='store_true', help='emit JSON instead of the table')
    args = p.parse_args(argv)
    palette: dict[str, str] = {}
    if args.colors_file:
        with open(args.colors_file, encoding='utf-8') as f:
            data = json.load(f)
        if isinstance(data, dict):
            palette = {str(k): str(v) for k, v in data.items()}
        else:
            palette = {'Colour %d' % (i + 1): str(v) for i, v in enumerate(data)}
    elif args.colors:
        for i, part in enumerate(args.colors.split(',')):
            part = part.strip()
            if not part:
                continue
            if '=' in part:
                name, hexv = part.split('=', 1)
            else:
                name, hexv = ('Colour %d' % (i + 1), part)
            palette[name.strip()] = hexv.strip()
    if not palette:
        p.error('provide --colors or --colors-file')
    report = run_qa(palette, args.light, args.dark, args.large)
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print_report(report)
    return 0
if __name__ == '__main__':
    sys.exit(main())
