import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from statsmodels.tsa.stattools import grangercausalitytests
import warnings
import json
import plotly.express as px

# Mengabaikan warning dari statsmodels agar tampilan terminal tetap bersih
warnings.filterwarnings('ignore')

# ---------------------------------------------------------
# 1. KONFIGURASI DAN DATA LOADING 
# ---------------------------------------------------------
st.set_page_config(page_title="Dashboard Kausalitas PDRB & PBB", layout="wide")

@st.cache_data
def load_data():
    # GANTI NAMA FILE INI dengan nama file CSV hasil ekspor dari Colab Anda
    df = pd.read_csv('Data_Final_Strictly_Balanced_2014_2023.csv') 
    return df

try:
    df = load_data()
except FileNotFoundError:
    st.error("File CSV tidak ditemukan. Pastikan file hasil ekspor Colab berada di folder yang sama dengan app.py.")
    st.stop()

# Load GeoJSON Peta Indonesia
@st.cache_data
def load_geojson():
    # Pastikan nama file ini sesuai dengan yang Anda unduh
    with open('indonesia.geojson', 'r', encoding='utf-8') as f:
        return json.load(f)

# Load Tabel Hasil Granger Pre-Computed
@st.cache_data
def load_granger_map_data():
    return pd.read_csv('tabel_hasil_granger_peta.csv')

geojson_indonesia = load_geojson()
df_granger_map = load_granger_map_data()

# =========================================================
# KODE SAKTI: PENYELARASAN STRING SPASIAL (Kamus Resolusi)
# =========================================================
# Format: "NAMA DI CSV ANDA": "Nama di GeoJSON"
# Isi kamus ini berdasarkan temuan dari alat diagnostik Anda tadi.
# Anda cukup menuliskan provinsi yang namanya berbeda saja.

kamus_koreksi_provinsi = {
    "DAERAH KHUSUS IBUKOTA JAKARTA": "Daerah Khusus Ibukota Jakarta",
    "JAWA BARAT": "Jawa Barat",
    "ACEH": "Aceh",
    "KEPULAUAN BANGKA BELITUNG": "Bangka Belitung",
    "DERAH ISTIMEWA YOGYAKARTA": "Daerah Istimewa Yogyakarta",
    "SUMATERA UTARA": "Sumatera Utara",
    "SUMATERA BARAT": "Sumatera Barat",
    "SUMATERA SELATAN": "Sumatera Selatan",
    "RIAU": "Riau",
    "KEPULAUAN RIAU": "Kepulauan Riau",
    "JAMBI": "Jambi",
    "BENGKULU": "Bengkulu",
    "LAMPUNG": "Lampung",
    "BANTEN": "Banten",
    "JAWA TENGAH": "Jawa Tengah",
    "JAWA TIMUR": "Jawa Timur",
    "KALIMANTAN BARAT": "Kalimantan Barat",
    "KALIMANTAN SELATAN": "Kalimantan Selatan",
    "KALIMANTAN TENGAH": "Kalimantan Tengah",
    "KALIMANTAN TIMUR": "Kalimantan Timur",
    "KALIMANTAN UTARA": "Kalimantan Utara",
    "BALI": "Bali",
    "NUSA TENGGARA BARAT": "Nusa Tenggara Barat",
    "NUSA TENGGARA TIMUR": "Nusa Tenggara Timur",
    "SULAWESI SELATAN": "Sulawesi Selatan",
    "SULAWESI BARAT": "Sulawesi Barat",
    "SULAWESI TENGGARA": "Sulawesi Tenggara",
    "SULAWESI TENGAH": "Sulawesi Tengah",
    "GORONTALO": "Gorontalo",
    "SULAWESI UTARA": "Sulawesi Utara",
    "MALUKU": "Maluku",
    "MALUKU UTARA": "Maluku Utara",
    "PAPUA": "Papua",
    "PAPUA BARAT": "Papua Barat",
    "PAPUA BARAT DAYA": "Papua Barat Daya",
    "PAPUA PEGUNUNGAN": "Papua Pegunungan",
    "PAPUA SELATAN": "Papua Selatan",
    "PAPUA TENGAH": "Papua Tengah"
}

# Terapkan kamus ke dataframe peta Anda
df_granger_map['PROVINSI'] = df_granger_map['PROVINSI'].replace(kamus_koreksi_provinsi)

# Opsional: Jika dataframe grafik trend (df) Anda juga menggunakan nama lama, 
# selaraskan juga agar dropdown tidak bentrok (jika diperlukan)
df['PROVINSI'] = df['PROVINSI'].replace(kamus_koreksi_provinsi)


# ---------------------------------------------------------
# 2. SIDEBAR (KONTROL PENGGUNA)
# ---------------------------------------------------------
st.sidebar.header("Parameter Analisis")

# Sesuaikan dengan nama kolom aktual di CSV Anda
daftar_provinsi = df['PROVINSI'].unique()
daftar_sektor = df['SEKTOR'].unique()

provinsi_terpilih = st.sidebar.selectbox("Pilih Provinsi:", daftar_provinsi)
sektor_terpilih = st.sidebar.selectbox("Pilih Sektor:", daftar_sektor)

