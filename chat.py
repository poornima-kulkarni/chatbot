from dotenv import load_dotenv
import streamlit as st
import os
import google.generativeai as genai
import io
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from PIL import Image

# Load environment variables
load_dotenv()

# Configure Gemini model
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
model = genai.GenerativeModel("gemini-1.5-flash")
chat = model.start_chat(history=[])

# Gemini response function (handles text and files)
def get_gemini_response(prompt=None, image=None, pdf_data=None, docx_data=None):
    contents = []
    if prompt:
        contents.append(prompt)
    if image is not None:
        contents.append(image)
    if pdf_data is not None:
        contents.append({"mime_type": "application/pdf", "data": pdf_data})
    # For docx, we'll treat it as raw text for simplicity here.
    # A more robust solution might involve parsing the docx.
    if docx_data is not None:
        try:
            from docx import Document
            doc = Document(io.BytesIO(docx_data))
            full_text = []
            for para in doc.paragraphs:
                full_text.append(para.text)
            contents.append("\n".join(full_text))
        except ImportError:
            st.warning("docx library not found. Docx files will be treated as binary.")
            contents.append(docx_data.decode('latin-1', errors='ignore')) # Basic decoding
        except Exception as e:
            st.error(f"Error processing docx file: {e}")
            contents.append(docx_data.decode('latin-1', errors='ignore')) # Basic decoding

    if not contents:
        return ""
    response = chat.send_message(contents, stream=True)
    return "".join([chunk.text for chunk in response])

# Streamlit page config
st.set_page_config(page_title="Chatbot", page_icon=":robot:", layout="wide")
st.markdown("<h1 style='text-align: center;'>🤖 Chatbot</h1>", unsafe_allow_html=True)

# Session history init
if 'chat_history' not in st.session_state:
    st.session_state['chat_history'] = []
if 'show_history' not in st.session_state:
    st.session_state['show_history'] = False
if 'last_response' not in st.session_state:
    st.session_state['last_response'] = ""

def toggle_history():
    st.session_state['show_history'] = not st.session_state['show_history']

def clear_response():
    st.session_state['last_response'] = ""

# Layout
with st.container():
    col1, col2 = st.columns([6, 2])  # Wider main chat area

    with col2:
        st.button("📜 Chat History", on_click=toggle_history)
        download_format = st.selectbox("📁 Download Chat history", ["Select format", "Download as PDF", "Download as TXT"])

        chat_text = "\n".join([f"{role}: {text}" for role, text in st.session_state['chat_history']])

        if download_format == "Download as PDF":
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
            styles = getSampleStyleSheet()

            from reportlab.lib.styles import ParagraphStyle
            from reportlab.lib.enums import TA_LEFT

            # Custom style that supports HTML
            html_style = ParagraphStyle(
                name="HTMLStyle",
                parent=styles["Normal"],
                fontName="Helvetica",
                fontSize=11,
                leading=14,
                alignment=TA_LEFT,
            )
            def markdown_to_html_bold(text):
                import re
                return re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)

            # ✅ Convert markdown **bold** to <b>bold</b>
            processed_text = markdown_to_html_bold(chat_text)

            # ✅ Build story with color and bold rendering
            story = []
            for line in processed_text.split('\n'):
                if line.strip():
                    if "You:" in line:
                        line = f'<font color="green">{line}</font>'
                    elif "🤖:" in line:
                        line = f'<font color="black">{line}</font>'
                        from reportlab.platypus import HRFlowable
                        story.append(HRFlowable(width="100%", thickness=0.7, color="grey"))
                    story.append(Paragraph(line, html_style))
                else:
                    story.append(Spacer(1, 12))

            doc.build(story)
            buffer.seek(0)

            st.download_button(
                label="📄 Download PDF",
                data=buffer,
                file_name="chat_history.pdf",
                mime="application/pdf"
            )


        elif download_format == "Download as TXT":
            buffer = io.BytesIO(chat_text.encode("utf-8"))
            st.download_button(
                label="📄 Download TXT",
                data=buffer,
                file_name="chat_history.txt",
                mime="text/plain"
            )
        uploaded_image = st.file_uploader("Upload an image:", type=["png", "jpg", "jpeg"])
        uploaded_pdf = st.file_uploader("Upload a PDF:", type=["pdf"])
        uploaded_docx = st.file_uploader("Upload a DOCX:", type=["docx"])
        image_data = None
        pdf_data = None
        docx_data = None

        if uploaded_image is not None:
            image = Image.open(uploaded_image)
            image_data = image

        if uploaded_pdf is not None:
            pdf_data = uploaded_pdf.read()

        if uploaded_docx is not None:
            docx_data = uploaded_docx.read()

    with col1:
        with st.form(key='chat_form', clear_on_submit=True):
            user_input = st.text_input("Input:", key="input", placeholder="Type your message (optional)")
            submit = st.form_submit_button("➤ Send")

        if submit:
            with st.spinner("🤔Thinking..."):
                response = get_gemini_response(prompt=user_input, image=image_data, pdf_data=pdf_data, docx_data=docx_data)
                st.session_state['last_response'] = response

            user_message = user_input
            if uploaded_image is not None:
                user_message += " (Image Uploaded)"
            if uploaded_pdf is not None:
                user_message += " (PDF Uploaded)"
            if uploaded_docx is not None:
                user_message += " (DOCX Uploaded)"

            st.session_state['chat_history'].append(("You", user_message))
            st.session_state['chat_history'].append(("🤖", st.session_state['last_response']))
            st.write("Response:")
            st.write("you:", user_message)
            st.write("🤖",st.session_state['last_response'])


        if st.session_state['show_history']:
            st.markdown("---")
            st.subheader("Chat History:")
            for i in range(0, len(st.session_state['chat_history']), 2):
                user_msg = st.session_state['chat_history'][i]
                bot_msg = st.session_state['chat_history'][i + 1] if i + 1 < len(st.session_state['chat_history']) else ("🤖", "")

                st.markdown(f'<div class="chat-message user-message"><b>{user_msg[0]}:</b> {user_msg[1]}</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="chat-message bot-message"><b>{bot_msg[0]}:</b> {bot_msg[1]}</div>', unsafe_allow_html=True)

                st.markdown("---")  # Horizontal line between each interaction
            st.markdown("---")

    st.button("🗑️ Clear Response", on_click=clear_response)

# Use CSS to position the note at the bottom center
st.markdown(
    """
    <style>
        .bottom-note {
            position: fixed;
            bottom: 10px;
            left: 50%;
            transform: translateX(-50%);
            font-size: small;
            text-align: center;
            width: 100%; /* Ensure it spans the width */
        }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown("<p class='bottom-note'>Note: This is a temporary chat chatbot, and the history is not saved for privacy. If you want to preserve your chats, please download them using the 'Download Chat history' option before refreshing.</p>", unsafe_allow_html=True)

if st.button("🗑️ Clear Chat history"):
    st.session_state['chat_history'] = []
    st.session_state['show_history'] = False
    st.session_state['last_response'] = ""
    st.rerun() # Rerun to hide the chat history section