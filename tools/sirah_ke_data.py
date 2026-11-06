#!/usr/bin/env python3
"""docx 'Cerita Copywriting Thread' (Sirah/Sahabat) -> data/<siri>.js (tiada dependency).

Guna:  python3 -I tools/sirah_ke_data.py "Set.docx" --siri Sirah-01 --mula 1001 --tema tema.json --fail data/Sirah-01.js
Struktur docx: jadual indeks (No., Tokoh/Babak, Kategori, Fasa, Tajuk, Ibrah, Sumber) -> `Cerita #NN: Tajuk`
-> [Garis Masa / Rujukan] -> ` [COPY DARI SINI]` ... teks ... ` [TAMAT]`.
Teks yang disalin = antara dua penanda tersebut.  Tema automatik ikut kata kunci; ganti dengan --tema.
"""
import argparse, importlib.util, json, os, re, sys

here = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location('dk', os.path.join(here, 'docx_ke_data.py'))
dk = importlib.util.module_from_spec(spec); spec.loader.exec_module(dk)

KEYWORD = [
 ('Kepimpinan & Keberanian', ['keberanian','panglima','pahlawan','perang','pemimpin','kepimpinan','pedang','syahid','strategi','panji','jihad','tentera','khalid','kemenangan','ketegasan','akauntabiliti']),
 ('Infaq & Harta', ['infaq','sedekah','harta','wakaf','dermawan','kedermawanan','kekayaan','jutawan','hutang','rezeki','kewangan','pusaka','bisnes','peniaga','perniagaan','kurma','unta']),
 ('Taubat & Hidayah', ['taubat','hidayah','ampun','keampunan','pintu taubat','memeluk islam','dosa','memaafkan','kemaafan']),
 ('Sabar & Tawakal', ['sabar','tawakal','ketabahan','ujian','musibah','lapar','penghinaan','ketenangan','redha','kesempitan','ketahanan','fitnah','boikot','pemulauan']),
 ('Ilmu & Dakwah', ['ilmu','dakwah','al-quran','quran','pendidikan','hafaz','ilmuwan','mengajar','menegur','mendidik','bacaan','hadis','pengajaran','fiqh']),
 ('Keluarga & Wanita', ['isteri','ibu','keluarga','wanita','puteri','anak','suami','ummul','khadijah','aisyah','fatimah','sahabiyyah','ummu']),
 ('Akhlak & Adab', ['akhlak','adab','malu','amanah','jujur','kejujuran','senyuman','kasih sayang','rahmat','tetamu','persaudaraan','ukhuwah','rendah','tawaduk']),
]
def auto_tema(*teks):
    t = ' ' + ' '.join(teks).lower() + ' '
    best, skor = 'Akhlak & Adab', 0
    for nama, kws in KEYWORD:
        s = sum(t.count(k) for k in kws)
        if s > skor: best, skor = nama, s
    return best

def jadual_indeks(paras):
    h = next(i for i, (t, _) in enumerate(paras[:30]) if t == 'No.')
    first = [i for i, (t, _) in enumerate(paras) if re.fullmatch(r'#\d+', t)]
    ncol = first[1] - first[0]
    cols = [t for t, _ in paras[h:first[0]]]
    assert len(cols) == ncol, f'kolum indeks {len(cols)} != {ncol}'
    rows = []
    for i in first:
        cells = paras[i:i + ncol]
        d = {}
        for name, (t, l) in zip(cols, cells):
            n = name.lower()
            if n.startswith('no'): continue
            if 'tokoh' in n or 'babak' in n: d['nama'] = t
            elif 'kategori' in n: d['subtema'] = t
            elif 'fasa' in n: d['garis'] = t
            elif 'tajuk' in n: d['tajukIdx'] = t
            elif 'ibrah' in n: d['ibrah'] = t
            elif 'sumber' in n or 'rujukan' in n: d['sumber'] = t; d['link'] = l[0] if l else ''
        rows.append(d)
    return rows, first[0]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('docx'); ap.add_argument('--siri', required=True)
    ap.add_argument('--mula', type=int, required=True); ap.add_argument('--tema'); ap.add_argument('--fail')
    ap.add_argument('--jadual', action='store_true')
    a = ap.parse_args()
    tema = json.load(open(a.tema, encoding='utf8')) if a.tema else {}
    paras = dk.baca(a.docx)
    rows, _ = jadual_indeks(paras)
    hs = [i for i, (t, _) in enumerate(paras) if re.match(r'^Cerita\s*#\d+\s*:', t, re.I)]
    assert len(hs) == 30 == len(rows), f'cerita {len(hs)}, baris indeks {len(rows)}'
    items = []
    for n, i in enumerate(hs):
        end = hs[n + 1] if n + 1 < len(hs) else len(paras)
        blok = [t for t, _ in paras[i + 1:end]]
        title = re.sub(r'^Cerita\s*#\d+\s*:\s*', '', paras[i][0], flags=re.I).strip()
        a0 = next(k for k, t in enumerate(blok) if 'COPY DARI SINI' in t)
        a1 = next(k for k, t in enumerate(blok) if '[TAMAT]' in t)
        meta = ' '.join(t for t in blok[:a0] if t)
        body = [t for t in blok[a0 + 1:a1] if t.strip()]
        assert len(body) >= 8, f'Cerita {n+1}: teks terlalu pendek ({len(body)})'
        garis = rows[n].get('garis', '')
        m = re.search(r'Garis Masa:\s*(.*?)(?:Rujukan Sahih:|$)', meta)
        if m and m.group(1).strip(): garis = m.group(1).strip()
        hook = body.pop(0)
        r = rows[n]
        tm = tema.get(str(n + 1)) or auto_tema(title, r.get('subtema', ''), r.get('ibrah', ''))
        it = dict(id=a.mula + n, siri=a.siri, no=n + 1, nama=r.get('nama', ''), tajuk=title, lokasi=garis, tahun='',
                  subtema=r.get('subtema', ''), ibrah=r.get('ibrah', ''), sumber=r.get('sumber', ''), link=r.get('link', ''),
                  tema=tm, hook=hook, body=body)
        assert it['link'].startswith('http'), f'Cerita {n+1}: pautan sumber tiada'
        items.append({k: v for k, v in it.items() if v != ''})
    if a.jadual:
        for it in items: print(it['no'], '|', it['tema'], '|', it['tajuk'][:70], '|', it.get('ibrah', '')[:60], file=sys.stderr)
    blok = ',\n'.join(json.dumps(it, ensure_ascii=False) for it in items)
    if a.fail:
        open(a.fail, 'w', encoding='utf8').write(f'(window.STORIES=window.STORIES||[]).push(\n{blok}\n);\n')
    else:
        print(blok)

if __name__ == '__main__':
    main()
