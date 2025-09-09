import streamlit as st
import PyPDF2
import io
import google.generativeai as genai
import pandas as pd

# Konfigurasi Gemini AI
genai.configure(api_key="AIzaSyBzKrjj-UwAVm-0MEjfSx3ShnJ4fDrsACU")

def extract_text_from_pdf(uploaded_file):
    """Mengekstrak teks dari file PDF"""
    pdf_reader = PyPDF2.PdfReader(uploaded_file)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text() + "\n"
    return text

def compare_pdfs_with_gemini(text1, text2):
    """Menggunakan Gemini untuk membandingkan dua teks PDF"""
    model = genai.GenerativeModel("gemini-1.5-flash")
    
    prompt = f"""
    Saya memiliki dua dokumen PDF yang berisi data produk. Bandingkan kedua dokumen ini dan identifikasi perbedaannya.
    
    DOKUMEN 1:
    {text1}
    
    DOKUMEN 2:
    {text2}
    
    Format data dalam dokumen memiliki kolom:
    - PGODE: Kode produk
    - NAMA BARANG: Nama produk
    - SATUAN/ISI: Informasi satuan/kemasan
    - JML BARANN: Jumlah barang dengan format khusus
    - NILAI RP BELL: Nilai dalam Rupiah
    
    Format JML BARANN menggunakan titik sebagai pemisah dengan interpretasi:
    - Digit pertama: Jumlah karton
    - Digit kedua (tengah): Jumlah pack
    - Digit ketiga: Jumlah pcs
    
    Contoh: 
    1         = 1 karton, 0 pack, 0 pcs
    2.012.010 = 2 karton, 12 pack, 10 pcs
    0.009.000 = 0 karton, 9 pack, 0 pcs
    0.000.018 = 0 karton, 0 pack, 18 pcs
    
    Tolong berikan analisis perbandingan yang detail dengan fokus pada:
    1. Apakah kedua dokumen sama atau berbeda?
    2. Jika berbeda, di bagian mana saja perbedaannya?
    3. Perbandingan berdasarkan PGODE, NAMA BARANG, dan JML BARANN
    4. Berikan penjelasan yang jelas tentang perbedaan jumlah barang sesuai format yang dijelaskan
    
    Sajikan hasil dalam format yang mudah dipahami.
    """
    
    response = model.generate_content(prompt)
    return response.text

def main():
    st.title("Aplikasi Perbandingan Data Produk dari PDF")
    st.write("Unggah dua file PDF untuk membandingkan data produk")
    
    # Upload file PDF
    pdf_file1 = st.file_uploader("Unggah PDF pertama", type="pdf", key="pdf1")
    pdf_file2 = st.file_uploader("Unggah PDF kedua", type="pdf", key="pdf2")
    
    if st.button("Bandingkan PDF") and pdf_file1 and pdf_file2:
        with st.spinner("Memproses PDF dan menganalisis perbedaan..."):
            # Ekstrak teks dari kedua PDF
            text1 = extract_text_from_pdf(pdf_file1)
            text2 = extract_text_from_pdf(pdf_file2)
            
            # Gunakan Gemini untuk membandingkan
            comparison_result = compare_pdfs_with_gemini(text1, text2)
            
            # Tampilkan hasil
            st.subheader("Hasil Perbandingan")
            st.write(comparison_result)
            
            # Tampilkan teks asli untuk referensi
            with st.expander("Lihat Teks PDF 1"):
                st.text(text1)
            
            with st.expander("Lihat Teks PDF 2"):
                st.text(text2)

if __name__ == "__main__":
    main()
