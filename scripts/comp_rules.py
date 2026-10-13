from __future__ import annotations
COLOUR_TOL = 3
SIZE_TOL_PT = 0.6
LEAD_TOL_PT = 1.2
GAP_TOL_IN = 0.03
ALIGN_TOL_IN = 0.04
EDGE_TOL_IN = 0.06
TINY_VISUAL_IN = 1.0
FILL_ROLES = {'ground', 'plate', 'panel', 'rule'}
TYPE_ROLES = {'display', 'title', 'heading', 'subhead', 'kicker', 'label', 'eyebrow', 'deck', 'body', 'list', 'caption', 'folio', 'pull', 'number', 'label-of'}
VISUAL_ROLES = {'figure'}
EXEMPT_TINY = {'decor', 'icon-scale', 'rule', 'ground', 'plate', 'panel'}
STRUCTURAL = {'folio', 'eyebrow', 'title'}
KNOWN = FILL_ROLES | TYPE_ROLES | VISUAL_ROLES | EXEMPT_TINY | {'anchor'}
WEIGHT_NAMES = {'100': 'Thin', '200': 'ExtraLight', '300': 'Light', '400': 'Regular', '500': 'Medium', '600': 'SemiBold', '700': 'Bold', '800': 'ExtraBold', '900': 'Black', 'normal': 'Regular', 'bold': 'Bold'}

def _defect(rule, page, detail, subjects=()):
    return {'rule': rule, 'severity': 'defect', 'page': page, 'detail': detail, 'subjects': list(subjects)}

def _rgb(css):
    if not css:
        return None
    nums = [float(x) for x in ''.join((c if c in '0123456789.' else ' ' for c in str(css))).split()]
    if len(nums) >= 4 and nums[3] == 0:
        return None
    if len(nums) < 3:
        return None
    return [int(round(v)) for v in nums[:3]]

def token_colours(tokens: dict) -> dict:
    out = {}
    for p in tokens.get('palette') or []:
        if p.get('rgb'):
            out[str(p['name'])] = [int(x) for x in p['rgb']]
    for v in tokens.get('text_variants') or []:
        rgb = v.get('rgb')
        if not rgb and v.get('hex'):
            h = str(v['hex']).lstrip('#')
            rgb = [int(h[i:i + 2], 16) for i in (0, 2, 4)]
        if rgb:
            out[str(v['name'])] = [int(x) for x in rgb]
    return out

def match_colour(rgb, colours: dict):
    for name, t in colours.items():
        if all((abs(a - b) <= COLOUR_TOL for a, b in zip(rgb, t))):
            return name
    return None

def ramp_styles(tokens: dict) -> list:
    fonts = tokens.get('fonts') or {}
    fam = {}
    for key in ('display', 'body'):
        f = fonts.get(key) or {}
        for n in (f.get('family'), f.get('indesign_family'), f.get('css_family')):
            if n:
                fam[str(n).replace(' ', '').lower()] = key
    out = []
    for name, st in ((tokens.get('type_ramp') or {}).get('styles') or {}).items():
        out.append((name, st.get('font'), str(st.get('weight') or 'Regular'), float(st.get('size_pt') or 0), float(st.get('leading_pt') or 0)))
    return (out, fam)

def _style_match(fr, styles, fam):
    family = str(fr.get('font') or '').replace('"', '').replace("'", '').replace(' ', '').lower()
    key = fam.get(family)
    if key is None:
        return (None, 'font %r is not a brand font' % fr.get('font'))
    weight = WEIGHT_NAMES.get(str(fr.get('weight') or '400'), str(fr.get('weight')))
    size, lead = (float(fr.get('sizePt') or 0), float(fr.get('leadPt') or 0))
    for name, fkey, w, s, ld in styles:
        if fkey == key and w.lower() == weight.lower() and (abs(s - size) <= SIZE_TOL_PT) and (abs(ld - lead) <= LEAD_TOL_PT):
            return (name, '')
    return (None, '%s %s %.1fpt/%.1fpt is not a declared style' % (fr.get('font'), weight, size, lead))

def _units(fr):
    runs = fr.get('runs') or []
    return runs if runs else [fr]

def check_colours(page, colours, lead=None):
    out = []
    n = page.get('page')
    bg = _rgb(page.get('pageBg'))
    if bg and (not match_colour(bg, colours)):
        out.append(_defect('off-token-colour', n, 'page ground rgb%s is no brand token' % bg))
    for fr in page.get('frames') or []:
        for what in ('bg', 'color'):
            rgb = _rgb(fr.get(what))
            if what == 'color' and (not (fr.get('text') or '').strip()):
                continue
            if rgb and (not match_colour(rgb, colours)):
                out.append(_defect('off-token-colour', n, '%s %s rgb%s is no brand token' % (fr.get('id'), what, rgb), [fr.get('id')]))
    return out

