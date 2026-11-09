#!/usr/bin/env python3
"""docx koleksi 'Variasi' (cerita Taufik: fakta haiwan, inovasi kitar semula ...) -> data/<siri>.js

Guna:  python3 -I tools/variasi_ke_data.py "Set.docx" --siri Variasi-01 --mula 3001 --tema tema.json --fail data/Variasi-01.js
Struktur docx: jadual indeks (Tajuk | Lokasi & Tahun | Sumber+pautan) -> `CERITA #NN | LOKASI (TAHUN)` atau
`SET 02 - CERITA #NN | ...` -> `NN. Tajuk` -> hook HURUF BESAR -> cerita (termasuk penutup tetap Taufik) -> `Sumber: ...`.
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
    ap.add_argument('--langkau', default='', help='nombor cerita (dalam docx) yang dilangkau, dipisah koma; nombor lain kekal ikut docx')
    a = ap.parse_args()
    tema = json.load(open(a.tema, encoding='utf8')) if a.tema else {}
    langkau = {x.strip() for x in a.langkau.split(',') if x.strip()}
    paras = dk.baca(a.docx)
    first = [i for i, (t, _) in enumerate(paras) if re.fullmatch(r'#\d+', t)]
    assert len(first) == 30, f'baris indeks {len(first)}'
    idx = []
    for i in first:
        (_, _), (tj, _), (lt, _), (sb, sl) = paras[i], paras[i + 1], paras[i + 2], paras[i + 3]
        idx.append((tj, lt, sb, sl[0] if sl else ''))
    hs = [i for i, (t, _) in enumerate(paras) if i > first[-1] and re.match(r'^(SET\s*\d+\s*-\s*)?CERITA\s*#\d+\s*\|', t)]
    assert len(hs) == 30, f'tajuk cerita {len(hs)}'
    items = []
    for n, i in enumerate(hs):
        end = hs[n + 1] if n + 1 < len(hs) else len(paras)
        blok = [t for t, _ in paras[i + 1:end] if t.strip()]
        tj, lt, sb, link = idx[n]
        assert blok[0].startswith(f'{n+1:02d}.'), f'Cerita {n+1}: baris tajuk tiada ({blok[0][:40]})'
        ks = [k for k, t in enumerate(blok) if re.match(r'^Sumber\b', t)]
        assert ks, f'Cerita {n+1}: baris sumber tiada'
        k = ks[-1]
        assert link.startswith('http'), f'Cerita {n+1}: pautan indeks tiada'
        tagar = [t for t in blok[k + 1:] if t.startswith('#')]     # contoh #HappyLoop (di bawah senarai sumber dalam docx)
        story = blok[1:k] + tagar
        assert len(story) >= 30, f'Cerita {n+1}: teks terlalu pendek ({len(story)})'
        hook = story.pop(0)
        m = re.match(r'^(.*?)\s*\(([^()]*)\)\s*$', lt)
        lokasi, tahun = (m.group(1), m.group(2)) if m else (lt, '')
        it = dict(id=a.mula + n, siri=a.siri, no=n + 1, tajuk=tj, lokasi=lokasi, tahun=tahun, sumber=sb, link=link,
                  tema=tema.get(str(n + 1), ''), hook=hook, body=story)
        if str(n + 1) in langkau: continue
        items.append({k: v for k, v in it.items() if v != ''})
    if a.jadual:
        for it in items: print(it['no'], '|', it['tajuk'][:80], '|', it.get('lokasi', ''), file=sys.stderr)
    blok = ',\n'.join(json.dumps(it, ensure_ascii=False) for it in items)
    if a.fail:
        open(a.fail, 'w', encoding='utf8').write(f'(window.STORIES=window.STORIES||[]).push(\n{blok}\n);\n')
    else:
        print(blok)

if __name__ == '__main__':
    main()
