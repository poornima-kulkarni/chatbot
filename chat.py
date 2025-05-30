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
model = genai.GenerativeModel("gemini-2.0-flash")
chat = model.start_chat(history=[])

# CSS Loading Function
def load_css(file_name):
    """Load CSS file and inject it into Streamlit"""
    try:
        with open(file_name) as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    except FileNotFoundError:
        st.warning(f"CSS file '{file_name}' not found. Using default styling.")

# Enhanced chat message display function
def display_chat_message(role, message, is_user=False):
    """Display chat message with professional styling"""
    css_class = "user-message" if is_user else "bot-message"
    st.markdown(f"""
    <div class="chat-message {css_class} fade-in">
        <b>{role}:</b> {message}
    </div>
    """, unsafe_allow_html=True)

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

# Streamlit page config
st.set_page_config(
    page_title="Chatbot", 
    page_icon=":robot:", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Load custom CSS
load_css('style.css')

# Main title with enhanced styling
st.markdown("""
<h1 style='text-align: center; font-family: "Helvetica Neue", sans-serif;'>🤖 Ephemeral AI</h1>
""", unsafe_allow_html=True)

# Session history initialization
if 'chat_history' not in st.session_state:
    st.session_state['chat_history'] = []
if 'show_history' not in st.session_state:
    st.session_state['show_history'] = False
if 'last_response' not in st.session_state:
    st.session_state['last_response'] = ""

# Helper functions
def toggle_history():
    st.session_state['show_history'] = not st.session_state['show_history']

def clear_response():
    st.session_state['last_response'] = ""

def clear_chat_history():
    st.session_state['chat_history'] = []
    st.session_state['show_history'] = False
    st.rerun()

# Main layout
with st.container():
    col1, col2 = st.columns([6, 2])  # Wider main chat area

    with col2:
        st.markdown("### 📊 Chat Controls")
        
        # History toggle button
        if st.button("📜 Chat History", key="history_btn", help="Toggle chat history display"):
            toggle_history()
        
        # Download options
        download_format = st.selectbox(
            "📁 Download Chat History", 
            ["Select format", "Download as PDF", "Download as TXT"],
            help="Choose format to download your chat history"
        )

        chat_text = "\n".join([f"{role}: {text}" for role, text in st.session_state['chat_history']])

        # PDF Download
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

            # Convert markdown **bold** to <b>bold</b>
            processed_text = markdown_to_html_bold(chat_text)

            # Build story with color and bold rendering
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
                mime="application/pdf",
                help="Download your chat history as a PDF file"
            )

        # TXT Download
        elif download_format == "Download as TXT":
            buffer = io.BytesIO(chat_text.encode("utf-8"))
            st.download_button(
                label="📄 Download TXT",
                data=buffer,
                file_name="chat_history.txt",
                mime="text/plain",
                help="Download your chat history as a text file"
            )
        
        # File uploader
        st.markdown(f"<div class='file'><b>File Upload:</b></div>", unsafe_allow_html=True)
        uploaded_files = st.file_uploader(
            "Upload files (images, PDFs, DOCX):", 
            type=["png", "jpg", "jpeg", "pdf", "docx"], 
            accept_multiple_files=True,
            help="Upload images, PDFs, or Word documents to include in your conversation"
        )

    with col1:
        st.markdown(f"<div class='h4'><b>Type your prompt here:</b></div>", unsafe_allow_html=True)
        # Chat input
        user_input = st.chat_input("Type your message here... (Press Enter to send, Shift+Enter for new line)")
        
        if user_input:
            with st.spinner("🤔 Thinking..."):
                response = get_gemini_response(prompt=user_input, files=uploaded_files)
                st.session_state['last_response'] = response

            # Prepare user message with file info
            user_message = user_input
            if uploaded_files:
                file_names = [file.name for file in uploaded_files]
                user_message += f" (Uploaded: {', '.join(file_names)})"

            # Add to chat history
            st.session_state['chat_history'].append(("You", user_message))
            st.session_state['chat_history'].append(("🤖", st.session_state['last_response']))
            
            # Display current conversation with enhanced styling
            st.markdown(f"<div class='chat-message'><b>You:</b> {user_message}</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='bot'><b>🤖:</b> {st.session_state['last_response']}</div>", unsafe_allow_html=True)

        # Chat history display
        if st.session_state['show_history'] and st.session_state['chat_history']:
            st.markdown("---")
            st.markdown("### 📜 Chat History")
            
            for i in range(0, len(st.session_state['chat_history']), 2):
                user_msg = st.session_state['chat_history'][i]
                bot_msg = st.session_state['chat_history'][i + 1] if i + 1 < len(st.session_state['chat_history']) else ("🤖", "")

                # Use enhanced display function for history too
                display_chat_message(user_msg[0], user_msg[1], is_user=True)
                display_chat_message("🤖", bot_msg[1], is_user=False)
                
                st.markdown("---")  # Horizontal line between each interaction

# Sidebar for control buttons
with st.sidebar:
    st.markdown("### 🛠️ Chat Controls")
    
    st.markdown("""
    <div style="display: flex; flex-direction: column; gap: 10px;">
    """, unsafe_allow_html=True)
    
    # Clear response button
    if st.button("🗑️ Clear Last Response", key="clear_response", help="Clear the last AI response"):
        clear_response()
        st.success("Last response cleared!")
    
    # Clear chat history button
    if st.button("🗑️ Clear Chat History", key="clear_history", help="Clear entire chat history"):
        clear_chat_history()
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Add some helpful info
    st.markdown("---")
    st.markdown("### ℹ️ Quick Tips")
    st.markdown("""
    - **Upload files**: Images, PDFs, and Word docs are supported
    - **Download history**: Save your conversations before refreshing
    - **Privacy**: Your chats are temporary and not stored permanently
    - **File limits**: Check file size limits for uploads
    """)

# Enhanced bottom note with better styling
st.markdown("""<div class="bottom-note"
    <strong>🔒 Privacy Notice:</strong> This is a temporary chat session—your conversation history won't be saved to protect your privacy. 
    Want to keep your chat? Hit 'Download Chat History' before you refresh and lose it all.
</div>
""", unsafe_allow_html=True)