def check_type(page, styles, fam):
    out = []
    n = page.get('page')
    for fr in page.get('frames') or []:
        role = fr.get('role')
        if role in FILL_ROLES or role in VISUAL_ROLES or role in EXEMPT_TINY:
            continue
        if not (fr.get('text') or '').strip():
            continue
        for u in _units(fr):
            if not (u.get('text') or '').strip():
                continue
            name, why = _style_match(u, styles, fam)
            if not name:
                out.append(_defect('off-ramp-type', n, '%s: %s' % (fr.get('id'), why), [fr.get('id')]))
    return out
CONTAINER_ROLES = {'plate', 'panel'}

def _inside(inner, outer, tol=0.005):
    a, b = (inner['gb'], outer['gb'])
    return a[0] >= b[0] - tol and a[1] >= b[1] - tol and (a[2] <= b[2] + tol) and (a[3] <= b[3] + tol)

def _container_of(fr, frames):
    holders = [c for c in frames if c is not fr and c.get('role') in CONTAINER_ROLES and _inside(fr, c)]
    if not holders:
        return None
    return min(holders, key=lambda c: (c['gb'][2] - c['gb'][0]) * (c['gb'][3] - c['gb'][1]))

def _on_scale(gap, scale_in):
    return gap <= GAP_TOL_IN or any((abs(gap - v) <= GAP_TOL_IN for v in scale_in))

def check_spacing(page, scale_in):
    out = []
    n = page.get('page')
    frames = [f for f in page.get('frames') or [] if f.get('role') and f['role'] not in ('ground', 'decor') and f.get('gb')]
    by_id = {f.get('id'): f for f in frames}
    centred = set()
    for f in frames:
        if f.get('role') == 'label-of' and f.get('anchor') in by_id:
            a = by_id[f['anchor']]
            ha, hl = (a['gb'][2] - a['gb'][0], f['gb'][2] - f['gb'][0])
            centred.add(f.get('id') if hl <= ha else a.get('id'))
    holder = {f.get('id'): _container_of(f, frames) for f in frames}

    def _judge(a, b, gap, what='gap'):
        if not _on_scale(gap, scale_in):
            out.append(_defect('off-scale-spacing', n, '%s -> %s %s %.3fin is not on the scale %s' % (a.get('id'), b.get('id'), what, gap, ', '.join(('%.3f' % v for v in scale_in))), [a.get('id'), b.get('id')]))

    def _stack_span(c):
        inner = [f for f in frames if holder[f.get('id')] is c]
        return (min((f['gb'][0] for f in inner)), max((f['gb'][2] for f in inner))) if inner else None
    for a in frames:
        if a.get('id') in centred:
            continue
        c = holder[a.get('id')]
        siblings = [b for b in frames if b is not a and holder[b.get('id')] is c]
        below = [b for b in siblings if b['gb'][0] >= a['gb'][2] - 0.005 and b.get('role') != 'folio' and (min(a['gb'][3], b['gb'][3]) - max(a['gb'][1], b['gb'][1]) > 0.2)]
        if below:
            b = min(below, key=lambda x: x['gb'][0] - a['gb'][2])
            _judge(a, b, b['gb'][0] - a['gb'][2])
        if c is None:
            continue
        top, bottom = _stack_span(c)
        pad_top, pad_bottom = (top - c['gb'][0], c['gb'][2] - bottom)
        if abs(pad_top - pad_bottom) <= GAP_TOL_IN and pad_top > GAP_TOL_IN:
            continue
        if not below:
            _judge(a, c, c['gb'][2] - a['gb'][2], 'bottom padding')
        above = [b for b in siblings if b['gb'][2] <= a['gb'][0] + 0.005 and min(a['gb'][3], b['gb'][3]) - max(a['gb'][1], b['gb'][1]) > 0.2]
        if not above:
            _judge(c, a, a['gb'][0] - c['gb'][0], 'top padding')
    return out

