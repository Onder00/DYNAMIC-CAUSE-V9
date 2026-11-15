#!/usr/bin/env python3
"""NASA RR-28 EDA telemetri verisi: kayıpsız, izlenebilir ilk temizlik.
Kullanım: python RR28_temizle.py RR-28_EDA_Telemetry_data.csv
Python standart kütüphanesi yeterlidir; pandas gerektirmez.
"""
import csv
import sys
from collections import defaultdict, Counter
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path

SOURCE = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('RR-28_EDA_Telemetry_data.csv')
OUTDIR = SOURCE.parent
CLEAN = OUTDIR / 'RR28_temiz_veri.csv'
DUP = OUTDIR / 'RR28_tekrar_kayitlari.csv'
REPORT = OUTDIR / 'RR28_temizlik_raporu.txt'
TIME = 'Controller_Time_GMT'
MISSING = {'', 'nan', 'na', 'null', 'none'}

# 1) Ham dosyayı aç: NaN değerlerini boşluğa çevir, sayıları doğrula.
with SOURCE.open('r', encoding='utf-8-sig', newline='') as fh:
    reader = csv.DictReader(fh)
    fields = list(reader.fieldnames or [])
    if TIME not in fields:
        raise ValueError(f'Tarih sütunu bulunamadı: {TIME}')
    measure_fields = [x for x in fields if x != TIME]
    groups = defaultdict(list)
    original_count = 0
    raw_missing = Counter()
    for line_no, row in enumerate(reader, start=2):
        original_count += 1
        data = {}
        for key in fields:
            s = (row.get(key) or '').strip()
            if s.lower() in MISSING:
                s = ''
                if key != TIME:
                    raw_missing[key] += 1
            elif key != TIME:
                try:
                    n = Decimal(s)
                except InvalidOperation:
                    raise ValueError(f'Sayısal olmayan değer, satır {line_no}: {key}={s!r}')
                if not n.is_finite():
                    raise ValueError(f'Sonlu olmayan değer, satır {line_no}: {key}={s!r}')
            data[key] = s
        try:
            stamp = datetime.strptime(data[TIME], '%Y-%m-%d %H:%M')
        except ValueError as exc:
            raise ValueError(f'Hatalı tarih, satır {line_no}: {data[TIME]}') from exc
        groups[stamp].append((line_no, data))

# 2) Aynı zamana ait kayıtlar: ortak değerleri koru, çelişenleri boş bırak.
clean_rows, dup_rows = [], []
conflict_count = Counter()
for stamp in sorted(groups):
    sources = groups[stamp]
    merged = {TIME: stamp.strftime('%Y-%m-%d %H:%M')}
    conflicts = []
    for col in measure_fields:
        available = [r[col] for _, r in sources if r[col] != '']
        distinct = {Decimal(v) for v in available}
        if len(distinct) > 1:
            merged[col] = ''  # çatışan gerçek ölçümlerden birini seçme!
            conflicts.append(col)
            conflict_count[col] += 1
        else:
            merged[col] = available[0] if available else ''
    if len(sources) > 1:
        for line_no, source in sources:
            dup_rows.append({'Original_CSV_Line': line_no, **source})
    missing_cols = [c for c in measure_fields if not merged[c]]
    flags = []
    if len(sources) > 1:
        flags.append('DUPLICATE_MERGED')
    if conflicts:
        flags.append('CONFLICTING_MEASUREMENTS')
    if missing_cols:
        flags.append('MISSING_VALUES')
    merged.update({
        'QA_Source_Row_Count': len(sources),
        'QA_Conflict_Columns': ';'.join(conflicts),
        'QA_Missing_Columns': ';'.join(missing_cols),
        'QA_Gap_Minutes_Before': '',
        'QA_Status': ';'.join(flags) or 'OK'
    })
    clean_rows.append(merged)

# 3) Önceki ölçüme göre zaman boşluğunu hesapla; doldurma yapma.
gap_counts = Counter()
prev = None
for row in clean_rows:
    stamp = datetime.strptime(row[TIME], '%Y-%m-%d %H:%M')
    if prev is not None:
        delta = int((stamp - prev).total_seconds() / 60)
        row['QA_Gap_Minutes_Before'] = delta
        if delta > 1:
            gap_counts[delta] += 1
            row['QA_Status'] += (';' if row['QA_Status'] != 'OK' else '') + 'TIME_GAP_BEFORE'
            row['QA_Status'] = row['QA_Status'].removeprefix('OK;')
    prev = stamp

# 4) Ham dosyaya dokunmadan yeni dosyaları yaz.
quality_fields = [
    'QA_Source_Row_Count', 'QA_Conflict_Columns', 'QA_Missing_Columns',
    'QA_Gap_Minutes_Before', 'QA_Status'
]
with CLEAN.open('w', encoding='utf-8-sig', newline='') as fh:
    writer = csv.DictWriter(fh, fieldnames=fields + quality_fields)
    writer.writeheader()
    writer.writerows(clean_rows)
with DUP.open('w', encoding='utf-8-sig', newline='') as fh:
    writer = csv.DictWriter(fh, fieldnames=['Original_CSV_Line'] + fields)
    writer.writeheader()
    writer.writerows(dup_rows)

merged_groups = sum(len(v) > 1 for v in groups.values())
missing_after = Counter({c: sum(not row[c] for row in clean_rows) for c in measure_fields})
text = [
    'NASA RR-28 — Veri Temizleme Raporu',
    'Kaynak: NASA Environmental Data Application (EDA), RR-28 Telemetry',
    f'Ham dosya: {SOURCE.name}',
    f'Ham kayıt sayısı: {original_count:,}',
    f'Temiz zaman kaydı sayısı: {len(clean_rows):,}',
    f'Birleştirilen tekrar grubu: {merged_groups}',
    f'Tekrar grup kaynak satırları: {len(dup_rows)}',
    f'Toplam çelişkili ölçüm hücresi: {sum(conflict_count.values())}',
    f'Ham eksik ölçüm hücresi: {sum(raw_missing.values())}',
    f'Temiz dosyadaki boş ölçüm hücresi: {sum(missing_after.values())}',
    f'1 dakikadan uzun zaman boşluğu: {sum(gap_counts.values())}',
    f'En büyük boşluk (dakika): {max(gap_counts, default=0)}',
    f'Zaman aralığı (GMT): {clean_rows[0][TIME]} — {clean_rows[-1][TIME]}',
    'Ham eksikler: ' + str(dict(raw_missing)),
    'Çelişen sütunlar: ' + str(dict(conflict_count)),
    'Temiz dosyada boş sütunlar: ' + str(dict(missing_after)),
    '',
    'Yöntem: NaN→boş; tekrarlanan zamanlarda yalnızca çelişmeyen değerler korundu.',
    'Çelişen hücreler boş bırakıldı; özgün satırlar ayrı dosyada saklandı.',
    'Zaman boşlukları doldurulmadı; yüksek CO2 değerleri otomatik silinmedi.',
    'ISS ve Ground sütunları ayrı bırakıldı. Tanısal eşik uygulanmadı.',
    f'Çıktı: {CLEAN.name}',
    f'Tekrar kayıt denetimi: {DUP.name}',
]
REPORT.write_text('\n'.join(text) + '\n', encoding='utf-8')
print('\n'.join(text))