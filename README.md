# 🤖 ChatBot

[![Python](https://img.shields.io/badge/Python-3.7%2B-blue.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28%2B-red.svg)](https://streamlit.io/)
[![Gemini API](https://img.shields.io/badge/Gemini-API-green.svg)](https://ai.google.dev/)
[![Privacy First](https://img.shields.io/badge/Privacy-First-orange.svg)](#privacy-features)

A privacy-focused, intelligent chatbot powered by Google's Gemini AI with multi-modal input support and zero permanent data storage.

## ✨ Features

🔒 **Privacy-First Design** - No permanent chat history storage  
📁 **Multi-Modal Input** - Upload files and images with your prompts  
💬 **Intelligent Conversations** - Powered by Google Gemini API  
📄 **Export Options** - Download chat history as PDF or TXT  
🎨 **Custom UI** - Beautiful interface with custom CSS styling  
⚡ **Session-Based** - Fast, temporary conversation memory  

## 🚀 Quick Start

### Prerequisites
- Python 3.7+
- Google Gemini API key ([Get one here](https://ai.google.dev/))

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/gemini-chatbot.git
   cd gemini-chatbot
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   ```bash
   # Create .env file
   echo "GEMINI_API_KEY=your_api_key_here" > .env
   ```

4. **Run the application**
   ```bash
   streamlit run app.py
   ```

5. **Open your browser** to `http://localhost:8501`

## 🖥️ Usage

### Basic Chat
1. Enter your message in the text input
2. Press Enter or click Send
3. Get AI-powered responses instantly

### File Upload
- Click the file uploader
- Select images or documents
- Add your text prompt
- The AI will analyze both text and files

### Export Chat History
1. Use the "Download Chat History" dropdown
2. Choose format: PDF or TXT
3. Your conversation downloads automatically

## 🔐 Privacy Features

- **Zero Persistence** - Chats are never saved to disk
- **Session Only** - History exists only while browser is open
- **User Control** - You decide what to export and when
- **Secure API** - Keys stored in environment variables
- **No Tracking** - No analytics or user behavior logging

## 🏗️ Project Structure

```
chatbot/
├── app.py              # Main Streamlit application
├── .env               # Environment variables (create this)
├── requirements.txt   # Python dependencies
├── README.md         # Project documentation
└── .gitignore       # Git ignore file
```

## ⚙️ Configuration

### Environment Variables
Create a `.env` file in the project root:

```env
GEMINI_API_KEY=your_gemini_api_key_here
```

### Customization
- Modify CSS styles in the Streamlit app
- Adjust export formats and styling
- Configure AI model parameters

## 🛠️ Development

### Running in Development Mode
```bash
streamlit run app.py --server.runOnSave true
```

### Code Structure
- **UI Layer**: Streamlit components and custom CSS
- **AI Layer**: Gemini API integration and response handling
- **Export Layer**: PDF and TXT generation with ReportLab

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📋 To-Do

- [ ] Add more export formats (Word, HTML)
- [ ] Implement conversation themes
- [ ] Add file type validation
- [ ] Create mobile-responsive design
- [ ] Add conversation statistics (session-only)

## ⚠️ Troubleshooting

**API Key Issues**
- Ensure your `.env` file exists and contains a valid Gemini API key
- Check API quota limits in Google AI Studio

**Import Errors**
- Verify all dependencies are installed: `pip install -r requirements.txt`
- Check Python version compatibility (3.7+)

**File Upload Problems**
- Ensure files are within size limits
- Check supported file formats

## 🙏 Acknowledgments

- Google Gemini AI for powering the conversations
- Streamlit for the amazing web framework
- ReportLab for PDF generation capabilities

## 📞 Support

If you encounter any issues or have questions:
- Open an issue on GitHub
- Check the troubleshooting section
- Review the full documentation

---

**Made with ❤️ and Python** | **Privacy-First AI Chatbot**

