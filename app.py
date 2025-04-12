import os
import pandas as pd
import PyPDF2
import requests
import streamlit as st

# Streamlit setup
st.set_page_config(page_title="PDF Keyword Finder", layout="centered")
st.title("🔍 PDF Keyword Finder")

# Upload Excel file
excel_file = st.file_uploader("📂 Upload your Excel file", type=["xlsx"])

if excel_file is not None:
    try:
        pdf_df = pd.read_excel(excel_file, sheet_name="PDFs")
        keywords_df = pd.read_excel(excel_file, sheet_name="Keywords")
    except Exception as e:
        st.error(f"❌ Error reading Excel: {e}")
    else:
        keywords = keywords_df['Keyword'].dropna().str.lower().tolist()
        results = []

        os.makedirs("pdfs", exist_ok=True)

        with st.spinner("🔄 Processing PDFs..."):
            for idx, row in pdf_df.iterrows():
                url = str(row['Filename']).strip()
                pdf_name = f"pdfs/pdf_{idx}.pdf"

                try:
                    response = requests.get(url)
                    if response.status_code == 200:
                        with open(pdf_name, 'wb') as f:
                            f.write(response.content)
                        st.success(f"✅ Downloaded: {url}")
                    else:
                        st.warning(f"⚠️ Failed to download: {url}")
                        continue
                except Exception as e:
                    st.error(f"❌ Download error: {url} | {e}")
                    continue

                try:
                    with open(pdf_name, 'rb') as file:
                        reader = PyPDF2.PdfReader(file)
                        text = ''
                        for page in reader.pages:
                            if page.extract_text():
                                text += page.extract_text() + '\n'

                    lines = text.split('\n')

                    for line in lines:
                        line_lower = line.lower()
                        for keyword in keywords:
                            if keyword in line_lower:
                                # Remove keyword from the line (case-insensitive)
                                start = line_lower.find(keyword)
                                cleaned_line = (
                                    line[:start] + 
                                    line[start + len(keyword):]
                                ).strip()

                                results.append({
                                    'PDF Source': url,
                                    'Keyword': keyword,
                                    'Matched Line': line.strip(),
                                    'Line Without Keyword': cleaned_line
                                })
                                break
                except Exception as e:
                    st.error(f"❌ PDF read error: {e}")

        # Show and download results
        if results:
            output_df = pd.DataFrame(results)
            st.dataframe(output_df)

            output_file = "output_results.xlsx"
            output_df.to_excel(output_file, index=False)

            with open(output_file, "rb") as f:
                st.download_button("⬇️ Download Results", data=f, file_name="output_results.xlsx")
        else:
            st.info("ℹ️ No keyword matches found.")
