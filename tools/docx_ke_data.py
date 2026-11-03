#!/usr/bin/env python3
"""docx Kisah Benar -> blok JS untuk data.js (tiada dependency).

Guna:  python3 -I tools/docx_ke_data.py "Set.docx" --siri KisahBenar-02 --mula 31 > blok.txt
Format docx: baris `Kisah NN: Subjek (Julukan) — Lokasi (Tahun)`, kemudian
`Sumber Fakta & Laporan Susulan: A & B` (ada hyperlink), baris hook HURUF BESAR,
dan perenggan cerita.  Tema diisi dari jadual TEMA di bawah (ikut nombor kisah dalam docx);
kalau tiada padanan, jatuh ke 'Kebaikan Insan' dan dicetak amaran ke stderr.
"""
import argparse, html, json, re, sys, zipfile

TEMA = {}  # {nombor_docx: "Tema"}; diisi dengan --tema fail.json bila ada siri baharu

def baca(path):
    z = zipfile.ZipFile(path)
    rels_xml = z.read('word/_rels/document.xml.rels').decode('utf8')
    rels = {}
    for tag in re.findall(r'<Relationship [^>]*>', rels_xml):
        i = re.search(r'Id="([^"]+)"', tag); t = re.search(r'Target="([^"]+)"', tag)
        if i and t: rels[i.group(1)] = html.unescape(t.group(1))
    x = z.read('word/document.xml').decode('utf8')
    out = []
    for p in re.findall(r'<w:p[ >].*?</w:p>', x, flags=re.S):
        links = [rels.get(i) for i in re.findall(r'<w:hyperlink[^>]*r:id="([^"]+)"', p)]
        t = html.unescape(re.sub(r'<[^>]+>', '', p)).strip()
        out.append((t, [l for l in links if l]))
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('docx'); ap.add_argument('--siri', required=True)
    ap.add_argument('--mula', type=int, required=True, help='id global pertama')
    ap.add_argument('--tema', help='fail JSON {"1":"Tema",...} ikut nombor kisah docx')
    a = ap.parse_args()
    tema = dict(TEMA)
    if a.tema: tema.update(json.load(open(a.tema, encoding='utf8')))
    paras = baca(a.docx)
    head = re.compile(r'^Kisah\s*(\d+)\s*:\s*(.+)$')
    idx = [i for i, (t, _) in enumerate(paras) if head.match(t)]
    items = []
    for n, i in enumerate(idx):
        end = idx[n + 1] if n + 1 < len(idx) else len(paras)
        m = head.match(paras[i][0]); no_docx = str(int(m.group(1)))
        subjek, meta = m.group(2).rsplit(' — ', 1)
        lm = re.match(r'(.*)\s\(([^()]*)\)\s*$', meta)
        lokasi, tahun = (lm.group(1), lm.group(2)) if lm else (meta, '')
        blok = [(t, l) for t, l in paras[i + 1:end] if t]
        sumber_t, sumber_l = blok[0]
        assert sumber_t.startswith('Sumber Fakta'), f'Kisah {no_docx}: baris sumber tiada'
        assert sumber_l, f'Kisah {no_docx}: sumber tiada hyperlink'
        hook = blok[1][0]
        body = [t for t, _ in blok[2:]]
        nama = subjek.split(' (')[0]
        if no_docx not in tema: print(f'AMARAN kisah {no_docx}: tema tiada', file=sys.stderr)
        items.append(dict(
            id=a.mula + n, siri=a.siri, no=n + 1, nama=nama, tajuk=subjek,
            lokasi=lokasi, tahun=tahun,
            sumber=sumber_t.split(':', 1)[1].strip(), link=sumber_l[0],
            tema=tema.get(no_docx, 'Kebaikan Insan'), hook=hook, body=body))
    assert len(items) == 30, f'dijangka 30 kisah, jumpa {len(items)}'
    print(',\n'.join(json.dumps(it, ensure_ascii=False) for it in items))

if __name__ == '__main__':
    main()
