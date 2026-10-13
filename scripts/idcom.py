from __future__ import annotations
import json
import time
import uuid
SCRIPT_LANGUAGE_UXPSCRIPT = 1431522407
PROGIDS = ('InDesign.Application', 'InDesign.Application.2025')
_app = None

class InDesignUnavailable(RuntimeError):
    pass

def app(refresh: bool=False):
    global _app
    if _app is not None and (not refresh):
        return _app
    import pythoncom
    import win32com.client
    pythoncom.CoInitialize()
    errors = []
    for progid in PROGIDS:
        try:
            _app = win32com.client.GetActiveObject(progid)
            return _app
        except Exception as exc:
            errors.append('GetActiveObject(%s): %s' % (progid, exc))
    for progid in PROGIDS:
        try:
            _app = win32com.client.Dispatch(progid)
            return _app
        except Exception as exc:
            errors.append('Dispatch(%s): %s' % (progid, exc))
    raise InDesignUnavailable('cannot reach InDesign over COM. Is it running?\n  ' + '\n  '.join(errors))

def alive(timeout: float=20.0) -> bool:
    try:
        return ex("return 'alive';", timeout=timeout) == 'alive'
    except Exception:
        return False
_WRAPPER = '\nconst __idsn = require("indesign");\nconst __key = %s;\n(async () => {\n  try {\n    const __r = await (async () => { %s })();\n    __idsn.app.insertLabel(__key, JSON.stringify({ok: true, result: __r === undefined ? null : __r}));\n  } catch (e) {\n    __idsn.app.insertLabel(__key, JSON.stringify({ok: false, error: String((e && e.message) || e)}));\n  }\n})();'

def ex(code: str, timeout: float=60.0, poll: float=0.05):
    a = app()
    key = 'svetlana_' + uuid.uuid4().hex[:16]
    try:
        a.InsertLabel(key, '')
    except Exception:
        pass
    script = _WRAPPER % (json.dumps(key), code)
    a.DoScript(script, SCRIPT_LANGUAGE_UXPSCRIPT)
    deadline = time.time() + timeout
    raw = ''
    while time.time() < deadline:
        try:
            raw = a.ExtractLabel(key)
        except Exception:
            raw = ''
        if raw:
            break
        time.sleep(poll)
    if not raw:
        raise RuntimeError('InDesign did not answer within %.0fs. The script may still be running, or it hit a modal dialog — check InDesign before retrying, and do not fire the same call again on top of it.' % timeout)
    try:
        a.InsertLabel(key, '')
    except Exception:
        pass
    payload = json.loads(raw)
    if not payload.get('ok'):
        raise RuntimeError('InDesign: %s' % payload.get('error'))
    return payload.get('result')

def documents() -> list:
    return json.loads(ex('\n    const a = require("indesign").app; const out = [];\n    for (let i = 0; i < a.documents.length; i++) {\n      const d = a.documents.item(i);\n      out.push({name: d.name, modified: d.modified, pages: d.pages.length,\n                saved: d.saved});\n    }\n    return JSON.stringify(out);\n    '))
if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == 'docs':
        for d in documents():
            print('%-4s modified=%-5s pages=%-3s %s' % ('', d['modified'], d['pages'], d['name']))
    elif len(sys.argv) > 2 and sys.argv[1] == 'ex':
        print(ex(sys.argv[2]))
    else:
        print('alive' if alive() else 'NOT ALIVE')
