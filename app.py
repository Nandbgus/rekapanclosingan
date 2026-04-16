import streamlit as st
import google.generativeai as genai
import PIL.Image
import json

# --- 1. KONFIGURASI API ---
# Gunakan API Key kamu yang sudah aktif
genai.configure(api_key="AQ.Ab8RN6IYDgBpTCJX-yGz6JhN_IlyY0lpuSGfdy-6bkOnhxhmNw")
model = genai.GenerativeModel(model_name="models/gemini-2.5-flash")

st.set_page_config(page_title="Sketsa Rekap - Merayu Coffee", layout="wide")

# --- 2. DATABASE HARGA & REKOMENDASI OUT ---
if 'menu_harga' not in st.session_state:
    st.session_state.menu_harga = {
        "VANILLA OREO": 15, "CHOCOLATE PREMIUM": 15, "GREENTEA WHIPPY": 15,
        "STRAWBERRY PUNCH": 16, "LEMON PUNCH": 16, "BLUEBERRY PUNCH": 16, "LECY PUNCH": 18,
        "KOPI SUSU MERAYU": 17, "KOPI SUSU AREN": 17, "CARAMELO": 18, "CREAMY": 18, "AMERICANO": 12,
        "TUBRUK": 7, "TUBRUK SUSU": 8, "LEMONADE": 12, "TEH TARIK": 12, "VIETNAM DRIP": 14,
        "MIE KUAH BON CABE": 17, "NASI KULIT": 17, "NASI AYAM GEPREK": 17, "TAICHAN NASI": 20,
        "RICEBOWL BLACKPEPPER": 20, "OTAK OTAK": 14, "CIRENG CRISPY": 14, "TAHU BAKSO": 14,
        "KENTANG GORENG": 14, "BASRENG CHILI OIL": 14, "MIX PLATTER": 18, "DIMSUM": 18
    }

# Daftar rekomendasi barang yang sering dibeli (Out)
REKOMENDASI_OUT = {
    "Es Batu": 10000,
    "Susu UHT": 17000,
    "Susu SKM": 14000,
    "Tapioka": 7000,
    "Chocolatos": 5000,
    "Gula Aren": 20000,
    "Gas LPG": 22000
}

if 'daftar_out' not in st.session_state:
    st.session_state.daftar_out = []

# --- 3. NAVIGASI HALAMAN ---
st.sidebar.title("🧭 Navigasi")
halaman = st.sidebar.selectbox("Pilih Halaman", ["📸 Rekapan Closing", "⚙️ Pengaturan Harga"])

# ---------------------------------------------------------
# HALAMAN: PENGATURAN HARGA
# ---------------------------------------------------------
if halaman == "⚙️ Pengaturan Harga":
    st.title("⚙️ Pengaturan Harga Produk")
    st.write("Ubah harga menu Merayu Coffee (dalam ribuan).")
    
    cols = st.columns(2) # Membagi layar menjadi 2 kolom untuk daftar harga
    menu_items = list(st.session_state.menu_harga.items())
    for i, (menu, harga) in enumerate(menu_items):
        with cols[i % 2]:
            st.session_state.menu_harga[menu] = st.number_input(f"Harga {menu}", value=harga, key=f"p_{menu}")
    
    st.info("Harga otomatis diperbarui di sistem rekapan.")

