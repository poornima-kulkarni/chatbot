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
def get_gemini_response(prompt=None, files=None):
    contents = []
    if prompt:
        contents.append(prompt)
    if files:
        for uploaded_file in files:
            file_type = uploaded_file.type
            file_bytes = uploaded_file.read()
            if "image" in file_type:
                try:
                    image = Image.open(io.BytesIO(file_bytes))
                    contents.append(image)
                except Exception as e:
                    st.error(f"Error processing image: {e}")
            elif file_type == "application/pdf":
                contents.append({"mime_type": "application/pdf", "data": file_bytes})
            elif "docx" in file_type:
                try:
                    from docx import Document
                    doc = Document(io.BytesIO(file_bytes))
                    full_text = []
                    for para in doc.paragraphs:
                        full_text.append(para.text)
                    contents.append("\n".join(full_text))
                except ImportError:
                    st.warning("docx library not found. Docx files will be treated as binary.")
                    contents.append(file_bytes.decode('latin-1', errors='ignore')) # Basic decoding
                except Exception as e:
                    st.error(f"Error processing docx file: {e}")
                    contents.append(file_bytes.decode('latin-1', errors='ignore')) # Basic decoding
            else:
                st.warning(f"Unsupported file type: {file_type}")

    if not contents:
        return ""
    response = chat.send_message(contents, stream=True)
    return "".join([chunk.text for chunk in response])

# Streamlit page config - Added initial_sidebar_state="collapsed"
st.set_page_config(
    page_title="Chatbot", 
    page_icon=":robot:", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""

<h1 style='text-align: center; font-family: "Helvetica Neue";'>🤖 Ephemeral AI</h1>

""", unsafe_allow_html=True)

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
        uploaded_files = st.file_uploader("Upload files (images, PDFs, DOCX):", type=["png", "jpg", "jpeg", "pdf", "docx"], accept_multiple_files=True)

    with col1:
        user_input = st.chat_input("Type your message here... (Press Enter to send, Shift+Enter for new line)")
        if user_input:
            with st.spinner("🤔Thinking..."):
                response = get_gemini_response(prompt=user_input, files=uploaded_files)
                st.session_state['last_response'] = response

            user_message = user_input
            if uploaded_files:
                file_names = [file.name for file in uploaded_files]
                user_message += f" (Uploaded: {', '.join(file_names)})"

            st.session_state['chat_history'].append(("You", user_message))
            st.session_state['chat_history'].append(("🤖", st.session_state['last_response']))
            st.markdown(f"<div><b>You:</b> {user_message}</div>", unsafe_allow_html=True)
            st.markdown(f"<div><b>🤖:</b> {st.session_state['last_response']}</div>", unsafe_allow_html=True)


        if st.session_state['show_history']:
            st.markdown("---")
            st.subheader("Chat History:")
            for i in range(0, len(st.session_state['chat_history']), 2):
                user_msg = st.session_state['chat_history'][i]
                bot_msg = st.session_state['chat_history'][i + 1] if i + 1 < len(st.session_state['chat_history']) else ("🤖", "")

                st.markdown(f"<div><b>{user_msg[0]}:</b> {user_msg[1]}</div>", unsafe_allow_html=True)
                st.markdown(f"<div><b>🤖:</b> {bot_msg[1]}</div>", unsafe_allow_html=True)

                st.markdown("---")  # Horizontal line between each interaction
            st.markdown("---")

# Sidebar for bottom buttons - Now collapsed by default
with st.sidebar:
    st.markdown(
        """
        <style>
            .bottom-buttons {
                display: flex;
                flex-direction: column;
                gap: 10px;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("<div class='bottom-buttons'>", unsafe_allow_html=True)
    st.button("🗑️ Clear Response", on_click=clear_response)
    if st.button("🗑️ Clear Chat history"):
        st.session_state['chat_history'] = []
        st.session_state['show_history'] = False
        st.rerun() # Rerun to hide the chat history section
    st.markdown("</div>", unsafe_allow_html=True)

# Note at the very bottom (outside sidebar)
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
            width: 100%;
        }
    </style>
    """,
    unsafe_allow_html=True,
)
st.markdown("<p class='bottom-note'>Note: This is a temporary chat session—your conversation history won't be saved to protect your privacy. Want to keep your chat? Hit 'Download Chat History' before you refresh and lose it all.</p>", unsafe_allow_html=True)