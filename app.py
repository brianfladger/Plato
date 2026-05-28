
import streamlit as st
import pandas as pd
from pdf2image import convert_from_bytes
import pytesseract
import re

st.set_page_config(page_title="Steam Log Extractor", layout="wide")

st.title("🔥 Steam Log Extractor (Cloud Tool)")

uploaded_files = st.file_uploader(
    "Drag and drop ALL your PDFs here",
    type=["pdf"],
    accept_multiple_files=True
)

def extract_data(text, filename):
    rows = []

    date_match = re.search(r'(\d{1,2}/\d{1,2}/\d{2,4})', text)
    date = date_match.group(1) if date_match else filename

    text = text.replace(",", ".")

    matches = re.findall(r'(\d{3,4})\s+([\d\.]+)', text)

    for m in matches:
        try:
            rows.append({
                "Date": date,
                "Time": m[0],
                "Steam_Produced_klbs": float(m[1]),
                "Source_File": filename
            })
        except:
            continue

    return rows


if uploaded_files:
    if st.button("Process Files"):

        all_data = []
        progress = st.progress(0)

        for i, file in enumerate(uploaded_files):
            try:
                images = convert_from_bytes(file.read())

                text = ""
                for img in images:
                    text += pytesseract.image_to_string(img)

                rows = extract_data(text, file.name)
                all_data.extend(rows)

            except Exception as e:
                st.error(f"Error processing {file.name}: {e}")

            progress.progress((i + 1) / len(uploaded_files))

        df = pd.DataFrame(all_data)

        if not df.empty:
            df["Time"] = pd.to_numeric(df["Time"], errors="coerce")
            df = df.sort_values(["Date", "Time"])

            st.success(f"{len(df)} rows extracted")

            st.dataframe(df)

            csv = df.to_csv(index=False).encode("utf-8")

            st.download_button(
                "Download Full CSV",
                csv,
                "steam_logs_full.csv",
                "text/csv"
            )
