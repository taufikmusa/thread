#!/usr/bin/env python3
"""docx Kisah Benar -> blok JS untuk data.js (tiada dependency).

Guna:  python3 -I tools/docx_ke_data.py "Set.docx" --siri KisahBenar-11 --mula 301 --tema tema.json --fail data/KisahBenar-11.js
Kemudian tambah nama siri dalam data/index.js (SIRI.utama).
Format docx: baris `Kisah NN: Subjek (Julukan) — Lokasi (Tahun)`, kemudian
`Sumber Fakta & Laporan Susulan: A & B` (ada hyperlink), baris hook HURUF BESAR,
dan perenggan cerita.  Tema diisi dari jadual TEMA di bawah (ikut nombor kisah dalam docx);
kalau tiada padanan, jatuh ke 'Kebaikan Insan' dan dicetak amaran ke stderr.
"""
import argparse, html, json, re, sys, zipfile


def bersih(t):
    t = re.sub(r'\*{1,3}([^*\n]+?)\*{1,3}', r'\1', t)
    return re.sub(r'\*+', '', t)                      # penanda tergantung (tebal merentas perenggan)

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
        t = bersih(html.unescape(re.sub(r'<[^>]+>', '', p)).strip())
        out.append((t, [l for l in links if l]))
    return out

ACRONIM = {'GPS','SARS','OKU','CEO','UK','AS','USA','AI','DNA','NASA','NBA','NFL','SPM','UAE','PBB','FBI','CPR','ICU','KL'}
KECIL = {'dan', 'ke', 'di', 'dari', 'hingga', 'yang', 'dalam', 'atas', 'untuk'}
def cap(x):
    """Huruf besar pada huruf pertama (langkau tanda petik/kurungan di depan), selebihnya kecil."""
    m = re.match(r"^([^A-Za-z\u00C0-\u024F0-9]*)(.*)$", x)
    return m.group(1) + m.group(2)[:1].upper() + m.group(2)[1:].lower()

def tc(t):
    """HURUF BESAR -> Title Case, kekalkan akronim, singkatan bertitik (D.C.), perkataan kecil, sempang."""
    out = []
    for k, w in enumerate(t.split(' ')):
        core = w.strip('(),/')
        if core.upper() in ACRONIM: out.append(w.upper()); continue
        if re.fullmatch(r'(?i)([a-z]\.)+[a-z]?\.?', core): out.append(w.upper()); continue
        if k and core.lower() in KECIL: out.append(w.lower()); continue
        if re.fullmatch(r'(?i)rm\d[\d,.]*', core): out.append(w.upper()); continue
        out.append('-'.join(cap(x) for x in w.split('-')))
    return ' '.join(out)

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

def outro_kiraan(paras):
    """Kira berapa kali setiap perenggan muncul selepas baris pengesahan 'Kisah #N (...)' (outro generik set 16+)."""
    from collections import Counter
    c, after = Counter(), False
    for t, _ in paras:
        if re.match(r'^KISAH\s*#\d+\s*:', t): after = False
        elif re.match(r'^Kisah #\d+ \(', t): after = True
        elif after and t: c[t] += 1
    return c

