import streamlit as st
import subprocess
import tempfile
import os

def run_pdfsteg_command(action, input_pdf, output_pdf=None, message_file=None):
    try:
        if action == "stat":
            result = subprocess.run(
                ["python", "full_pdf_steg.py", "stat", input_pdf],
                capture_output=True, text=True, check=True)
            return result.stdout
        elif action == "embed":
            result = subprocess.run(
                ["python", "full_pdf_steg.py", "embed", input_pdf, output_pdf, message_file],
                capture_output=True, text=True, check=True)
            return result.stdout
        elif action == "extract":
            result = subprocess.run(
                ["python", "full_pdf_steg.py", "extract", input_pdf, output_pdf],
                capture_output=True, text=True, check=True)
            return result.stdout
    except subprocess.CalledProcessError as e:
        return e.stderr

st.set_page_config(page_title="PDF Steganography Demo", page_icon="🔒", layout="wide")
st.title("🔒 PDF Steganography Demo")
st.markdown("Easily hide and extract secret messages in PDF files. Powered by PDFSteg.")

mode = st.sidebar.radio("What do you want to do?", (
    "Hide Message", "Extract Message", "Check Capacity"
))

if mode == "Hide Message":
    st.subheader("Hide a Secret Message in Your PDF")
    pdf_file = st.file_uploader("Upload your PDF file", type=["pdf"])
    message = st.text_area("Enter your secret message", height=120)
    if st.button("Hide Message"):
        if pdf_file is not None and message.strip() != "":
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_pdf:
                tmp_pdf.write(pdf_file.read())
                cover_path = tmp_pdf.name
            raw_path = cover_path.replace(".pdf", "_raw.pdf")
            subprocess.run([
                "qpdf", cover_path, "--stream-data=uncompress", raw_path
            ], check=True)
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix=".txt") as tmp_msg:
                tmp_msg.write(message)
                message_path = tmp_msg.name
            stego_path = raw_path.replace("_raw.pdf", "_stego.pdf")
            result = run_pdfsteg_command("embed", raw_path, stego_path, message_path)
            if "successfully embedded" in result:
                st.success("Message hidden successfully!")
                with open(stego_path, "rb") as f:
                    st.download_button("Download Stego PDF", f, "stego.pdf", "application/pdf")
            else:
                st.error(result)
            os.unlink(cover_path)
            os.unlink(raw_path)
            os.unlink(message_path)
            if os.path.exists(stego_path):
                os.unlink(stego_path)

elif mode == "Extract Message":
    st.subheader("Extract a Secret Message from a PDF")
    stego_pdf = st.file_uploader("Upload your stego PDF file", type=["pdf"])
    if st.button("Extract Message"):
        if stego_pdf is not None:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_pdf:
                tmp_pdf.write(stego_pdf.read())
                stego_path = tmp_pdf.name
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix=".txt") as out_msg:
                out_path = out_msg.name
            result = run_pdfsteg_command("extract", stego_path, out_path)
            if os.path.exists(out_path):
                with open(out_path, 'r') as f:
                    content = f.read()
                st.success("Message extracted!")
                st.text_area("Extracted Secret Message:", content, height=200)
            else:
                st.error(result)
            os.unlink(stego_path)
            if os.path.exists(out_path):
                os.unlink(out_path)

elif mode == "Check Capacity":
    st.subheader("Check Hiding Capacity of a PDF")
    in_pdf = st.file_uploader("Upload PDF", type=["pdf"])
    if st.button("Check Capacity"):
        if in_pdf is not None:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_pdf:
                tmp_pdf.write(in_pdf.read())
                cover_path = tmp_pdf.name
            raw_path = cover_path.replace(".pdf", "_raw.pdf")
            subprocess.run([
                "qpdf", cover_path, "--stream-data=uncompress", raw_path
            ], check=True)
            result = run_pdfsteg_command("stat", raw_path)
            st.info(result)
            os.unlink(cover_path)
            os.unlink(raw_path)
