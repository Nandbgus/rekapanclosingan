import streamlit as st
import google.generativeai as genai
import PIL.Image
import json

# --- CONFIGURASI API GEMINI ---
# Masukkan API Key kamu di sini
genai.configure(api_key="AQ.Ab8RN6KPoCBTKexvBIp5yNlotHEd4zhJhOsurfD_fu9NgXCiGA")
model = genai.GenerativeModel('gemini-1.5-flash')

st.set_page_config(page_title="Sketsa Rekap - Merayu Coffee", layout="centered")

# --- DATABASE HARGA (Session State agar tidak hilang saat pindah halaman) ---
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

# --- NAVIGASI HALAMAN ---
st.sidebar.title("🧭 Navigasi")
halaman = st.sidebar.radio("Pilih Halaman:", ["📸 Rekapan Closing", "⚙️ Pengaturan Harga"])

# ---------------------------------------------------------
# HALAMAN 1: REKAPAN CLOSING
# ---------------------------------------------------------
if halaman == "📸 Rekapan Closing":
    st.title("☕ Sketsa Rekap Kasir")
    st.write("Proses rekapan otomatis Merayu Coffee menggunakan AI.")

    tab1, tab2 = st.tabs(["Upload Data", "Hasil Laporan"])

    with tab1:
        st.subheader("1. Penjualan (In)")
        foto_tally = st.file_uploader("Upload Foto Tally (WA/Catatan)", type=['jpg', 'png', 'jpeg'])
        qris_input = st.number_input("Total QRIS (Rp)", value=0, step=1000)
        
        st.divider()
        st.subheader("2. Belanja (Out)")
        out_label = st.text_input("Barang yang dibeli", placeholder="Contoh: Es Batu, Susu")
        out_amount = st.number_input("Nominal Belanja (Rp)", value=0, step=1000)

        if st.button("Proses Rekapan ✨", use_container_width=True):
            if foto_tally:
                with st.spinner('Agen AI sedang menghitung...'):
                    img = PIL.Image.open(foto_tally)
                    prompt = f"""
                    Analisa teks penjualan dari gambar. Jumlahkan format angka (misal 1+2+1 = 4).
                    Cocokkan nama produk dengan daftar ini: {list(st.session_state.menu_harga.keys())}.
                    Berikan output HANYA dalam format JSON: 
                    {{"items": [{{"name": "NAMA_PRODUK", "qty": TOTAL_QTY}}]}}
                    """
                    response = model.generate_content([prompt, img])
                    try:
                        data_json = response.text.replace('```json', '').replace('```', '').strip()
                        hasil = json.loads(data_json)
                        st.session_state.hasil_closing = hasil['items']
                        st.session_state.qris = qris_input
                        st.session_state.out_total = out_amount
                        st.success("Berhasil! Silakan buka tab 'Hasil Laporan'.")
                    except:
                        st.error("Gagal membaca foto. Coba foto lebih dekat/jelas.")
            else:
                st.warning("Upload foto tally dulu ya!")

    with tab2:
        if 'hasil_closing' in st.session_state:
            st.header("📋 Laporan Closing")
            total_omset = 0
            rekap_data = []
            
            for sale in st.session_state.hasil_closing:
                nama = sale['name']
                qty = sale['qty']
                harga = st.session_state.menu_harga.get(nama, 0) * 1000
                subtotal = qty * harga
                total_omset += subtotal
                rekap_data.append({"Produk": nama, "Qty": qty, "Subtotal": f"Rp {subtotal:,}"})
            
            st.table(rekap_data)
            
            tunai_kotor = total_omset - st.session_state.qris
            setoran_akhir = tunai_kotor - st.session_state.out_total
            
            st.metric("Total Omset (Gross)", f"Rp {total_omset:,}")
            st.metric("Potongan QRIS", f"Rp {st.session_state.qris:,}")
            st.metric("Potongan Belanja (Out)", f"Rp {st.session_state.out_total:,}")
            st.success(f"**TOTAL SETORAN TUNAI: Rp {setoran_akhir:,}**")
        else:
            st.info("Data belum diproses. Silakan upload foto di tab sebelah.")

# ---------------------------------------------------------
# HALAMAN 2: PENGATURAN HARGA
# ---------------------------------------------------------
elif halaman == "⚙️ Pengaturan Harga":
    st.title("⚙️ Manajemen Harga Produk")
    st.write("Ubah harga menu Merayu Coffee di sini. Perubahan akan langsung tersimpan di sistem rekapan.")

    # Tampilkan dalam grid agar lebih rapi (2 kolom)
    cols = st.columns(2)
    menu_items = list(st.session_state.menu_harga.items())
    
    for i, (menu, harga) in enumerate(menu_items):
        with cols[i % 2]:
            new_price = st.number_input(f"Harga {menu} (k)", value=harga, step=1, key=f"price_{menu}")
            st.session_state.menu_harga[menu] = new_price

    if st.button("Simpan Perubahan", use_container_width=True):
        st.toast("Harga berhasil diperbarui!", icon="✅")
