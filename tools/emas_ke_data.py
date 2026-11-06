#!/usr/bin/env python3
"""docx 'Set Copywriting Gaya Mentor' (simpanan emas) -> data/<siri>.js (tiada dependency).

Guna:  python3 -I tools/emas_ke_data.py "Set.docx" --siri Emas-01 --mula 2001 --tema tema.json --fail data/Emas-01.js
Struktur docx: jadual indeks (Set | Tajuk | Tema & Fokus) -> `SET N: TAJUK` (HURUF BESAR) -> perenggan cerita
dan penutup tetap (CTA Taufik).  Seluruh teks antara dua tajuk disalin; tiada pautan sumber.
"""
import argparse, importlib.util, json, os, re, sys

here = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location('dk', os.path.join(here, 'docx_ke_data.py'))
dk = importlib.util.module_from_spec(spec); spec.loader.exec_module(dk)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('docx'); ap.add_argument('--siri', required=True)
    ap.add_argument('--mula', type=int, required=True); ap.add_argument('--tema'); ap.add_argument('--fail')
    ap.add_argument('--jadual', action='store_true')
    a = ap.parse_args()
    tema = json.load(open(a.tema, encoding='utf8')) if a.tema else {}
    paras = dk.baca(a.docx)
    h = next(i for i, (t, _) in enumerate(paras[:30]) if t.lower().startswith('set') or t.lower().startswith('no. set'))
    rows = [i for i, (t, _) in enumerate(paras) if re.fullmatch(r'Set\s*\d+(\s*\(#\d+\))?', t)]
    assert len(rows) == 30, f'baris indeks {len(rows)}'
    idx = []
    for r in rows:
        idx.append((paras[r][0], paras[r + 1][0], paras[r + 2][0]))
    fin = rows[-1] + 3
    hs = [i for i in range(fin, len(paras)) if re.match(r'^SET\s*\d+', paras[i][0])]
    assert len(hs) == 30, f'tajuk cerita {len(hs)}'
    items = []
    for n, i in enumerate(hs):
        end = hs[n + 1] if n + 1 < len(hs) else len(paras)
        body = [t for t, _ in paras[i + 1:end] if t.strip()]
        label, title, fokus = idx[n]
        head = paras[i][0]
        assert head.upper().rstrip('?.!').endswith(title.upper().rstrip('?.!')[-25:]), f'Set {n+1}: tajuk tidak padan\n {head}\n {title}'
        assert len(body) >= 25, f'Set {n+1}: teks terlalu pendek ({len(body)})'
        hook = body.pop(0)
        setno = re.search(r'\d+', label).group(0)
        it = dict(id=a.mula + n, siri=a.siri, no=n + 1, tajuk=title, lokasi=f'Set {setno}', subtema=fokus,
                  tema=tema.get(str(n + 1)) or fokus, hook=hook, body=body)
        items.append(it)
    if a.jadual:
        for it in items: print(it['no'], '|', it['lokasi'], '|', it['tajuk'][:60], '|', it['subtema'][:50], file=sys.stderr)
    blok = ',\n'.join(json.dumps(it, ensure_ascii=False) for it in items)
    if a.fail:
        open(a.fail, 'w', encoding='utf8').write(f'(window.STORIES=window.STORIES||[]).push(\n{blok}\n);\n')
    else:
        print(blok)

if __name__ == '__main__':
    main()
