from dotenv import load_dotenv
import streamlit as st
import os
import io
import google.generativeai as genai
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from PIL import Image


# Load environment variables
load_dotenv()

# API keys
GEMINI_API_KEY = st.secrets["GOOGLE_API_KEY"]
REPLICATE_API_KEY = st.secrets["REPLICATE_IMAGE_GEN_API"]

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")
chat = model.start_chat(history=[])

# Load CSS
def load_css(file_name):
    try:
        with open(file_name) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        st.warning(f"CSS file '{file_name}' not found.")

# Load HTML
def load_html(file_name):
    try:
        with open(file_name, encoding='utf-8') as f:
            st.markdown(f.read(), unsafe_allow_html=True)
    except FileNotFoundError:
        st.warning(f"HTML file '{file_name}' not found.")

# Display chat message
def display_chat_message(role, message, is_user=False):
    css_class = "user-message" if is_user else "bot-message"
    st.markdown(f"<div class='chat-message {css_class} fade-in'><b>{role}:</b> {message}</div>", unsafe_allow_html=True)


# Gemini response with file handling
def get_gemini_response(prompt=None, files=None):
    contents = []
    if prompt:
        contents.append(prompt)
    if files:
        for uploaded_file in files:
            file_type = uploaded_file.type
            file_bytes = uploaded_file.read()
            if "image" in file_type:
                image = Image.open(io.BytesIO(file_bytes))
                contents.append(image)
            elif file_type == "application/pdf":
                contents.append({"mime_type": "application/pdf", "data": file_bytes})
            elif "docx" in file_type:
                from docx import Document
                doc = Document(io.BytesIO(file_bytes))
                contents.append("\n".join([para.text for para in doc.paragraphs]))
            else:
                contents.append(file_bytes.decode('latin-1', errors='ignore'))

    if not contents:
        return ""

    response = chat.send_message(contents, stream=True)
    return "".join([chunk.text for chunk in response])

# Session state
for key in ["chat_history", "show_history", "last_response", "generated_image"]:
    if key not in st.session_state:
        st.session_state[key] = [] if "history" in key else False if "show" in key else ""

def toggle_history(): st.session_state['show_history'] = not st.session_state['show_history']
def clear_response(): st.session_state['last_response'] = ""
def clear_chat_history():
    st.session_state['chat_history'] = []
    st.session_state['show_history'] = False
    st.rerun()

# Page setup
st.set_page_config(page_title="Chatbot", page_icon=":robot:", layout="wide", initial_sidebar_state="collapsed")
load_css("style.css")
load_html("layout.html")

with st.container():
    col1, col2 = st.columns([6, 2])

    with col2:
        st.markdown("### 📊 Chat Controls")
        if st.button("📜 Chat History"):
            toggle_history()

        download_format = st.selectbox("📁 Download Chat History", ["Select format", "Download as PDF", "Download as TXT"])
        chat_text = "\n".join([f"{role}: {text}" for role, text in st.session_state['chat_history']])

        if download_format == "Download as PDF":
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
            styles = getSampleStyleSheet()
            html_style = ParagraphStyle(name="HTMLStyle", parent=styles["Normal"], fontName="Helvetica", fontSize=11, leading=14, alignment=TA_LEFT)

            def markdown_to_html_bold(text):
                import re
                return re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)

            story = []
            for line in markdown_to_html_bold(chat_text).split('\n'):
                if line.strip():
                    if "You:" in line:
                        line = f'<font color="green">{line}</font>'
                    elif "🤖:" in line:
                        line = f'<font color="black">{line}</font>'
                        story.append(HRFlowable(width="100%", thickness=0.7, color="grey"))
                    story.append(Paragraph(line, html_style))
                else:
                    story.append(Spacer(1, 12))
            doc.build(story)
            buffer.seek(0)
            st.download_button("📄 Download PDF", buffer, file_name="chat_history.pdf", mime="application/pdf")

        elif download_format == "Download as TXT":
            buffer = io.BytesIO(chat_text.encode("utf-8"))
            st.download_button("📄 Download TXT", buffer, file_name="chat_history.txt", mime="text/plain")

        st.markdown("##### File Upload")
        uploaded_files = st.file_uploader("Upload files:", type=["png", "jpg", "jpeg", "pdf", "docx"], accept_multiple_files=True)

    with col1:
        user_input = st.chat_input("Type your message here...")
        if user_input:
            with st.spinner("🤔 Thinking..."):
                response = get_gemini_response(prompt=user_input, files=uploaded_files)
                st.session_state['last_response'] = response

            msg = user_input + (f" (Uploaded: {', '.join([f.name for f in uploaded_files])})" if uploaded_files else "")
            st.session_state['chat_history'].append(("You", msg))
            st.session_state['chat_history'].append(("🤖", response))

            display_chat_message("You", msg, is_user=True)
            display_chat_message("🤖", response)

        if st.session_state['show_history'] and st.session_state['chat_history']:
            st.markdown("---")
            st.markdown("### 📜 Chat History")
            for i in range(0, len(st.session_state['chat_history']), 2):
                u, b = st.session_state['chat_history'][i], st.session_state['chat_history'][i+1]
                display_chat_message(u[0], u[1], is_user=True)
                display_chat_message("🤖", b[1], is_user=False)
            st.markdown("---")


# Sidebar
with st.sidebar:
    st.markdown("### 🛠️ Chat Controls")
    if st.button("🗑️ Clear Last Response"): clear_response()
    if st.button("🗑️ Clear Chat History"): clear_chat_history()
    st.markdown("---")
    st.markdown("### ℹ️ Tips")
    st.markdown("""
    - Upload PDFs, DOCX, or images    
    - Download your chat  
    - All data is ephemeral (temporary)
    """)
