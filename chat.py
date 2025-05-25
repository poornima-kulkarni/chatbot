from dotenv import load_dotenv
import streamlit as st
import os
import google.generativeai as genai

# Load environment variables
load_dotenv()

# Configure the Gemini model
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
model = genai.GenerativeModel("gemini-1.5-flash")
chat = model.start_chat(history=[])

# Function to get Gemini response
def get_gemini_response(question):
    response = chat.send_message(question, stream=True)
    full_response = ""
    for chunk in response:
        full_response += chunk.text
    return full_response

# Initialize Streamlit app
st.set_page_config(page_title="Chatbot", page_icon=":robot:", layout="centered")
st.header("Chatbot🤖")

# Initializing temporary chat history
if 'chat_history' not in st.session_state:
    st.session_state['chat_history'] = []

# Converting chat history to plain text
import io
col1, col2, col3 = st.columns([4, 1, 2]) 

with col3:
    chat_text = "\n".join([f"{role}: {text}" for role, text in st.session_state['chat_history']])
    buffer = io.BytesIO(chat_text.encode("utf-8"))

    # Show just one persistent download button
    st.download_button(
        label="📄 Download Chat",
        data=buffer,
        file_name="chat.pdf",
        mime="text/plain"
    )   

# Input form to allow enter-key submission
with st.form(key='chat_form', clear_on_submit=True):
    input = st.text_input("Input: ", key="input", placeholder="Type your message...")
    submit = st.form_submit_button("➤")  # Send button emoji

# When submit is clicked or Enter is pressed
if submit and input:
    with st.spinner("Thinking..."):
        response = get_gemini_response(input)

    # Add to chat history
    st.session_state['chat_history'].append(("You", input))
    st.session_state['chat_history'].append(("🤖", response))

    # Show the response
    st.write("Response:")
    st.write(response)

# Display chat history
st.markdown('---')
st.subheader("Chat History:")
for role, text in st.session_state['chat_history']:
    st.write(f"{role}: {text}")

if st.button("🗑️ Clear Chat"):
    st.session_state['chat_history'] = []