# Filter dataset
df_filtered = df[(df['PROVINSI'] == provinsi_terpilih) & (df['SEKTOR'] == sektor_terpilih)]
df_filtered = df_filtered.sort_values('SERIES') # Pastikan urutan waktu benar

# ---------------------------------------------------------
# 3. AREA VISUALISASI TREN (DUAL-AXIS)
# ---------------------------------------------------------
st.title("Analisis Prediktabilitas PDRB dan Penerimaan PBB")
st.subheader(f"Wilayah: {provinsi_terpilih} | Sektor: {sektor_terpilih}")

fig = go.Figure()

# Garis PDRB (Sumbu Y Kiri)
fig.add_trace(go.Scatter(
    x=df_filtered['SERIES'], y=df_filtered['NILAI_PDRB'],
    name="Nilai PDRB", mode='lines+markers', line=dict(color='#1f77b4')
))

# Garis PBB (Sumbu Y Kanan)
fig.add_trace(go.Scatter(
    x=df_filtered['SERIES'], y=df_filtered['NILAI_PBB'],
    name="Nilai PBB", mode='lines+markers', line=dict(color='#ff7f0e'),
    yaxis='y2'
))

fig.update_layout(
    title="Tren Pergerakan Nilai (2014 S2 - 2023 S2)",
    
    # PERBAIKAN: Menambahkan type='category' agar Plotly tidak menyingkat angka
    xaxis=dict(
        title="Semester (Tahun & Urutan)",
        type='category' 
    ),
    
    yaxis=dict(
        title=dict(text="Nilai PDRB", font=dict(color='#1f77b4')), 
        tickfont=dict(color='#1f77b4')
    ),
    yaxis2=dict(
        title=dict(text="Nilai PBB", font=dict(color='#ff7f0e')), 
        tickfont=dict(color='#ff7f0e'), 
        overlaying='y', side='right'
    ),
    
    legend=dict(x=0.01, y=0.99, bgcolor='rgba(255,255,255,0.7)'),
    height=500
)

st.plotly_chart(fig, use_container_width=True)
st.markdown("---")

# ---------------------------------------------------------
# 4.  AREA PETA KLOROPLET (SPASIAL)
# ---------------------------------------------------------
st.markdown("---")
st.header("Peta Persebaran Signifikansi Kausalitas (First Difference)")
st.caption("Peta ini memvisualisasikan hasil pra-komputasi uji stasioneritas dan Granger secara spasial. Hanya memuat data untuk sektor yang Anda pilih di Sidebar.")

# Arah Kausalitas (Radio button untuk memilih visualisasi peta)
arah_uji = st.radio(
    "Pilih Arah Kausalitas untuk Dipetakan:",
    ('Δ PDRB ➔ Δ PBB (PDRB memprediksi PBB)', 'Δ PBB ➔ Δ PDRB (PBB memprediksi PDRB)'),
    horizontal=True
)

# Menentukan kolom target dari CSV berdasarkan pilihan radio button
# Sesuaikan nama string 'SIGNIFIKAN_...' ini dengan header asli di CSV hasil ekspor Anda
kolom_target = 'SIGNIFIKAN_PDRB_ke_PBB' if arah_uji == 'Δ PDRB ➔ Δ PBB (PDRB memprediksi PBB)' else 'SIGNIFIKAN_PBB_ke_PDRB'

# Filter data tabel Granger HANYA berdasarkan Sektor yang dipilih pengguna di sidebar
# Kita tidak memfilter provinsi, karena peta butuh seluruh 23 provinsi
df_map_filtered = df_granger_map[df_granger_map['SEKTOR'] == sektor_terpilih]

# Menyiapkan palet warna tegas untuk pengambil keputusan
color_discrete_map = {'Signifikan': '#2ca02c', 'Tidak Signifikan': '#d62728'} 

try:
    fig_map = px.choropleth_mapbox(
        df_map_filtered,
        geojson=geojson_indonesia,
        locations='PROVINSI', # Nama kolom di dataframe Anda
        
        # PERHATIAN KRITIS: 'featureidkey' adalah kunci penghubung GeoJSON dan CSV Anda.
        # Jika di GeoJSON nama provinsinya ada di dalam "properties" -> "state", maka isikan "properties.state".
        # Jika di "properties" -> "name", maka isikan "properties.name".
        featureidkey="properties.PROVINSI", 
        
        color=kolom_target,
        color_discrete_map=color_discrete_map,
        mapbox_style="carto-positron",
        zoom=3.8,
        center={"lat": -2.5489, "lon": 118.0149}, # Titik tengah kepulauan Indonesia
        opacity=0.8,
        hover_name='PROVINSI',
        hover_data={'PROVINSI': False, kolom_target: True},
        labels={kolom_target: 'Status Kausalitas'}
    )
    
    fig_map.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
    st.plotly_chart(fig_map, use_container_width=True)

except Exception as e:
    st.error(f"Gagal merender peta. Kemungkinan besar karena ketidakcocokan kunci `featureidkey` antara data CSV dengan struktur file GeoJSON Anda. Detail: {e}")

