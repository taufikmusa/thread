#!/usr/bin/env python3
"""docx Kisah Benar -> blok JS untuk data.js (tiada dependency).

Guna:  python3 -I tools/docx_ke_data.py "Set.docx" --siri KisahBenar-02 --mula 31 > blok.txt
Format docx: baris `Kisah NN: Subjek (Julukan) — Lokasi (Tahun)`, kemudian
`Sumber Fakta & Laporan Susulan: A & B` (ada hyperlink), baris hook HURUF BESAR,
dan perenggan cerita.  Tema diisi dari jadual TEMA di bawah (ikut nombor kisah dalam docx);
kalau tiada padanan, jatuh ke 'Kebaikan Insan' dan dicetak amaran ke stderr.
"""
import argparse, html, json, re, sys, zipfile


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

ACRONIM = {'OKU','CEO','UK','AS','USA','AI','DNA','NASA','NBA','NFL','SPM','UAE','PBB','FBI','CPR','ICU','KL'}
def tc(t):
    return ' '.join(w if w.strip('(),') in ACRONIM else w.capitalize() if w.lower() != 'hingga' else 'hingga'
                    for w in t.split(' ')).replace('Dan ', 'Dan ')

# tema automatik ikut kata kunci (urutan = keutamaan); semak keluaran dan ganti dengan --tema bila salah
KEYWORD = [
 ('Perang & Bencana', ['perang','gempa','runtuhan','bom ','bom,','letupan','pelarian','syria','afghanistan','bencana','banjir','tsunami','taufan','ribut','gunung berapi','kem pelarian','konflik','tentera']),
 ('Ketabahan & OKU', ['lumpuh','tanpa lengan','tanpa tangan','tanpa kaki','tanpa kedua','buta','pekak','oku','barah','leukemia','kanser','kecacatan','kerusi roda','istimewa','autisme','down syndrome','ketabahan','penyakit','kehilangan keempat','kehilangan kaki','kehilangan lengan','cacat']),
 ('Kemiskinan & Pendidikan', ['miskin','kemiskinan','kebuluran','lapar','belajar','pelajar','sekolah','universiti','pendidikan','yatim','gelandangan','tidak mampu','kerja keras','buku','tuisyen','biasiswa']),
 ('Cinta & Persahabatan', ['cinta','suami','isteri','pasangan','sahabat','persahabatan','kekasih','perkahwinan','kawan','teman','jodoh']),
 ('Wira & Inspirasi', ['menyelamatkan','wira','pakar bedah','doktor','polis','bomba','hutan','inspirasi','inovasi','pencipta','jurutera','pengorbanan nyawa','heroik','pahlawan']),
 ('Kasih Keluarga', ['ibu','bapa','ayah','anak','adik','abang','kakak','datuk','nenek','keluarga','cucu','emak']),
]
def auto_tema(*teks):
    t = ' ' + ' '.join(teks).lower() + ' '
    for nama, kws in KEYWORD:
        if any(k in t for k in kws): return nama
    return 'Kebaikan Insan'

def bina(a, tema, paras):
    old = re.compile(r'^Kisah\s*(\d+)\s*:\s*(.+)$')
    new = re.compile(r'^KISAH\s*#(\d+)\s*[\u2022\u00b7\-]\s*(.+)$')
    idx_old = [i for i, (t, _) in enumerate(paras) if old.match(t)]
    idx_new = [i for i, (t, _) in enumerate(paras) if new.match(t)]
    fmt, idx = ('old', idx_old) if len(idx_old) >= len(idx_new) else ('new', idx_new)
    items = []
    for n, i in enumerate(idx):
        end = idx[n + 1] if n + 1 < len(idx) else len(paras)
        blok = [(t, l) for t, l in paras[i + 1:end] if t]
        no = n + 1
        if fmt == 'old':
            m = old.match(paras[i][0])
            subjek, meta = m.group(2).rsplit(' \u2014 ', 1)
            lm = re.match(r'(.*)\s\(([^()]*)\)\s*$', meta)
            lokasi, tahun = (lm.group(1), lm.group(2)) if lm else (meta, '')
            nama, tajuk, subtema = subjek.split(' (')[0], subjek, ''
        else:
            m = new.match(paras[i][0])
            sub, meta = m.group(2).rsplit(' (', 1)
            meta = meta.rstrip(')')
            lokasi, tahun = meta.rsplit(' - ', 1) if ' - ' in meta else (meta, '')
            subtema, lokasi, tahun = tc(sub.strip()), tc(lokasi.strip()), tahun.strip().lower()
            tajuk = nama = blok.pop(0)[0]
        sumber_t, sumber_l = blok[0]
        assert sumber_t.startswith('Sumber Fakta'), f'Kisah {no}: baris sumber tiada ({sumber_t[:40]})'
        assert sumber_l, f'Kisah {no}: sumber tiada hyperlink'
        hook = blok[1][0]
        body = [t for t, _ in blok[2:]]
        assert len(body) >= 15, f'Kisah {no}: badan cerita terlalu pendek ({len(body)})'
        tm = tema.get(str(no)) or auto_tema(tajuk, subtema, hook)
        it = dict(id=a.mula + n, siri=a.siri, no=no, nama=nama, tajuk=tajuk, lokasi=lokasi, tahun=tahun,
                  sumber=sumber_t.split(':', 1)[1].strip(), link=sumber_l[0], tema=tm, hook=hook, body=body)
        if subtema: it['subtema'] = subtema
        items.append(it)
    return items

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('docx'); ap.add_argument('--siri', required=True)
    ap.add_argument('--mula', type=int, required=True, help='id global pertama')
    ap.add_argument('--tema', help='fail JSON {"1":"Tema",...} ikut nombor dalam siri (1-30); mengatasi tema automatik')
    ap.add_argument('--jadual', action='store_true', help='cetak jadual semakan tema ke stderr')
    a = ap.parse_args()
    tema = json.load(open(a.tema, encoding='utf8')) if a.tema else {}
    items = bina(a, tema, baca(a.docx))
    assert len(items) == 30, f'dijangka 30 kisah, jumpa {len(items)}'
    if a.jadual:
        for it in items: print(it['no'], '|', it['tema'], '|', it['tajuk'][:60], '|', it.get('subtema', ''), file=sys.stderr)
    print(',\n'.join(json.dumps(it, ensure_ascii=False) for it in items))

if __name__ == '__main__':
    main()
