
import streamlit as st
import pandas as pd
from pdf2image import convert_from_bytes
import pytesseract
import re

# --- App Setup ---
st.set_page_config(page_title="Steam Log Extractor", layout="wide")
st.title("🔥 Steam Plant Log Extractor")

uploaded_files = st.file_uploader(
    "📂 Drag and drop ALL your PDFs here",
    type=["pdf"],
    accept_multiple_files=True
)

# --- Improved Extraction Logic ---
def extract_data(text, filename):
    rows = []

    # ✅ Extract date (fallback = filename)
    date_match = re.search(r'(\d{1,2}/\d{1,2}/\d{2,4})', text)
    date = date_match.group(1) if date_match else filename

    # ✅ Clean OCR text
    text = text.replace(",", ".")

    lines = text.split("\n")

    for line in lines:
        line = line.strip()

        # ✅ Strict time match (0000–2359)
        time_match = re.match(r'^(0?\d{3}|1\d{3}|2[0-3]\d{2})\b', line)
        if not time_match:
            continue

        time = time_match.group(0)

        # ✅ Extract numeric values from the line
        numbers = re.findall(r'[\d.]+', line)

        if len(numbers) < 2:
            continue

        try:
            steam = float(numbers[1])
        except:
            continue

        # ✅ Filter unrealistic steam values
        if steam <= 0 or steam > 50:
            continue

        rows.append({
            "Date": date,
            "Time": time,
            "Steam_Produced_klbs": steam,
            "Source_File": filename
        })

    return rows


# --- Main Processing ---
if uploaded_files:

    if st.button("🚀 Process All Files"):

        all_rows = []
        progress = st.progress(0)
        status = st.empty()

        for i, file in enumerate(uploaded_files):

            status.text(f"Processing: {file.name}")

            try:
                images = convert_from_bytes(file.read())

                full_text = ""

                # ✅ OCR each page
                for img in images:
                    full_text += pytesseract.image_to_string(img)

                # ✅ Extract structured rows
                rows = extract_data(full_text, file.name)
                all_rows.extend(rows)

            except Exception as e:
                st.warning(f"⚠️ Error with {file.name}: {e}")

            progress.progress((i + 1) / len(uploaded_files))

        # --- Build DataFrame ---
        df = pd.DataFrame(all_rows)

        if df.empty:
            st.error("❌ No valid data extracted.")
        else:
            # ✅ Clean + sort
            df["Time"] = pd.to_numeric(df["Time"], errors="coerce")
            df["Steam_Produced_klbs"] = pd.to_numeric(df["Steam_Produced_klbs"], errors="coerce")

            df = df.dropna()
            df = df.sort_values(["Date", "Time"])

            st.success(f"✅ Extraction complete — {len(df)} rows")

            # --- Preview ---
            st.subheader("Preview")
            st.dataframe(df.head(50), use_container_width=True)

            # --- Full CSV Download ---
            csv = df.to_csv(index=False).encode("utf-8")

            st.download_button(
                "⬇️ Download FULL CSV",
                csv,
                "steam_logs_full.csv",
                "text/csv"
            )

            # --- Daily Summary ---
            summary = (
                df.groupby("Date")["Steam_Produced_klbs"]
                .sum()
                .reset_index()
                .rename(columns={"Steam_Produced_klbs": "Daily_Total_klbs"})
            )

            st.subheader("Daily Totals")
            st.dataframe(summary, use_container_width=True)

            summary_csv = summary.to_csv(index=False).encode("utf-8")

            st.download_button(
                "⬇️ Download Daily Summary",
                summary_csv,
                "steam_logs_summary.csv",
                "text/csv"
            )