# ---------------------------------------------------------
# HALAMAN: REKAPAN CLOSING
# ---------------------------------------------------------
elif halaman == "📸 Rekapan Closing":
    st.title("☕ Closing Merayu Coffee")
    
    col_input, col_rekap = st.columns(2) # Membagi layar utama menjadi 2 bagian

    with col_input:
        st.subheader("1. Penjualan (In)")
        foto_tally = st.file_uploader("Upload Foto Tally (WA/Kertas)", type=['jpg', 'png', 'jpeg'])
        qris_input = st.number_input("Total Pendapatan QRIS (Rp)", value=0, step=1000)

        st.divider()
        st.subheader("2. Belanja Pakai Kas (Out)")
        
        # Fitur Rekomendasi Out (Tombol Cepat)
        st.write("✨ Klik barang yang sering dibeli:")
        cols_rec = st.columns(3) # Membagi tombol rekomendasi menjadi 3 kolom
        for i, (item, harga) in enumerate(REKOMENDASI_OUT.items()):
            if cols_rec[i % 3].button(f"+ {item}", key=f"rec_{item}"):
                st.session_state.daftar_out.append({"Barang": item, "Harga": harga})
                st.toast(f"Ditambahkan: {item}")

        st.write("---")
        # Input Manual Out
        c1, c2 = st.columns(2) # Kolom nama barang lebih lebar dari harga
        item_out = c1.text_input("Nama Barang Lain", placeholder="Misal: Sedotan")
        harga_out = c2.number_input("Harga (Rp)", value=0, step=1000, key="manual_out")
        
        if st.button("Tambah Barang Manual ➕", use_container_width=True):
            if item_out and harga_out > 0:
                st.session_state.daftar_out.append({"Barang": item_out, "Harga": harga_out})
                st.success(f"Berhasil menambah {item_out}")
            else:
                st.error("Isi nama barang dan harga!")

        if st.session_state.daftar_out:
            st.write("**Daftar Belanja Saat Ini:**")
            for i, d in enumerate(st.session_state.daftar_out):
                st.caption(f"{i+1}. {d['Barang']}: Rp {d['Harga']:,}")
            if st.button("Kosongkan Daftar Belanja 🗑️"):
                st.session_state.daftar_out = []

    with col_rekap:
        st.subheader("3. Hasil Rekapan")
        if st.button("Generate Rekapan Otomatis 🚀", use_container_width=True):
            if foto_tally:
                with st.spinner('AI Gemini 2.5 Flash sedang menghitung...'):
                    img = PIL.Image.open(foto_tally)
                    
                    # PROMPT EKSPLISIT & TELITI
                    prompt = f"""
                    Kamu adalah Agen Kasir Digital Merayu Coffee. Ekstrak data jualan dari foto.
                    
                    INSTRUKSI KHUSUS AMBIGUITAS:
                    1. JANGAN GABUNGKAN produk mirip:
                       - 'Lemon' atau 'Lemonade' (tanpa kata Punch) -> 'LEMONADE'.
                       - 'Lemon Punch' atau 'Punch Lemon' -> 'LEMON PUNCH'.
                       - 'Kopsus' atau 'Kopsus Merayu' -> 'KOPI SUSU MERAYU'.
                       - 'Kopsus Aren' -> 'KOPI SUSU AREN'.
                    
                    INSTRUKSI TEKNIS:
                    1. PENJUMLAHAN: Jumlahkan angka tally (misal: 1+2+1 = 4).
                    2. DAFTAR MENU RESMI: {list(st.session_state.menu_harga.keys())}
                    3. OUTPUT JSON SAJA: 
                       {{"items": [{{"name": "NAMA_MENU_RESMI", "qty": TOTAL_QTY}}]}}
                    """
                    
                    try:
                        response = model.generate_content([prompt, img])
                        # Membersihkan markdown JSON jika ada
                        cleaned_json = response.text.replace('```json', '').replace('```', '').strip()
                        data = json.loads(cleaned_json)
                        st.session_state.hasil_closing = data['items']
                        st.session_state.qris_final = qris_input
                    except Exception as e:
                        st.error(f"Gagal memproses gambar: {e}")
            else:
                st.warning("Silakan upload foto tally terlebih dahulu.")

        if 'hasil_closing' in st.session_state:
            st.markdown("---")
            total_in = 0
            total_qty_sold = 0
            
            st.write("### 🛒 Rincian Barang Terjual")
            for item in st.session_state.hasil_closing:
                nama = item['name']
                qty = item['qty']
                harga = st.session_state.menu_harga.get(nama, 0) * 1000
                total_in += (qty * harga)
                total_qty_sold += qty
                st.write(f"✅ **{nama}**: {qty} pcs (Rp {qty*harga:,})")
            
            st.divider()
            
            total_out = sum(d['Harga'] for d in st.session_state.daftar_out)
            tunai_bersih = (total_in - st.session_state.qris_final) - total_out
            
            # RINGKASAN AKHIR DALAM METRIC
            m1, m2 = st.columns(2)
            m1.metric("Total Barang", f"{total_qty_sold} pcs")
            m2.metric("Total Omset (Gross)", f"Rp {total_in:,}")
            
            m3, m4 = st.columns(2)
            m3.metric("Total Out (Belanja)", f"Rp {total_out:,}")
            m4.metric("Potongan QRIS", f"Rp {st.session_state.qris_final:,}")
            
            st.success(f"### 💰 SETORAN TUNAI: Rp {tunai_bersih:,}")
            st.write("*(Pastikan uang fisik di laci sesuai dengan angka di atas)*")
