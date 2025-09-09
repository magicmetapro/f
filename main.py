import streamlit as st
import PyPDF2
import io
import google.generativeai as genai
import pandas as pd
import re

# Konfigurasi Gemini AI
genai.configure(api_key="AIzaSyBzKrjj-UwAVm-0MEjfSx3ShnJ4fDrsACU")

def extract_text_from_pdf(uploaded_file):
    """Mengekstrak teks dari file PDF"""
    pdf_reader = PyPDF2.PdfReader(uploaded_file)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text() + "\n"
    return text

def parse_product_data(text):
    """Memproses teks dan mengekstrak data produk ke dalam dataframe"""
    lines = text.split('\n')
    products = []
    current_product = {}
    
    for line in lines:
        # Cari baris yang berisi data produk (dengan format nomor, kode, dll)
        if re.match(r'^\d+\s+\d{6}\s+', line):
            parts = re.split(r'\s{2,}', line.strip())
            if len(parts) >= 5:
                products.append({
                    'NO': parts[0],
                    'PGODE': parts[1],
                    'NAMA_BARANG': parts[2],
                    'SATUAN_ISI': parts[3],
                    'JML_BARANG': parts[4],
                    'NILAI_RP': parts[5] if len(parts) > 5 else ''
                })
    
    return pd.DataFrame(products)

def compare_product_data(df1, df2):
    """Membandingkan dua dataframe produk dan mengidentifikasi perbedaan"""
    # Gabungkan data berdasarkan PGODE
    merged = pd.merge(df1, df2, on='PGODE', how='outer', suffixes=('_1', '_2'))
    
    # Identifikasi perbedaan
    differences = []
    
    for _, row in merged.iterrows():
        pgode = row['PGODE']
        
        # Cek jika produk ada di kedua file
        in_both = not pd.isna(row['JML_BARANG_1']) and not pd.isna(row['JML_BARANG_2'])
        
        if not in_both:
            # Produk hanya ada di satu file
            if pd.isna(row['JML_BARANG_1']):
                differences.append(f"Produk dengan PGODE {pgode} hanya ada di PDF 2: {row['NAMA_BARANG_2']}")
            else:
                differences.append(f"Produk dengan PGODE {pgode} hanya ada di PDF 1: {row['NAMA_BARANG_1']}")
        else:
            # Produk ada di kedua file, bandingkan jumlah
            if row['JML_BARANG_1'] != row['JML_BARANG_2']:
                # Parse format jumlah
                qty1 = parse_quantity(row['JML_BARANG_1'])
                qty2 = parse_quantity(row['JML_BARANG_2'])
                
                differences.append(
                    f"Perbedaan jumlah untuk PGODE {pgode} ({row['NAMA_BARANG_1']}): " +
                    f"PDF 1 = {row['JML_BARANG_1']} ({qty1['karton']} karton, {qty1['pack']} pack, {qty1['pcs']} pcs), " +
                    f"PDF 2 = {row['JML_BARANG_2']} ({qty2['karton']} karton, {qty2['pack']} pack, {qty2['pcs']} pcs)"
                )
    
    return differences

def parse_quantity(qty_str):
    """Mengurai format jumlah barang menjadi karton, pack, dan pcs"""
    if not qty_str or pd.isna(qty_str):
        return {'karton': 0, 'pack': 0, 'pcs': 0}
    
    # Normalisasi format
    if '.' not in qty_str:
        # Format seperti "1" berarti 1 karton
        try:
            karton = int(qty_str)
            return {'karton': karton, 'pack': 0, 'pcs': 0}
        except:
            return {'karton': 0, 'pack': 0, 'pcs': 0}
    
    # Format dengan titik pemisah
    parts = qty_str.split('.')
    if len(parts) == 3:
        try:
            return {
                'karton': int(parts[0]),
                'pack': int(parts[1]),
                'pcs': int(parts[2])
            }
        except:
            return {'karton': 0, 'pack': 0, 'pcs': 0}
    else:
        return {'karton': 0, 'pack': 0, 'pcs': 0}

def main():
    st.title("Aplikasi Perbandingan Data Produk dari PDF")
    st.write("Unggah dua file PDF untuk membandingkan data produk (Fokus: PGODE dan Jumlah Barang)")
    
    # Upload file PDF
    col1, col2 = st.columns(2)
    with col1:
        pdf_file1 = st.file_uploader("Unggah PDF pertama", type="pdf", key="pdf1")
    with col2:
        pdf_file2 = st.file_uploader("Unggah PDF kedua", type="pdf", key="pdf2")
    
    if st.button("Bandingkan PDF") and pdf_file1 and pdf_file2:
        with st.spinner("Memproses PDF dan menganalisis perbedaan..."):
            # Ekstrak teks dari kedua PDF
            text1 = extract_text_from_pdf(pdf_file1)
            text2 = extract_text_from_pdf(pdf_file2)
            
            # Parse data produk
            df1 = parse_product_data(text1)
            df2 = parse_product_data(text2)
            
            # Bandingkan data
            differences = compare_product_data(df1, df2)
            
            # Tampilkan hasil
            st.subheader("Hasil Perbandingan")
            
            if not differences:
                st.success("✅ Kedua file PDF memiliki data yang sama untuk semua PGODE dan jumlah barang.")
            else:
                st.warning(f"❌ Ditemukan {len(differences)} perbedaan:")
                for diff in differences:
                    st.write(f"- {diff}")
            
            # Tampilkan data dalam bentuk tabel untuk referensi
            with st.expander("Lihat Data PDF 1"):
                st.dataframe(df1[['PGODE', 'NAMA_BARANG', 'JML_BARANG']])
            
            with st.expander("Lihat Data PDF 2"):
                st.dataframe(df2[['PGODE', 'NAMA_BARANG', 'JML_BARANG']])
            
            # Gunakan Gemini untuk analisis tambahan jika diperlukan
            if differences:
                st.subheader("Analisis Tambahan oleh AI")
                model = genai.GenerativeModel("gemini-1.5-flash")
                
                prompt = f"""
                Saya telah membandingkan dua dokumen PDF dan menemukan perbedaan berikut:
                
                {chr(10).join(differences)}
                
                Format JML BARANG menggunakan titik sebagai pemisah dengan interpretasi:
                - Digit pertama: Jumlah karton
                - Digit kedua (tengah): Jumlah pack
                - Digit ketiga: Jumlah pcs
                
                Berikan analisis singkat tentang perbedaan-perbedaan ini, fokus pada:
                1. Jenis perbedaan utama (produk hilang/tambahan atau perubahan jumlah)
                2. Implikasi dari perbedaan jumlah barang
                3. Rekomendasi untuk menyelaraskan data
                
                Jawab dalam bahasa Indonesia dengan jelas dan singkat.
                """
                
                try:
                    response = model.generate_content(prompt)
                    st.write(response.text)
                except Exception as e:
                    st.error(f"Error dalam menghasilkan analisis AI: {e}")

if __name__ == "__main__":
    main()
