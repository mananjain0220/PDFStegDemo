import streamlit as st
import subprocess
import tempfile
import os
import time
import sys

# ----- Custom Theming -----
st.set_page_config(
    page_title="PDF Steganography Suite",
    page_icon="🔒",
    layout="wide",
    initial_sidebar_state="expanded"
)

custom_css = """
<style>
.main-header {
    background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
    color: #fff;
    padding: 2rem 1rem 1rem 1rem;
    border-radius: 16px;
    text-align: center;
    margin-bottom: 1.5rem;
}
.upload-area {
    border: 2px dashed #764ba2;
    border-radius: 12px;
    padding: 1.5rem;
    background: #faf8ff;
    text-align: center;
    margin-bottom: 1rem;
    transition: border-color 0.3s;
}
.upload-area:hover {
    border-color: #667eea;
    background: #f3f0fa;
}
.metric-card {
    background: #fff;
    border-left: 5px solid #764ba2;
    padding: 1rem;
    border-radius: 10px;
    margin-bottom: 1rem;
    box-shadow: 0 1px 3px rgba(35,26,60,0.07), 0 0.5px 1.5px rgba(35,26,60,0.03);
}
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)
st.markdown('<div class="main-header"><h2>🔒 PDF Steganography Suite</h2><p>Easily hide and extract secret messages from PDFs.</p></div>', unsafe_allow_html=True)

# ---- Helper Functions ----
def run_pdfsteg_command(action, input_pdf, output_pdf=None, message_file=None):
    try:
        if action == "stat":
            result = subprocess.run(
                [sys.executable, "full_pdf_steg.py", "stat", input_pdf],
                capture_output=True, text=True, check=True)
            return result.stdout
        elif action == "embed":
            result = subprocess.run(
                [sys.executable, "full_pdf_steg.py", "embed", input_pdf, output_pdf, message_file],
                capture_output=True, text=True, check=True)
            return result.stdout
        elif action == "extract":
            result = subprocess.run(
                [sys.executable, "full_pdf_steg.py", "extract", input_pdf, output_pdf],
                capture_output=True, text=True, check=True)
            return result.stdout
    except subprocess.CalledProcessError as e:
        return e.stderr

# ----- Tabs for User Navigation -----
tabs = st.tabs(["🔒 Hide Message", "🔍 Extract Message", "📊 Check Capacity", "ℹ️ Help"])

# ---- Hide Message Tab ----
with tabs[0]:
    st.markdown("#### Hide a Secret Message in a PDF")
    uploaded_pdf = st.file_uploader("Upload PDF to hide a message", type="pdf", key="hide_pdf")
    secret_message = st.text_area("Enter your secret message below (max 1000 characters):", max_chars=1000, height=120)
    col_embed, col_reset = st.columns([2,1])
    with col_embed:
        embed_btn = st.button("🔒 Hide Message", type="primary")
    with col_reset:
        reset_btn = st.button("Clear", key="clear_embed")

    if embed_btn and uploaded_pdf and secret_message.strip() != "":
        with st.spinner("Processing and hiding your message…"):
            # Save the PDF to temp file
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_pdf:
                tmp_pdf.write(uploaded_pdf.read())
                cover_path = tmp_pdf.name
            raw_path = cover_path.replace(".pdf", "_raw.pdf")
            qpdf_process = subprocess.run(
                ["qpdf", cover_path, "--stream-data=uncompress", raw_path],
                capture_output=True, text=True)
            if qpdf_process.returncode != 0:
                st.error("PDF decompression failed. Please try another PDF.")
            else:
                with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix=".txt") as tmp_msg:
                    tmp_msg.write(secret_message)
                    message_path = tmp_msg.name
                stego_path = raw_path.replace("_raw.pdf", "_stego.pdf")
                result = run_pdfsteg_command("embed", raw_path, stego_path, message_path)
                time.sleep(1)  # Small UX delay
                if "successfully embedded" in result.lower():
                    st.markdown('<div class="metric-card">✅ <b>Message hidden successfully!</b></div>', unsafe_allow_html=True)
                    with open(stego_path, "rb") as f:
                        st.download_button("📥 Download Stego PDF", f, "stego.pdf", "application/pdf")
                else:
                    st.error(result)
            # Cleanup
            for path in [cover_path, raw_path, message_path, stego_path]:
                try:
                    if os.path.exists(path):
                        os.unlink(path)
                except Exception:
                    pass

# ---- Extract Message Tab ----
with tabs[1]:
    st.markdown("#### Extract a Hidden Message from a PDF")
    stego_pdf = st.file_uploader("Upload your stego PDF", type="pdf", key="extract_pdf")
    extract_btn = st.button("🔍 Extract Message", key="extract_btn")
    if extract_btn and stego_pdf:
        with st.spinner("Extracting hidden message…"):
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_pdf:
                tmp_pdf.write(stego_pdf.read())
                stego_path = tmp_pdf.name
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix=".txt") as tmp_out:
                out_path = tmp_out.name
            result = run_pdfsteg_command("extract", stego_path, out_path)
            time.sleep(1)
            if os.path.exists(out_path):
                with open(out_path) as f:
                    content = f.read()
                if content.strip():
                    st.success("✅ Message extracted:")
                    st.text_area("Extracted Secret Message:", content, height=180)
                else:
                    st.warning("No message was found in the PDF.")
            else:
                st.error(result)
            # Cleanup
            for path in [stego_path, out_path]:
                try:
                    if os.path.exists(path):
                        os.unlink(path)
                except Exception:
                    pass

# ---- Check Capacity Tab ----
with tabs[2]:
    st.markdown("#### Check the Capacity of Your PDF File")
    check_pdf = st.file_uploader("Upload PDF to analyze capacity", type="pdf", key="capacity_pdf")
    check_btn = st.button("Analyze Capacity")
    if check_btn and check_pdf:
        with st.spinner("Analyzing PDF…"):
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_pdf:
                tmp_pdf.write(check_pdf.read())
                cover_path = tmp_pdf.name
            raw_path = cover_path.replace(".pdf", "_raw.pdf")
            qpdf_process = subprocess.run(
                ["qpdf", cover_path, "--stream-data=uncompress", raw_path],
                capture_output=True, text=True)
            if qpdf_process.returncode != 0:
                st.error("PDF decompression failed. Try another file.")
            else:
                result = run_pdfsteg_command("stat", raw_path)
                st.markdown('<div class="metric-card">{}</div>'.format(result.replace("\n", "<br>")), unsafe_allow_html=True)
            for path in [cover_path, raw_path]:
                try:
                    if os.path.exists(path):
                        os.unlink(path)
                except Exception:
                    pass

# ---- Help Tab ----
with tabs[3]:
    st.markdown("""
    ### 🔎 How to Use This App

    - **Hide Message:** Upload a regular PDF, type your secret, and download a visually identical PDF with your hidden message.
    - **Extract Message:** Upload a steganographic PDF made in this app to reveal the original hidden message.
    - **Capacity Check:** Find out how much secret data your PDF can hide before starting.

    ---
    **Troubleshooting Tips:**
    - Use text-heavy PDFs (reports, papers) for maximum capacity.
    - PDF files with only images or advanced encryption may work poorly.
    - For any issues, refresh the page and try again.

    ---
    **About:**  
    This tool uses high-capacity operator-based PDF steganography and is designed for the ATTRIBUT research project.
    """, unsafe_allow_html=True)