def check_anchor_labels(page):
    out = []
    n = page.get('page')
    frames = page.get('frames') or []
    by_id = {f.get('id'): f for f in frames}
    for fr in frames:
        if fr.get('role') != 'label-of':
            continue
        anchor = by_id.get(fr.get('anchor'))
        if not anchor:
            out.append(_defect('anchor-label-misaligned', n, '%s names anchor %r which is not on the page' % (fr.get('id'), fr.get('anchor')), [fr.get('id')]))
            continue
        ac = (anchor['gb'][0] + anchor['gb'][2]) / 2
        lc = (fr['gb'][0] + fr['gb'][2]) / 2
        if abs(ac - lc) <= ALIGN_TOL_IN:
            continue
        connector = any((c.get('role') == 'rule' and c['gb'][1] <= anchor['gb'][3] + 0.05 and (c['gb'][3] >= fr['gb'][1] - 0.05) and (abs((c['gb'][0] + c['gb'][2]) / 2 - ac) <= ALIGN_TOL_IN) for c in frames))
        if not connector:
            out.append(_defect('anchor-label-misaligned', n, '%s centre is %.3fin off its anchor %s and no connector joins them' % (fr.get('id'), abs(ac - lc), anchor.get('id')), [fr.get('id'), anchor.get('id')]))
    return out

def check_roles(page):
    out = []
    n = page.get('page')
    for fr in page.get('frames') or []:
        role = fr.get('role')
        if not role:
            out.append(_defect('unlabelled-frame', n, '%s has no data-role; every frame declares what it is' % fr.get('id'), [fr.get('id')]))
        elif role not in KNOWN:
            out.append(_defect('unknown-role', n, '%s role %r is not a recognised role' % (fr.get('id'), role), [fr.get('id')]))
    return out

def check_tiny_visuals(page):
    out = []
    n = page.get('page')
    for fr in page.get('frames') or []:
        if fr.get('role') in VISUAL_ROLES or (fr.get('img') and fr.get('role') not in EXEMPT_TINY):
            w, h = (float(fr.get('wIn') or 0), float(fr.get('hIn') or 0))
            if min(w, h) < TINY_VISUAL_IN:
                out.append(_defect('tiny-visual', n, '%s is %.2f x %.2fin; nothing instructional under %.1fin' % (fr.get('id'), w, h, TINY_VISUAL_IN), [fr.get('id')]))
    return out

def check_waterfall(pages):
    out = []
    edges = {}
    for p in pages:
        hand = 'recto' if int(p.get('page') or 1) % 2 == 1 else 'verso'
        for fr in p.get('frames') or []:
            if fr.get('role') in STRUCTURAL and fr.get('gb'):
                edges.setdefault((fr['role'], hand), []).append((p.get('page'), fr['gb'][1]))
    for (role, hand), xs in edges.items():
        base = xs[0][1]
        for pg, x in xs[1:]:
            if abs(x - base) > EDGE_TOL_IN:
                out.append(_defect('role-edge-drift', pg, '%s on a %s page sits at x=%.3fin, elsewhere %.3fin' % (role, hand, x, base)))
    return out

def check_lead_colour(pages, colours, colourway):
    if not colourway or colourway not in colours:
        return []
    want = colours[colourway]
    for p in pages:
        if (bg := _rgb(p.get('pageBg'))) and all((abs(a - b) <= COLOUR_TOL for a, b in zip(bg, want))):
            return []
        for fr in p.get('frames') or []:
            rgb = _rgb(fr.get('bg'))
            if rgb and all((abs(a - b) <= COLOUR_TOL for a, b in zip(rgb, want))):
                return []
    return [_defect('lead-colour-absent', None, 'the declared colourway %s never appears as a fill; the piece is not leading with it' % colourway)]

def audit(pages: list, tokens: dict, colourway: str='') -> dict:
    found = []
    if not pages:
        return {'defects': [_defect('empty-audit', None, 'zero pages measured; measuring nothing is not measuring clean')], 'warnings': [], 'by_rule': {'empty-audit': 1}, 'pages_checked': 0}
    colours = token_colours(tokens)
    styles, fam = ramp_styles(tokens)
    scale = [float(v) for v in (tokens.get('spacing_scale') or {}).get('values_in') or []]
    for p in pages:
        found += check_roles(p)
        found += check_colours(p, colours)
        found += check_type(p, styles, fam)
        if scale:
            found += check_spacing(p, scale)
        found += check_anchor_labels(p)
        found += check_tiny_visuals(p)
    found += check_waterfall(pages)
    found += check_lead_colour(pages, colours, colourway)
    by_rule = {}
    for d in found:
        by_rule[d['rule']] = by_rule.get(d['rule'], 0) + 1
    return {'defects': [d for d in found if d['severity'] == 'defect'], 'warnings': [d for d in found if d['severity'] != 'defect'], 'by_rule': by_rule, 'pages_checked': len(pages)}
