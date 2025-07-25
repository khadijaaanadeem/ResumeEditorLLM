# 📄 Resume Editor using DeepSeek LLM (Ollama + Gradio)

An AI-powered resume editor that takes in a user's resume (PDF or text) and a job description, then generates customized suggestions and produces an improved resume version in both PDF and text formats — all through an intuitive Gradio UI.

## 🚀 Features

- 🔍 **Resume + Job Description Analysis**: Accepts PDF or plain text resumes and a job summary.
- 💡 **LLM-Powered Suggestions**: Uses DeepSeek LLM via [Ollama](https://ollama.com/) to intelligently revise content.
- 📄 **Outputs Editable Text + Downloadable PDF**.
- 🧠 **Understands Tone, Skills, and Relevance**: Tailors changes to match job requirements and tone.
- 🎨 **User-Friendly Interface**: Built with [Gradio](https://www.gradio.app/) for easy upload, input, and download.

## 🛠️ Tech Stack

- **LLM**: [DeepSeek LLM](https://ollama.com/library/deepseek-coder) (via Ollama)
- **Frontend**: Gradio
- **Backend**: Python (PDFMiner, fpdf, etc.)
- **Parsing**: PyMuPDF, regex-based text extraction

## 🧪 How It Works

1. 📤 Upload your current resume (PDF or raw text).
2. 🧾 Paste the job description you want to apply for.
3. ⚙️ The LLM analyzes your content, context, and tone.
4. 📝 Generates tailored content changes (e.g. rewrites, skills matches, tone alignment).
5. 📁 Outputs:
    - Improved version in **editable text** format
    - Automatically converted **PDF version**

## 📷 UI Preview

> Upload → Input JD → View suggestions → Download updated resume

![Gradio UI Screenshot](your_screenshot.png) <!-- Replace with actual screenshot path -->

## 📦 Setup Instructions

```bash
# Clone the repo
git clone https://github.com/yourusername/resume-editor-llm.git
cd resume-editor-llm

# Set up Python environment
pip install -r requirements.txt

# Start Ollama (make sure DeepSeek is pulled)
ollama run deepseek-coder

# Run the app
python app.py
