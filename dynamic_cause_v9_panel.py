"""DYNAMIC CAUSE V9 – NASA Space Apps research demonstrator.

Run from the DYNAMIC_CAUSE folder:
    python -m streamlit run dynamic_cause_v9_panel.py --server.port 8509

This dashboard only reads V3/V8 output files. It does NOT open COM9, flash
firmware, modify Arduino sketches, or replace V5. NASA RR-28 is historical
experimental environmental data, NOT live ISS telemetry or crew health data.
"""
from __future__ import annotations

import csv
import io
import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parent
LIVE_FILE = ROOT / "ESP32_canli_veriler_v3.csv"
EVENTS_FILE = ROOT / "ESP32_dokunma_olaylari.csv"
SD_FILE = ROOT / "DC_V8.CSV"
NASA_FILE = ROOT / "RR28_temiz_veri.csv"
CHECKIN_FILE = ROOT / "DYNAMIC_CAUSE_V9_checkins.csv"

LIVE_COLS = ["esp32_millis", "light_adc", "touch", "event_count"]
NASA_FIELDS = {
    "CO₂ (ppm)": ("CO2_ppm_ISS", "CO2_ppm_Ground"),
    "Sıcaklık (°C)": ("Temp_degC_ISS", "Temp_degC_Ground"),
    "Bağıl nem (%)": ("RH_percent_ISS", "RH_percent_Ground"),
}
CHECKIN_COLS = [
    "timestamp_utc", "sleep_hours", "fatigue_0_10", "mood_0_10",
    "symptom_present", "source",
]

st.set_page_config(page_title="DYNAMIC CAUSE V9", page_icon="🛰️", layout="wide")
st.markdown("""
<style>
.block-container {padding-top: 1.6rem; max-width: 1500px;}
.dc-header {border-radius:18px;padding:26px 28px;margin-bottom:18px;
background:linear-gradient(115deg,#0c203b,#173d62 62%,#16616a);
color:white;box-shadow:0 8px 28px rgba(0,0,0,.13)}
.dc-header h1 {color:white;margin:0 0 .35rem 0;font-size:2.25rem;letter-spacing:1px}
.dc-header p {color:#d4e9f0;margin:0;font-size:1rem}
.dc-chip {display:inline-block;border:1px solid #76a9b4;border-radius:20px;
padding:3px 10px;font-size:.77rem;margin-bottom:10px;color:#d7f2f0}
.dc-note {font-size:.85rem;color:#7f91a6}
</style>
""", unsafe_allow_html=True)


def file_state(path: Path) -> str:
    if not path.exists():
        return "Bulunamadı"
    return f"Var · {path.stat().st_size / 1024:.1f} KB"


def read_csv_file(path: Path) -> pd.DataFrame:
    if not path.is_file() or path.stat().st_size == 0:
        return pd.DataFrame()
    try:
        return pd.read_csv(path, on_bad_lines="skip", low_memory=False)
    except (OSError, UnicodeError, ValueError, pd.errors.ParserError, pd.errors.EmptyDataError):
        return pd.DataFrame()


