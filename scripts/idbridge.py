import os, sys, json, urllib.request, urllib.error
BRIDGE = os.environ.get('INDESIGN_BRIDGE_URL', 'http://127.0.0.1:3000').rstrip('/')
_TRANSPORT = None

def _ex_http(code, timeout=60):
    body = json.dumps({'code': code}).encode()
    req = urllib.request.Request(BRIDGE + '/execute', data=body, headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            payload = json.loads(r.read())
    except urllib.error.HTTPError as e:
        raise RuntimeError('HTTP %s: %s' % (e.code, e.read().decode()[:500]))
    if 'error' in payload:
        raise RuntimeError('bridge: ' + str(payload['error']))
    return payload.get('result')

def _pick_transport():
    global _TRANSPORT
    if _TRANSPORT:
        return _TRANSPORT
    forced = (os.environ.get('SVETLANA_ID_TRANSPORT') or 'auto').strip().lower()
    if forced in ('com', 'http'):
        _TRANSPORT = forced
        return _TRANSPORT
    try:
        import idcom
        if idcom.alive(timeout=20):
            _TRANSPORT = 'com'
            print('[idbridge] transport: COM (doScript/UXPSCRIPT) — no panel needed', file=sys.stderr)
            return _TRANSPORT
    except Exception as exc:
        print('[idbridge] COM unavailable (%s) — falling back to the UXP bridge' % exc, file=sys.stderr)
    _TRANSPORT = 'http'
    print('[idbridge] transport: UXP bridge over HTTP', file=sys.stderr)
    return _TRANSPORT

def ex(code, timeout=60):
    if _pick_transport() == 'com':
        import idcom
        return idcom.ex(code, timeout=timeout)
    return _ex_http(code, timeout=timeout)

def _jspath(p):
    return p.replace('\\', '/')

def open_doc(path):
    return ex('return require("indesign").app.open("%s").name;' % _jspath(path))

def info():
    code = '\n    var app = require("indesign").app;\n    var d = app.activeDocument;\n    var pages = [];\n    for (var p=0;p<d.pages.length;p++){ var b=d.pages.item(p).bounds; pages.push(b); }\n    return JSON.stringify({name:d.name,\n      pw:d.documentPreferences.pageWidth, ph:d.documentPreferences.pageHeight,\n      units_h:String(d.viewPreferences.horizontalMeasurementUnits),\n      npages:d.pages.length, pageBounds:pages});\n    '
    return ex(code)

def frames():
    code = '\n    var d = require("indesign").app.activeDocument;\n    var out = {name:d.name, pages:[]};\n    for (var p=0;p<d.pages.length;p++){\n      var pg=d.pages.item(p), tfs=pg.textFrames, fr=[];\n      for (var i=0;i<tfs.length;i++){\n        var tf=tfs.item(i), gb=tf.geometricBounds, txt="";\n        try{ txt=tf.contents; }catch(e){ txt=""; }\n        if(typeof txt!=="string") txt="";\n        fr.push({id:tf.id, gb:gb, over:tf.overflows, hasText:txt.replace(/\\s/g,"").length>0, snip:txt.substring(0,60)});\n      }\n      out.pages.push({page:p, bounds:pg.bounds, frames:fr});\n    }\n    return JSON.stringify(out);\n    '
    return ex(code)

def export_pdf(out_path):
    code = '\n    var idn=require("indesign"), app=idn.app, d=app.activeDocument;\n    var f="%s";\n    try { app.pdfExportPreferences.viewPDF = false; } catch (e) {}\n    d.exportFile(idn.ExportFormat.PDF_TYPE, f, false);\n    return "exported "+f;\n    ' % _jspath(out_path)
    return ex(code, timeout=120)

def save_as(out_path):
    code = '\n    var d=require("indesign").app.activeDocument;\n    d.save("%s");\n    return d.name;\n    ' % _jspath(out_path)
    return ex(code, timeout=120)

def close_nosave():
    code = '\n    var idn=require("indesign"); var d=idn.app.activeDocument;\n    d.close(idn.SaveOptions.NO);\n    return "closed";\n    '
    return ex(code)

def open_docs_report():
    code = '\n    var a=require("indesign").app.documents, o=[];\n    for(var i=0;i<a.length;i++) o.push(a.item(i).name);\n    return JSON.stringify(o);\n    '
    return ex(code)
if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'info'
    arg = sys.argv[2] if len(sys.argv) > 2 else ''
    try:
        if cmd == 'ex':
            print(ex(arg))
        elif cmd == 'open':
            print(open_doc(arg))
        elif cmd == 'info':
            print(info())
        elif cmd == 'frames':
            print(frames())
        elif cmd == 'pdf':
            print(export_pdf(arg))
        elif cmd == 'saveas':
            print(save_as(arg))
        elif cmd == 'close':
            print(close_nosave())
        elif cmd == 'closeall_report':
            print(open_docs_report())
        else:
            print('unknown cmd', cmd)
            sys.exit(2)
    except (urllib.error.URLError, RuntimeError) as e:
        print('BRIDGE ERROR:', e, file=sys.stderr)
        sys.exit(2)
