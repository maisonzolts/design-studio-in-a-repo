from __future__ import annotations
import sys
import idbridge

def main() -> int:
    try:
        result = idbridge.ex("return 'alive';", timeout=20)
    except Exception as exc:
        print(f'InDesign unavailable: {exc}', file=sys.stderr)
        return 1
    print('alive' if result == 'alive' else f'unexpected response: {result!r}')
    return 0 if result == 'alive' else 2
if __name__ == '__main__':
    raise SystemExit(main())