def prepare_sensor(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty or not set(LIVE_COLS).issubset(frame.columns):
        return pd.DataFrame(columns=LIVE_COLS)
    data = frame.copy()
    for col in LIVE_COLS:
        data[col] = pd.to_numeric(data[col], errors="coerce")
    data = data.dropna(subset=LIVE_COLS)
    if "timestamp_utc" in data.columns:
        data["timestamp_utc"] = pd.to_datetime(data["timestamp_utc"], utc=True, errors="coerce")
    return data


def last_sample_time(path: Path, frame: pd.DataFrame) -> datetime | None:
    if not frame.empty and "timestamp_utc" in frame.columns:
        times = pd.to_datetime(frame["timestamp_utc"], utc=True, errors="coerce").dropna()
        if not times.empty:
            return times.max().to_pydatetime()
    if path.is_file():
        return datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
    return None


def freshness(path: Path, frame: pd.DataFrame, seconds: int = 12) -> tuple[bool, str]:
    timestamp = last_sample_time(path, frame)
    if timestamp is None:
        return False, "Veri yok"
    lag = max(0, (datetime.now(timezone.utc) - timestamp).total_seconds())
    return lag <= seconds, f"Son kayıt ~{lag:.0f} saniye önce"


@st.cache_data(show_spinner=False)
def read_nasa_cached(path_string: str, modified: float) -> pd.DataFrame:
    _ = modified  # cache invalidates whenever file modification time changes
    data = pd.read_csv(path_string, low_memory=False, on_bad_lines="skip")
    if "Controller_Time_GMT" in data.columns:
        data["Controller_Time_GMT"] = pd.to_datetime(
            data["Controller_Time_GMT"], utc=True, errors="coerce"
        )
    return data


def get_nasa() -> pd.DataFrame:
    if not NASA_FILE.is_file():
        return pd.DataFrame()
    try:
        return read_nasa_cached(str(NASA_FILE), NASA_FILE.stat().st_mtime)
    except (OSError, ValueError, UnicodeError, pd.errors.ParserError):
        return pd.DataFrame()


def get_checkins() -> pd.DataFrame:
    data = read_csv_file(CHECKIN_FILE)
    if data.empty or not set(CHECKIN_COLS).issubset(data.columns):
        return pd.DataFrame(columns=CHECKIN_COLS)
    for col in ("sleep_hours", "fatigue_0_10", "mood_0_10"):
        data[col] = pd.to_numeric(data[col], errors="coerce")
    data["timestamp_utc"] = pd.to_datetime(data["timestamp_utc"], utc=True, errors="coerce")
    return data.dropna(subset=["timestamp_utc"]).sort_values("timestamp_utc")


def store_checkin(sleep: float, fatigue: int, mood: int, symptom: bool) -> None:
    new_file = not CHECKIN_FILE.exists() or CHECKIN_FILE.stat().st_size == 0
    with CHECKIN_FILE.open("a", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=CHECKIN_COLS)
        if new_file:
            writer.writeheader()
        writer.writerow({
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "sleep_hours": sleep,
            "fatigue_0_10": fatigue,
            "mood_0_10": mood,
            "symptom_present": int(symptom),
            "source": "manual_research_demo",
        })


def demo_checkins() -> pd.DataFrame:
    """Deterministic, clearly SYNTHETIC data for live presentations only."""
    rows = [
        (8.0, 2, 8, 0), (7.5, 3, 7, 0), (7.0, 3, 8, 0),
        (7.5, 2, 7, 0), (7.0, 4, 7, 0), (5.0, 8, 3, 1),
    ]
    result = pd.DataFrame(rows, columns=[
        "sleep_hours", "fatigue_0_10", "mood_0_10", "symptom_present"
    ])
    result["timestamp_utc"] = pd.date_range("2026-11-09", periods=len(result), freq="D", tz="UTC")
    result["source"] = "SYNTHETIC_DEMO"
    return result[CHECKIN_COLS]


def assess_checkin(row: pd.Series) -> list[str]:
    """Illustrative rules, not validated medical cutoffs or diagnosis."""
    notes: list[str] = []
    if pd.notna(row.get("sleep_hours")) and float(row["sleep_hours"]) < 6:
        notes.append("Bildirilen uyku süresi 6 saatin altında (demo kuralı).")
    if pd.notna(row.get("fatigue_0_10")) and float(row["fatigue_0_10"]) >= 7:
        notes.append("Bildirilen yorgunluk 7/10 veya üzerinde (demo kuralı).")
    if pd.notna(row.get("mood_0_10")) and float(row["mood_0_10"]) <= 3:
        notes.append("Bildirilen iyi oluş 3/10 veya altında (demo kuralı).")
    if str(row.get("symptom_present", "0")).strip().lower() in {"1", "1.0", "true", "yes"}:
        notes.append("Katılımcı belirti bildirmiş (öz bildirim).")
    return notes


def baseline_change_flags(data: pd.DataFrame) -> list[str]:
    """Experimental within-person deviation, requires five PREVIOUS records."""
    if len(data) < 6:
        return []
    previous = data.iloc[-6:-1]
    latest = data.iloc[-1]
    flags: list[str] = []
    comparisons = [
        ("sleep_hours", -1.5, "Uyku", "saat", "lower"),
        ("fatigue_0_10", 3.0, "Yorgunluk", "puan", "higher"),
        ("mood_0_10", -3.0, "İyi oluş", "puan", "lower"),
    ]
    for col, threshold, label, unit, direction in comparisons:
        if col not in previous.columns or col not in latest.index:
            continue
        vals = pd.to_numeric(previous[col], errors="coerce").dropna()
        current = pd.to_numeric(pd.Series([latest[col]]), errors="coerce").iloc[0]
        if len(vals) < 5 or pd.isna(current):
            continue
        baseline = float(vals.median())
        delta = float(current) - baseline
        triggered = delta <= threshold if direction == "lower" else delta >= threshold
        if triggered:
            flags.append(f"{label}: kişisel 5-kayıt medyanı {baseline:g}, "
                         f"son bildirim {float(current):g} ({delta:+.1f} {unit}; demo değişim kuralı).")
    return flags


def report_as_json(sensor: pd.DataFrame, sd: pd.DataFrame,
                   nasa: pd.DataFrame, checkins: pd.DataFrame) -> str:
    active, activity = freshness(LIVE_FILE, sensor)
    latest = sensor.iloc[-1] if not sensor.empty else None
    checks = checkins.iloc[-1] if not checkins.empty else None
    report = {
        "project": "DYNAMIC CAUSE V9",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "scope": "NASA Space Apps research demonstration; NOT a medical device",
        "local_hardware": {
            "platform": "ESP32 + Arduino Uno",
            "sensors": "LDR light (ADC), TTP223 touch/event; NOT physiological monitoring",
            "collector_active": active,
            "collector_status": activity,
            "rows_in_local_csv": len(sensor),
            "latest_light_adc": int(latest["light_adc"]) if latest is not None else None,
            "latest_touch": int(latest["touch"]) if latest is not None else None,
            "latest_event_counter_this_boot": int(latest["event_count"]) if latest is not None else None,
        },
        "sd_storage": {
            "file": "DC_V8.CSV", "rows_in_imported_or_local_file": len(sd),
            "time_basis": "ESP32 millis since boot; not actual UTC date/time",
        },
        "nasa_rr28": {
            "file": "RR28_temiz_veri.csv", "rows": len(nasa),
            "data_type": "Historical research environmental telemetry, not live ISS feed",
        },
        "self_reports": {
            "rows": len(checkins),
            "latest_source": str(checks.get("source", "")) if checks is not None else None,
            "latest_rule_triggers": assess_checkin(checks) if checks is not None else [],
            "within_person_baseline_flags": baseline_change_flags(checkins),
        },
        "limitations": [
            "No direct ISS connectivity or astronaut physiological sensor.",
            "No claim that historical RR-28 environmental observations caused local self-reports.",
            "Check-in flags are unvalidated illustrative rules, not clinical decisions.",
            "Sensor boot resets its event counter; accumulated logs are separate.",
        ],
    }
    return json.dumps(report, ensure_ascii=False, indent=2)


with st.sidebar:
    st.subheader("🛰️ DYNAMIC CAUSE")
    st.caption("V9 · Research Mission Dashboard")
    st.markdown("**Dosya bağlantıları**")
    for title, path in [
        ("Canlı ESP32 (V3 collector)", LIVE_FILE),
        ("Dokunma olayları", EVENTS_FILE),
        ("MicroSD kayıt kopyası", SD_FILE),
        ("NASA RR-28", NASA_FILE),
        ("Health check-in", CHECKIN_FILE),
    ]:
        st.caption(f"{title}: {file_state(path)}")
    st.divider()
    st.info("Arduino IDE Serial Monitor kapalı olmalı. COM9 portunu yalnızca V3 Python collector kullanır.")
    st.caption("Orijinal V3, V5, V7 ve V8 dosyaları değişmez.")

st.markdown("""
<div class="dc-header">
  <span class="dc-chip">NASA SPACE APPS · DYNAMIC TEAM · RESEARCH DEMO</span>
  <h1>DYNAMIC CAUSE V9</h1>
  <p>Local sensing · Offline evidence · Historical NASA context · Explainable check-in rules</p>
</div>
""", unsafe_allow_html=True)

st.caption("Veri kaynaklarını ayrı tutar: yerel ESP32 ölçümleri gerçektir; NASA RR-28 geçmiş araştırma verisidir; örnek sağlık bildirimleri sentetiktir.")

tab_live, tab_sd, tab_nasa, tab_health, tab_report = st.tabs([
    "📡 Canlı İstasyon", "💾 MicroSD & Kayıtlar", "🌍 NASA RR-28",
    "🧑‍🚀 Crew Check-in & Karar Desteği", "📋 Kanıt & Sunum Raporu",
])


def render_live() -> None:
    data = prepare_sensor(read_csv_file(LIVE_FILE))
    active, status = freshness(LIVE_FILE, data)
    st.subheader("ESP32 · yerel gerçek ölçüm")
    st.success(f"● Collector güncel — {status}") if active else st.warning(f"● Collector durgun — {status}")
    if data.empty:
        st.info("Canlı CSV henüz okunamadı. `python esp32_veri_toplama_v3.py` komutunu ayrı terminalde çalıştır.")
        return
    latest = data.iloc[-1]
    a, b, c, d = st.columns(4)
    a.metric("Işık ADC", f"{int(latest['light_adc']):,}", help="Ham 12-bit ADC değeri; kalibrasyon olmadan lux değildir.")
    b.metric("Dokunma", "AKTİF" if int(latest["touch"]) else "PASİF")
    c.metric("Oturum olay sayacı", int(latest["event_count"]), help="ESP32 yeniden başladığında sıfırlanır.")
    d.metric("CSV kayıt sayısı", f"{len(data):,}")
    shown = data.tail(350).copy()
    if "timestamp_utc" in shown.columns and shown["timestamp_utc"].notna().any():
        st.line_chart(shown, x="timestamp_utc", y="light_adc", height=270)
    else:
        shown = shown.reset_index(drop=True)
        st.line_chart(shown["light_adc"], height=270)
    st.caption("Işık ölçümü Dünya üzerindeki LDR sensöründen alınır; ISS kabin aydınlığı değildir.")
    with st.expander("Son 12 canlı satır"):
        st.dataframe(data.tail(12).iloc[::-1], hide_index=True, use_container_width=True)


with tab_live:
    if hasattr(st, "fragment"):
        @st.fragment(run_every="2s")
        def live_auto_refresh() -> None:
            render_live()
        live_auto_refresh()
    else:
        if st.button("Veriyi yenile", key="refresh_live"):
            pass
        render_live()

with tab_sd:
    st.subheader("Offline-first · MicroSD delil kaydı")
    st.write("ESP32, `DC_V8.CSV` dosyasına ölçümleri bilgisayara ihtiyaç duymadan kaydeder. Kartı çıkarmadan önce güç kesilmelidir.")
    sd_uploaded = st.file_uploader("İstersen SD karttan DC_V8.CSV dosyasını buraya yükle", type=["csv"], key="sd_file")
    if sd_uploaded is not None:
        try:
            sd_data = prepare_sensor(pd.read_csv(io.BytesIO(sd_uploaded.getvalue()), on_bad_lines="skip"))
            sd_source = "Yüklenen dosya"
        except (OSError, ValueError, UnicodeError, pd.errors.ParserError):
            sd_data = pd.DataFrame()
            sd_source = "Okuma hatası"
    else:
        sd_data = prepare_sensor(read_csv_file(SD_FILE))
        sd_source = "Proje klasöründeki DC_V8.CSV"
    if not sd_data.empty:
        a, b, c = st.columns(3)
        a.metric("SD kayıt sayısı", f"{len(sd_data):,}")
        b.metric("Son ışık ADC", int(sd_data.iloc[-1]["light_adc"]))
        c.metric("Son olay sayacı", int(sd_data.iloc[-1]["event_count"]))
        st.caption(f"Kaynak: {sd_source}. `esp32_millis` açılıştan geçen süredir; gerçek tarih-saat değildir.")
        st.line_chart(sd_data.tail(350).set_index("esp32_millis")["light_adc"], height=240)
        st.dataframe(sd_data.tail(50).iloc[::-1], use_container_width=True, hide_index=True)
        st.download_button("SD verisini CSV indir", sd_data.to_csv(index=False).encode("utf-8-sig"),
                           file_name="DYNAMIC_CAUSE_V9_SD_verileri.csv", mime="text/csv")
    else:
        st.info("MicroSD verisi henüz bu klasöre kopyalanmadı. `DC_V8.CSV` dosyasını yükle veya proje klasörüne kopyala.")

    events = read_csv_file(EVENTS_FILE)
    st.divider()
    st.markdown("#### Dokunma olay kayıtları")
    if events.empty:
        st.caption("Olay CSV henüz bulunamadı.")
    else:
        st.metric("Kaydedilmiş olay satırı", f"{len(events):,}")
        st.dataframe(events.tail(30).iloc[::-1], use_container_width=True, hide_index=True)
        st.caption("Bu toplam, olay CSV satır sayısıdır; yeniden başlatmalardaki sayaçlarla karıştırmayın.")

with tab_nasa:
    st.subheader("NASA RR-28 · tarihsel deneysel çevre verisi")
    st.warning("Bunlar 2024 tarihli ISS/yer kontrol deney verileridir; canlı ISS telemetrisi veya astronot sağlığı ölçümü DEĞİLDİR.")
    nasa = get_nasa()
    if nasa.empty:
        st.error("`RR28_temiz_veri.csv` proje klasöründe bulunamadı veya okunamadı.")
    else:
        qa = nasa["QA_Status"].astype(str) if "QA_Status" in nasa.columns else pd.Series(dtype=str)
        missing_qa = int(qa.str.contains("MISSING", case=False).sum()) if not qa.empty else 0
        aa, bb, cc = st.columns(3)
        aa.metric("NASA veri satırı", f"{len(nasa):,}")
        bb.metric("Eksik değer işaretli", f"{missing_qa:,}")
        cc.metric("Veri türü", "HISTORICAL")
        if "QA_Gap_Minutes_Before" in nasa.columns:
            gaps = pd.to_numeric(nasa["QA_Gap_Minutes_Before"], errors="coerce")
            long_gaps = int((gaps > 1).sum())
            st.caption(f"Kalite kontrol: {long_gaps:,} satırda 1 dakikadan uzun veri boşluğu işaretlenmiş.")
        selected = st.selectbox("Çevresel parametre", list(NASA_FIELDS))
        iss, ground = NASA_FIELDS[selected]
        if {"Controller_Time_GMT", iss, ground}.issubset(nasa.columns):
            cleaned = nasa[["Controller_Time_GMT", iss, ground]].copy()
            cleaned[iss] = pd.to_numeric(cleaned[iss], errors="coerce")
            cleaned[ground] = pd.to_numeric(cleaned[ground], errors="coerce")
            cleaned = cleaned.dropna(subset=["Controller_Time_GMT"]).sort_values("Controller_Time_GMT")
            if not cleaned.empty:
                plot = cleaned.tail(2500).rename(columns={iss: "ISS (historical)", ground: "Ground (historical)"})
                st.line_chart(plot, x="Controller_Time_GMT", y=["ISS (historical)", "Ground (historical)"], height=330)
                st.caption(f"Ölçülen geçmiş zaman aralığı: {cleaned['Controller_Time_GMT'].min()} – {cleaned['Controller_Time_GMT'].max()}")
            else:
                st.info("Seçilen parametrede çizilecek geçerli zaman noktası bulunamadı.")
        else:
            st.warning("Beklenen NASA sütunlarından biri eksik.")
        with st.expander("Veri kalitesi ve ham satırlar"):
            st.dataframe(nasa.head(50), use_container_width=True, hide_index=True)
            st.caption("QA_Status ve eksik değerler korunur; doğrulama olmadan doldurulmaz.")

with tab_health:
    st.subheader("Crew Health Check-in · açıklanabilir kural motoru")
    st.info("Bu alan, demo katılımcısının öz bildirimini işler. Gerçek astronot sağlık kaydı değildir; teşhis veya klinik karar üretmez.")
    with st.form("checkin_form"):
        x, y, z = st.columns(3)
        sleep = x.slider("Uyku (saat)", 0.0, 14.0, 7.0, 0.5)
        fatigue = y.slider("Yorgunluk (0–10)", 0, 10, 3)
        mood = z.slider("İyi oluş (0–10)", 0, 10, 7)
        symptom = st.checkbox("Belirti bildirildi (evet/hayır)")
        save = st.form_submit_button("Check-in kaydet", type="primary")
    if save:
        try:
            store_checkin(sleep, fatigue, mood, symptom)
            st.success("Öz bildirim, V9 check-in CSV'sine kaydedildi.")
        except OSError as error:
            st.error(f"Check-in dosyası yazılamadı: {error}")

    use_synthetic = st.toggle("Sunum için sentetik senaryoyu göster", value=False)
    if use_synthetic:
        data = demo_checkins()
        st.warning("SENTETİK DEMO VERİSİ: Bu kayıtlar gerçek kişi veya astronotlara ait değildir.")
    else:
        data = get_checkins()

    if data.empty:
        st.caption("Değerlendirme yapmak için formu doldur veya sentetik senaryoyu aç.")
    else:
        current = data.iloc[-1]
        triggers = assess_checkin(current)
        personal_flags = baseline_change_flags(data)
        if triggers or personal_flags:
            st.warning(f"İNCELEME ÖNERİSİ · {len(triggers) + len(personal_flags)} açıklanabilir demo kuralı tetiklendi.")
            for reason in triggers:
                st.write("• " + reason)
            for reason in personal_flags:
                st.write("• " + reason)
            st.caption("Önerilen aksiyon: Bildirimi gözden geçir, tekrar ölçüm/öz bildirim al; gerektiğinde yetkili uzmana yönlendir.")
        else:
            st.success("Bu gösterim kurallarına göre bildirim yok. Bu, sağlığın normal olduğunu kanıtlamaz.")
        if len(data) < 6:
            st.caption("Kişisel değişim kontrolü için en az 5 önceki ve 1 yeni bildirim gerekir; sabit eşik kuralları yine çalışır.")
        c1, c2, c3 = st.columns(3)
        c1.metric("Son uyku", f"{float(current['sleep_hours']):.1f} saat")
        c2.metric("Son yorgunluk", f"{int(current['fatigue_0_10'])}/10")
        c3.metric("Son iyi oluş", f"{int(current['mood_0_10'])}/10")
        chart = data[["timestamp_utc", "sleep_hours", "fatigue_0_10", "mood_0_10"]].copy()
        st.line_chart(chart, x="timestamp_utc", y=["sleep_hours", "fatigue_0_10", "mood_0_10"], height=250)
        with st.expander("Kural açıklaması ve ölçümlerin kaynağı"):
            st.write("Örnek sabit eşikler: uyku <6 saat, yorgunluk ≥7/10, iyi oluş ≤3/10 veya belirti bildirimi. "
                     "Kişisel değişim örnekleri: önceki 5 kaydın medyanına göre uyku -1,5 saat, yorgunluk +3, iyi oluş -3. "
                     "Bunlar klinik ya da NASA operasyon eşikleri değildir.")
            st.dataframe(data.tail(20).iloc[::-1], hide_index=True, use_container_width=True)

with tab_report:
    st.subheader("Evidence Engine · kaynak ayrımı ve teslim raporu")
    st.write("Veri kökeni ve bilimsel sınırlamalar sunumda açıkça gösterilir; farklı deneylerden nedensellik çıkarılmaz.")
    sources = pd.DataFrame([
        {"Kaynak": "Yerel ESP32", "Ne ölçüyor?": "Işık ADC, dokunma ve olay", "Nitelik": "Gerçek yerel donanım", "Canlı ISS?": "Hayır"},
        {"Kaynak": "MicroSD", "Ne ölçüyor?": "ESP32 ölçüm arşivi", "Nitelik": "Offline yerel kayıt", "Canlı ISS?": "Hayır"},
        {"Kaynak": "NASA RR-28", "Ne ölçüyor?": "Geçmiş CO₂, sıcaklık, nem", "Nitelik": "Tarihsel araştırma", "Canlı ISS?": "Hayır"},
        {"Kaynak": "Check-in", "Ne ölçüyor?": "Uyku/yorgunluk/iyi oluş bildirimi", "Nitelik": "Manuel veya sentetik demo", "Canlı ISS?": "Hayır"},
    ])
    st.dataframe(sources, hide_index=True, use_container_width=True)
    with st.expander("DYNAMIC CAUSE nasıl çalışır?", expanded=True):
        st.markdown("""
        **1. Acquire:** ESP32'nin LDR/TTP223 ölçümleri USB seri ve MicroSD üzerinden kaydedilir.  
        **2. Preserve:** Yerel CSV ve SD CSV ayrı saklanır, kaynağı belirtilir.  
        **3. Contextualize:** NASA RR-28'in *tarihsel* ISS/yer deney koşulları ayrı grafikte incelenir.  
        **4. Check-in:** Manuel veya açıkça sentetik bildirimler demo kurallarıyla değerlendirilir.  
        **5. Explain:** Hangi kuralın tetiklendiği ve hangi veriye dayandığı gösterilir.
        """)
    live = prepare_sensor(read_csv_file(LIVE_FILE))
    uploaded_sd = st.session_state.get("sd_file")
    if uploaded_sd is not None:
        try:
            sd = prepare_sensor(pd.read_csv(io.BytesIO(uploaded_sd.getvalue()), on_bad_lines="skip"))
        except (OSError, ValueError, UnicodeError, pd.errors.ParserError):
            sd = pd.DataFrame()
    else:
        sd = prepare_sensor(read_csv_file(SD_FILE))
    nasa = get_nasa()
    checkins = get_checkins()
    if st.session_state.get("report_synthetic", False):
        checkins = demo_checkins()
    st.checkbox("Raporda sentetik check-in senaryosunu kullan", key="report_synthetic")
    # Update immediately on checkbox change (no existing source modified).
    if st.session_state.get("report_synthetic", False):
        checkins = demo_checkins()
    report = report_as_json(live, sd, nasa, checkins)
    st.download_button("⬇️ V9 kanıt raporunu JSON indir", report.encode("utf-8"),
                       file_name="DYNAMIC_CAUSE_V9_EVIDENCE.json", mime="application/json", type="primary")
    with st.expander("Raporun içeriğini gör"):
        st.code(report, language="json")
    st.warning("Bilimsel sınır: Bu prototip astronotların nabzını, SpO₂ değerini veya diğer fizyolojik parametrelerini ölçmüyor; güvenlik-kritik karar vermiyor.")

st.divider()
st.caption("DYNAMIC CAUSE V9 · Space Apps prototype · Offline-first · Source-aware · Explainable research demo")