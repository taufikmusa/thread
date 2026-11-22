#!/usr/bin/env python3
"""docx 'Copywriting' ringkas (Refleksi / Kisah Benar Kucing ...) -> data/<siri>.js (tiada dependency).

Guna:  python3 -I tools/cerita_ke_data.py "Set.docx" --siri Kucing-02 --mula 4011 --tema tema.json --fail data/Kucing-02.js [--bil 30]
Struktur: jadual indeks (No. | Tajuk/Nama | Tokoh atau Lokasi & Tahun | Fokus/Ringkasan) -> tajuk cerita
`CERITA #NN | ...` atau `COPYWRITING #NN | ...` -> hook HURUF BESAR -> cerita (termasuk penutup tetap, jika ada).
Tiada sumber/pautan dalam docx jenis ini.
"""
import argparse, importlib.util, json, os, re, sys

here = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location('dk', os.path.join(here, 'docx_ke_data.py'))
dk = importlib.util.module_from_spec(spec); spec.loader.exec_module(dk)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('docx'); ap.add_argument('--siri', required=True)
    ap.add_argument('--mula', type=int, required=True); ap.add_argument('--tema'); ap.add_argument('--fail')
    ap.add_argument('--bil', type=int, default=30, help='bilangan cerita dijangka'); ap.add_argument('--jadual', action='store_true')
    a = ap.parse_args()
    tema = json.load(open(a.tema, encoding='utf8')) if a.tema else {}
    paras = dk.baca(a.docx)
    first = [i for i, (t, _) in enumerate(paras) if re.fullmatch(r'#?\d{1,3}', t)]
    assert len(first) == a.bil, f'baris indeks {len(first)}'
    ncol = first[1] - first[0]
    hdr = [t for t, _ in paras[first[0] - ncol:first[0]]]
    assert ncol == 4, f'kolum indeks {ncol}: {hdr}'
    idx = [tuple(paras[i + k][0] for k in (1, 2, 3)) for i in first]
    hs = [i for i, (t, _) in enumerate(paras) if i > first[-1] and re.match(r'^(CERITA|COPYWRITING)\s*#\d+\s*\|', t)]
    assert len(hs) == a.bil, f'tajuk cerita {len(hs)}'
    mode_lokasi = 'lokasi' in hdr[2].lower()          # kucing: Nama | Lokasi & Tahun | Ringkasan
    items = []
    for n, i in enumerate(hs):
        end = hs[n + 1] if n + 1 < len(hs) else len(paras)
        blok = [t for t, _ in paras[i + 1:end] if t.strip()]
        c1, c2, c3 = idx[n]
        assert len(blok) >= 8, f'Cerita {n+1}: teks terlalu pendek ({len(blok)})'
        hook = blok.pop(0)
        if mode_lokasi:
            m = re.match(r'^(.*?)\s*\(([^()]*)\)\s*$', c2)
            lokasi, tahun = (m.group(1), m.group(2)) if m else (c2, '')
            it = dict(id=a.mula + n, siri=a.siri, no=n + 1, tajuk=c1, lokasi=lokasi, tahun=tahun, subtema=c3)
        else:                                          # refleksi: Hook | Tokoh & Sumber | Fokus
            it = dict(id=a.mula + n, siri=a.siri, no=n + 1, tajuk=c2, subtema=c3)
        it.update(tema=tema.get(str(n + 1), ''), hook=hook, body=blok)
        items.append({k: v for k, v in it.items() if v != ''})
    if a.jadual:
        for it in items: print(it['no'], '|', it['tajuk'][:50], '|', it.get('lokasi', ''), '|', it.get('subtema', '')[:90], file=sys.stderr)
    blokj = ',\n'.join(json.dumps(it, ensure_ascii=False) for it in items)
    if a.fail:
        open(a.fail, 'w', encoding='utf8').write(f'(window.STORIES=window.STORIES||[]).push(\n{blokj}\n);\n')
    else:
        print(blokj)

if __name__ == '__main__':
    main()