# ---------------------------------------------------------
# 5. MESIN EKONOMETRIKA & NARASI
# ---------------------------------------------------------
st.subheader("Pengujian Kausalitas Granger (Short-term Predictability)")
st.caption("Catatan Metodologi: Data secara otomatis ditransformasi menggunakan First Difference (ΔY) untuk memastikan stasioneritas. Jeda waktu (lag) dikunci pada 1 semester mengingat limitasi jumlah observasi waktu (T=19).")

narasi_kebijakan = {
    "PBB_mempengaruhi_PDRB": "Berdasarkan pengujian, akselerasi penerimaan PBB memiliki daya prediksi terhadap akselerasi PDRB di semester berikutnya. Secara literatur, ini mengindikasikan bahwa optimalisasi pajak bumi bangunan berkorelasi dengan peningkatan aktivitas ekonomi wilayah, kemungkinan melalui belanja daerah produktif yang didanai oleh pajak tersebut.",
    "PDRB_mempengaruhi_PBB": "Pertumbuhan PDRB terbukti memprediksi pertumbuhan penerimaan PBB ke depan. Ekspansi ekonomi di sektor dan provinsi ini secara langsung memperlebar basis pemajakan, sehingga otoritas pajak dapat memproyeksikan peningkatan penerimaan pada semester mendatang.",
    "Bi_directional": "Terdapat hubungan prediktabilitas dua arah (Bi-directional). Akselerasi PDRB mendorong basis PBB, dan penerimaan PBB yang kembali ke daerah tersebut (melalui bagi hasil/belanja) membantu menstimulasi PDRB di semester berikutnya. Ini menunjukkan interaksi fiskal dan ekonomi yang sangat sehat.",
    "Tidak_Signifikan": "Tidak ditemukan bukti kausalitas prediktif (Granger) antar kedua variabel pada sektor dan wilayah ini. Fluktuasi penerimaan PBB dan PDRB kemungkinan bergerak secara independen, bersifat inelastis dalam jangka pendek (6 bulan), atau lebih dipengaruhi oleh variabel makroekonomi lain di luar model ini."
}

if st.button("Jalankan Uji Ekonometrika", type="primary"):
    with st.spinner('Melakukan diferensiasi data dan menghitung OLS...'):
        
        # 1. Isolasi dan Stasioneritas (First Difference)
        data_uji = df_filtered[['NILAI_PBB', 'NILAI_PDRB']].copy()
        data_diff = data_uji.diff().dropna()
        
        try:
            # 2. Eksekusi Granger
            max_lag = 1
            
            # PDRB -> PBB
            gc_pdrb_to_pbb = grangercausalitytests(data_diff[['NILAI_PBB', 'NILAI_PDRB']], maxlag=[max_lag], verbose=False)
            p_val_pdrb_to_pbb = gc_pdrb_to_pbb[max_lag][0]['ssr_ftest'][1]
            
            # PBB -> PDRB
            gc_pbb_to_pdrb = grangercausalitytests(data_diff[['NILAI_PDRB', 'NILAI_PBB']], maxlag=[max_lag], verbose=False)
            p_val_pbb_to_pdrb = gc_pbb_to_pdrb[max_lag][0]['ssr_ftest'][1]
            
            # 3. Tampilan Hasil
            col1, col2 = st.columns(2)
            # Logika pewarnaan metrik Streamlit (inverse karena p-value kecil = bagus)
            delta_color_1 = "normal" if p_val_pdrb_to_pbb < 0.05 else "inverse"
            delta_color_2 = "normal" if p_val_pbb_to_pdrb < 0.05 else "inverse"
            
            col1.metric("P-Value (Δ PDRB ➔ Δ PBB)", f"{p_val_pdrb_to_pbb:.4f}", 
                        "Signifikan (H0 Ditolak)" if p_val_pdrb_to_pbb < 0.05 else "Tidak Signifikan",
                        delta_color=delta_color_1)
            
            col2.metric("P-Value (Δ PBB ➔ Δ PDRB)", f"{p_val_pbb_to_pdrb:.4f}", 
                        "Signifikan (H0 Ditolak)" if p_val_pbb_to_pdrb < 0.05 else "Tidak Signifikan",
                        delta_color=delta_color_2)
            
            # 4. Tampilan Narasi Kebijakan
            st.markdown("### Kesimpulan & Implikasi Analitis")
            if p_val_pdrb_to_pbb < 0.05 and p_val_pbb_to_pdrb > 0.05:
                st.info(narasi_kebijakan["PDRB_mempengaruhi_PBB"])
            elif p_val_pbb_to_pdrb < 0.05 and p_val_pdrb_to_pbb > 0.05:
                st.success(narasi_kebijakan["PBB_mempengaruhi_PDRB"])
            elif p_val_pdrb_to_pbb < 0.05 and p_val_pbb_to_pdrb < 0.05:
                st.warning(narasi_kebijakan["Bi_directional"])
            else:
                st.error(narasi_kebijakan["Tidak_Signifikan"])

        except Exception as e:
            st.error(f"Uji statistik gagal dieksekusi. Varians data mungkin bernilai nol atau terdapat data konstan. Detail error: {e}")