def bina(a, tema, paras):
    a_outro = getattr(a, 'outro', False)
    OUTRO_KIRAAN = outro_kiraan(paras)
    old = re.compile(r'^Kisah\s*(\d+)\s*:\s*(.+)$')
    new = re.compile(r'^KISAH\s*#(\d+)\s*[\u2022\u00b7\-]\s*(.+)$')
    kolon = re.compile(r'^KISAH\s*#(\d+)\s*:\s*(.+)$')                 # set 16+: KISAH #451: TAJUK
    idx_old = [i for i, (t, _) in enumerate(paras) if old.match(t)]
    idx_new = [i for i, (t, _) in enumerate(paras) if new.match(t)]
    idx_kol = [i for i, (t, _) in enumerate(paras) if kolon.match(t)]
    fmt, idx = max((('old', idx_old), ('new', idx_new), ('kolon', idx_kol)), key=lambda x: len(x[1]))
    items = []
    for n, i in enumerate(idx):
        end = idx[n + 1] if n + 1 < len(idx) else len(paras)
        blok = [(t, l) for t, l in paras[i + 1:end] if t]
        no = n + 1
        hook_awal = visual_awal = ''
        if fmt == 'old':
            m = old.match(paras[i][0])
            subjek, meta = m.group(2).rsplit(' \u2014 ', 1)
            lm = re.match(r'(.*)\s\(([^()]*)\)\s*$', meta)
            lokasi, tahun = (lm.group(1), lm.group(2)) if lm else (meta, '')
            nama, tajuk, subtema = subjek.split(' (')[0], subjek, ''
        elif fmt == 'kolon':
            m = kolon.match(paras[i][0])
            tajuk = nama = tc(m.group(2).strip()); lokasi = tahun = subtema = ''
        else:
            m = new.match(paras[i][0])
            rest = m.group(2).strip()
            mt = re.match(r'^TAHUN\s+(.+?)\s*[\u2022\u00b7]\s*(.+)$', rest)   # set 23+: TAHUN 1916 • KATEGORI
            if mt:
                sub, lokasi, tahun = mt.group(2), '', mt.group(1)
            elif rest.endswith(')') and ' (' in rest:   # set 04-08: tajuk (LOKASI - TAHUN)
                sub, meta = rest.rsplit(' (', 1)
                meta = meta.rstrip(')')
                lokasi, tahun = meta.rsplit(' - ', 1) if ' - ' in meta else (meta, '')
            else:                                      # set 09-10: tiada lokasi dalam docx
                sub, lokasi, tahun = rest, '', ''
            subtema, lokasi, tahun = tc(sub.strip()), tc(lokasi.strip()), tc(tahun.strip())
            tajuk = blok.pop(0)[0]
            tajuk = re.sub(r'^\d+\.\s*', '', tajuk)                 # awalan "331. " (set 12)
            ym = re.search(r'\s*\((\d{4}(?:\s*[\u2013-]\s*\d{4})?)\)\s*$', tajuk)
            if ym:                                                    # tahun hujung tajuk -> medan tahun
                tahun = tahun or ym.group(1); tajuk = tajuk[:ym.start()]
            nama = tajuk
            if mt:                                                    # set 23+: petikan, [Visual Gambar Ikonik], sumber di hujung
                if blok and re.match(r'^[\u201c"]', blok[0][0]): hook_awal = blok.pop(0)[0]
                if blok and blok[0][0].startswith('Visual Gambar'):
                    visual_awal = blok.pop(0)[0].split(':', 1)[1].strip()
                if not blok[0][0].startswith('Sumber'):
                    k = max(k for k, (t, _) in enumerate(blok) if t.startswith('Sumber'))
                    blok.insert(0, blok.pop(k))
        gambar = ''
        if fmt == 'kolon':
            if blok[0][0].startswith('Kata Kunci'):
                gambar = blok.pop(0)[0].split(':', 1)[1].strip()
        visual = visual_awal
        if fmt == 'kolon':                                # set 20: Kategori & Latar / [Visual Gambar] / sumber di hujung
            if blok[0][0].startswith('Kategori'):
                kat = blok.pop(0)[0].split(':', 1)[1].strip()
                km = re.match(r'^(.*)\s\(([^()]*)\)\s*$', kat)
                if km:
                    subtema = km.group(1).strip()
                    lokasi, tahun = km.group(2).rsplit(' - ', 1) if ' - ' in km.group(2) else (km.group(2), '')
                else:
                    subtema = kat
            if blok[0][0].startswith('[Visual'):
                visual = blok.pop(0)[0].split(']:', 1)[1].strip()
            if not blok[0][0].startswith('Sumber'):
                k = max(k for k, (t, _) in enumerate(blok) if t.startswith('Sumber'))
                blok.insert(0, blok.pop(k))
        sumber_t, sumber_l = blok[0]
        assert sumber_t.startswith('Sumber'), f'Kisah {no}: baris sumber tiada ({sumber_t[:40]})'
        assert sumber_l, f'Kisah {no}: sumber tiada hyperlink'
        if fmt == 'kolon':
            body = [t for t, _ in blok[1:]]
            v = next((k for k, t in enumerate(body) if re.match(r'^Kisah #\d+ \(', t)), None)
            if v is not None:                       # buang baris pengesahan + outro generik; kekalkan penutup khusus
                sisa = body[v + 1:]
                ekor = [t for t in sisa if OUTRO_KIRAAN.get(t, 0) < 10 and not t.startswith('Kisah #')]
                body = body[:v] + ekor if not a_outro else body
            hook = body.pop(0)
        elif hook_awal:
            hook = hook_awal
            body = [t for t, _ in blok[1:]]
        else:
            hook = blok[1][0]
            body = [t for t, _ in blok[2:]]
            while body and body[0].isupper():      # hook dua baris HURUF BESAR (set 12)
                hook += '\n' + body.pop(0)
        assert len(body) >= 10, f'Kisah {no}: badan cerita terlalu pendek ({len(body)})'
        tm = tema.get(str(no)) or auto_tema(tajuk, subtema, hook)
        it = dict(id=a.mula + n, siri=a.siri, no=no, nama=nama, tajuk=tajuk, lokasi=lokasi, tahun=tahun,
                  sumber=re.sub(r'\s*\(https?://.*$', '', sumber_t.split(':', 1)[1].strip()), link=sumber_l[0], tema=tm, hook=hook, body=body)
        if subtema: it['subtema'] = subtema
        if gambar: it['gambar'] = gambar
        if visual: it['visual'] = visual
        items.append(it)
    return items

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('docx'); ap.add_argument('--siri', required=True)
    ap.add_argument('--mula', type=int, required=True, help='id global pertama')
    ap.add_argument('--tema', help='fail JSON {"1":"Tema",...} ikut nombor dalam siri (1-30); mengatasi tema automatik')
    ap.add_argument('--fail', help='tulis terus ke data/<siri>.js (muat malas) dan bukannya stdout')
    ap.add_argument('--outro', action='store_true', help='set 16+: kekalkan baris pengesahan dan outro generik (lalai: dibuang)')
    ap.add_argument('--jadual', action='store_true', help='cetak jadual semakan tema ke stderr')
    a = ap.parse_args()
    tema = json.load(open(a.tema, encoding='utf8')) if a.tema else {}
    items = bina(a, tema, baca(a.docx))
    assert len(items) == 30, f'dijangka 30 kisah, jumpa {len(items)}'
    if a.jadual:
        for it in items: print(it['no'], '|', it['tema'], '|', it['tajuk'][:60], '|', it.get('subtema', ''), file=sys.stderr)
    blok = ',\n'.join(json.dumps(it, ensure_ascii=False) for it in items)
    if a.fail:
        with open(a.fail, 'w', encoding='utf8') as f:
            f.write(f'(window.STORIES=window.STORIES||[]).push(\n{blok}\n);\n')
    else:
        print(blok)

if __name__ == '__main__':
    main()
