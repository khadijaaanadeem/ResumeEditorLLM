import gradio as gr
import ollama
import os
from typing import Tuple, Optional
import re
import PyPDF2
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
import io
import tempfile

class ResumeEditor:
    def __init__(self):
        # Initialize Ollama client for DeepSeek R1
        self.model_name = "deepseek-r1:latest"
        self.check_ollama_model()
    
    def check_ollama_model(self):
        """Check if DeepSeek R1 model is available in Ollama"""
        try:
            models = ollama.list()
            if 'models' in models:
                model_names = [model.get('name', '') for model in models['models']]
                if self.model_name not in model_names:
                    print(f"Warning: {self.model_name} not found. Available models: {model_names}")
                    print(f"To install DeepSeek R1, run: ollama pull {self.model_name}")
                else:
                    print(f"✅ {self.model_name} is available")
            else:
                print("Warning: Could not retrieve model list from Ollama")
        except Exception as e:
            print(f"Warning: Could not connect to Ollama: {e}")
            print("Make sure Ollama is running. Start it with: ollama serve")
    
    def extract_text_from_pdf(self, pdf_file) -> str:
        """Extract text from uploaded PDF file"""
        try:
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            return text.strip()
        except Exception as e:
            return f"Error reading PDF: {str(e)}"
    
    def create_pdf_from_text(self, text: str) -> str:
        """Create a PDF file from LaTeX-formatted text and return the file path"""
        try:
            # Create a temporary file
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
            temp_file.close()
            
            # Create PDF document
            doc = SimpleDocTemplate(temp_file.name, pagesize=letter,
                                  rightMargin=72, leftMargin=72,
                                  topMargin=72, bottomMargin=18)
            
            # Define styles for LaTeX-like formatting
            styles = getSampleStyleSheet()
            
            # Section header style (for \section{})
            section_style = ParagraphStyle(
                'SectionHeader',
                parent=styles['Heading1'],
                fontSize=14,
                spaceAfter=12,
                spaceBefore=20,
                textColor='#2E4057',
                fontName='Helvetica-Bold'
            )
            
            # Subsection style (for \cventry{})
            subsection_style = ParagraphStyle(
                'SubsectionHeader',
                parent=styles['Heading2'],
                fontSize=12,
                spaceAfter=8,
                spaceBefore=12,
                fontName='Helvetica-Bold'
            )
            
            # Normal text style
            normal_style = ParagraphStyle(
                'CustomNormal',
                parent=styles['Normal'],
                fontSize=10,
                spaceAfter=6,
                leading=12
            )
            
            # Item style (for \cvitem{})
            item_style = ParagraphStyle(
                'ItemStyle',
                parent=styles['Normal'],
                fontSize=10,
                spaceAfter=4,
                leftIndent=20,
                leading=12
            )
            
            # Build PDF content
            story = []
            
            # Process LaTeX-like formatting
            text = self._process_latex_formatting(text)
            
            # Split text into lines and process
            lines = text.split('\n')
            for line in lines:
                line = line.strip()
                if not line:
                    story.append(Spacer(1, 6))
                    continue
                
                # Process LaTeX commands
                if line.startswith('SECTION:'):
                    section_title = line.replace('SECTION:', '').strip()
                    story.append(Paragraph(section_title, section_style))
                elif line.startswith('CVENTRY:'):
                    entry_text = line.replace('CVENTRY:', '').strip()
                    story.append(Paragraph(entry_text, subsection_style))
                elif line.startswith('CVITEM:'):
                    item_text = line.replace('CVITEM:', '').strip()
                    story.append(Paragraph(f"• {item_text}", item_style))
                else:
                    # Regular text
                    line = line.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                    story.append(Paragraph(line, normal_style))
            
            # Build PDF
            doc.build(story)
            
            return temp_file.name
            
        except Exception as e:
            return f"Error creating PDF: {str(e)}"
    
    def _process_latex_formatting(self, text: str) -> str:
        """Convert LaTeX commands to processable format"""
        import re
        
        # Convert \section{} to SECTION:
        text = re.sub(r'\\section\{([^}]+)\}', r'SECTION: \1', text)
        
        # Convert \cventry{} to CVENTRY:
        text = re.sub(r'\\cventry\{([^}]+)\}\{([^}]+)\}\{([^}]+)\}\{([^}]+)\}\{([^}]+)\}\{([^}]*)\}', 
                     r'CVENTRY: \1 | \2 | \3 | \4\n\6', text)
        
        # Convert \cvitem{} to CVITEM:
        text = re.sub(r'\\cvitem\{([^}]+)\}\{([^}]+)\}', r'CVITEM: \1: \2', text)
        
        # Remove other LaTeX commands
        text = re.sub(r'\\[a-zA-Z]+\{[^}]*\}', '', text)
        text = re.sub(r'\\[a-zA-Z]+', '', text)
        
        return text
    
    def edit_resume(self, resume_text: str, job_description: str, pdf_file=None) -> Tuple[str, str, Optional[str]]:
        """
        Edit resume based on job description using Ollama DeepSeek R1
        """
        # Handle PDF input if provided
        if pdf_file is not None:
            resume_text = self.extract_text_from_pdf(pdf_file)
            if resume_text.startswith("Error"):
                return resume_text, "", None
        
        if not resume_text.strip() or not job_description.strip():
            return "Please provide both resume and job description.", "", None
        
        try:
            # Use Ollama DeepSeek R1 for resume editing
            edited_resume = self._ollama_edit_resume(resume_text, job_description)
            
            # Generate analysis
            analysis = self._generate_analysis(resume_text, job_description)
            
            # Create PDF if requested
            pdf_path = None
            if edited_resume and not edited_resume.startswith("Error"):
                pdf_path = self.create_pdf_from_text(edited_resume)
            
            return edited_resume, analysis, pdf_path
            
        except Exception as e:
            return f"Error: {str(e)}", "", None
    
    def _mock_edit_resume(self, resume_text: str, job_description: str) -> str:
        """
        Mock resume editing for demonstration
        """
        # Extract key skills from job description
        job_keywords = self._extract_keywords(job_description)
        
        # Add a note at the top of the resume
        edited_resume = f"""[EDITED RESUME - Tailored for this position]

{resume_text}

--- SUGGESTED ADDITIONS ---
Based on the job description, consider highlighting these skills/keywords:
{', '.join(job_keywords[:10])}

Note: This is a demo version. For full LLM integration, add your OpenAI API key.
"""
        return edited_resume
    
    def _ollama_edit_resume(self, resume_text: str, job_description: str) -> str:
        """
        Use Ollama DeepSeek R1 to extract and tailor resume information
        """
        prompt = f"""
        You must extract resume information and format it exactly as specified. Do not include any thinking, explanations, or commentary. Start your response immediately with "NAME:" and follow the exact format.
        
        FORMAT REQUIRED:
        NAME: [Full Name]
        EMAIL: [Email Address]
        PHONE: [Phone Number]
        LOCATION: [City, State/Country]
        
        SUMMARY: [2-3 line professional summary tailored to the job]
        
        EXPERIENCE:
        - [Job Title] | [Company] | [Dates] | [Location]
          [Bullet point achievement 1 with metrics if possible]
          [Bullet point achievement 2 with metrics if possible]
          [Bullet point achievement 3 with metrics if possible]
        
        EDUCATION:
        - [Degree] | [Institution] | [Year] | [Location]
        
        SKILLS:
        - [Skill Category]: [Relevant skills matching job requirements]
        
        PROJECTS: (if applicable)
        - [Project Name]: [Brief description with technologies used]
        
        Job Requirements:
        {job_description}
        
        Original Resume:
        {resume_text}
        
        Start with NAME: immediately:
        """
        
        try:
            response = ollama.chat(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                options={
                    "temperature": 0.3,  # Lower temperature for more consistent output
                    "top_p": 0.8,
                    "max_tokens": 1500
                }
            )
            
            # Clean the response to remove thinking tags and unwanted content
            cleaned_response = self._clean_llm_output(response['message']['content'])
            
            return cleaned_response
            
        except Exception as e:
            return f"Error connecting to Ollama: {str(e)}\n\nPlease ensure Ollama is running and DeepSeek R1 model is installed.\nRun: ollama pull {self.model_name}"
    
    def _clean_llm_output(self, text: str) -> str:
        """Clean LLM output to remove thinking tags and unwanted content"""
        import re
        
        # Remove <think> tags and their content
        text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
        
        # Remove any remaining XML-like tags
        text = re.sub(r'<[^>]+>', '', text)
        
        # Find the start of the actual resume content (NAME:)
        name_match = re.search(r'NAME:', text, re.IGNORECASE)
        if name_match:
            text = text[name_match.start():]
        
        # Clean up extra whitespace and newlines
        text = re.sub(r'\n\s*\n\s*\n', '\n\n', text)  # Remove excessive newlines
        text = text.strip()
        
        return text
    
    def _openai_edit_resume(self, resume_text: str, job_description: str) -> str:
        """
        Use OpenAI to edit resume (requires API key) - kept for reference
        """
        prompt = f"""
        You are a professional resume editor. Please edit the following resume to better match the job description provided. 
        
        Instructions:
        1. Keep all factual information accurate
        2. Emphasize relevant skills and experiences
        3. Adjust language to match job requirements
        4. Maintain professional formatting
        5. Do not add false information
        
        Job Description:
        {job_description}
        
        Original Resume:
        {resume_text}
        
        Please provide the edited resume:
        """
        
        # Note: This method is kept for reference but not used
        # response = self.client.chat.completions.create(
        #     model="gpt-3.5-turbo",
        #     messages=[{"role": "user", "content": prompt}],
        #     max_tokens=2000,
        #     temperature=0.7
        # )
        # return response.choices[0].message.content
        
        return "OpenAI integration not configured. Using Ollama instead."
    
    def _extract_keywords(self, job_description: str) -> list:
        """
        Extract key skills and requirements from job description
        """
        # Simple keyword extraction (in production, use more sophisticated NLP)
        common_skills = [
            'python', 'javascript', 'react', 'node.js', 'sql', 'aws', 'docker',
            'kubernetes', 'machine learning', 'data analysis', 'project management',
            'agile', 'scrum', 'communication', 'leadership', 'teamwork'
        ]
        
        job_lower = job_description.lower()
        found_keywords = [skill for skill in common_skills if skill in job_lower]
        
        # Also extract capitalized words (likely to be technologies/skills)
        capitalized_words = re.findall(r'\b[A-Z][a-z]+\b', job_description)
        found_keywords.extend(capitalized_words[:5])
        
        return list(set(found_keywords))
    
    def _generate_analysis(self, resume_text: str, job_description: str) -> str:
        """
        Generate analysis of resume vs job requirements
        """
        resume_keywords = self._extract_keywords(resume_text)
        job_keywords = self._extract_keywords(job_description)
        
        matching_skills = set(resume_keywords) & set(job_keywords)
        missing_skills = set(job_keywords) - set(resume_keywords)
        
        analysis = f"""
        📊 RESUME ANALYSIS
        
        ✅ Matching Skills Found: {len(matching_skills)}
        {', '.join(matching_skills) if matching_skills else 'None identified'}
        
        ⚠️ Skills to Highlight: {len(missing_skills)}
        {', '.join(list(missing_skills)[:10]) if missing_skills else 'None identified'}
        
        💡 Recommendations:
        - Emphasize matching skills in your experience descriptions
        - Consider adding projects that demonstrate missing skills
        - Use keywords from the job description in your resume
        - Quantify your achievements where possible
        """
        
        return analysis

def create_interface():
    """
    Create the Gradio interface
    """
    editor = ResumeEditor()
    
    # Enhanced CSS for professional styling
    css = """
    /* Global Styles */
    .gradio-container {
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif !important;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        min-height: 100vh;
    }
    
    /* Main container */
    .container {
        max-width: 1400px;
        margin: auto;
        background: white;
        border-radius: 20px;
        box-shadow: 0 20px 40px rgba(0,0,0,0.1);
        overflow: hidden;
    }
    
    /* Header styling */
    .main-header {
        background: linear-gradient(135deg, #2c3e50 0%, #3498db 100%);
        color: white;
        padding: 30px;
        text-align: center;
        margin-bottom: 0;
    }
    
    .main-header h1 {
        margin: 0;
        font-size: 2.5rem;
        font-weight: 700;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    }
    
    .main-header p {
        margin: 10px 0 0 0;
        font-size: 1.1rem;
        opacity: 0.9;
    }
    
    /* Input sections */
    .input-section {
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        padding: 25px;
        border-radius: 15px;
        margin: 20px;
        border: 1px solid #dee2e6;
        box-shadow: 0 5px 15px rgba(0,0,0,0.08);
    }
    
    /* Output sections */
    .output-section {
        background: linear-gradient(135deg, #e8f5e9 0%, #d4edda 100%);
        padding: 25px;
        border-radius: 15px;
        margin: 20px;
        border: 1px solid #c3e6cb;
        box-shadow: 0 5px 15px rgba(0,0,0,0.08);
    }
    
    /* Tabs styling */
    .tab-nav {
        background: #f8f9fa;
        border-radius: 10px 10px 0 0;
        padding: 5px;
    }
    
    .tab-nav button {
        background: transparent;
        border: none;
        padding: 12px 20px;
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .tab-nav button.selected {
        background: #007bff;
        color: white;
        box-shadow: 0 2px 8px rgba(0,123,255,0.3);
    }
    
    /* Button styling */
    .btn-primary {
        background: linear-gradient(135deg, #007bff 0%, #0056b3 100%) !important;
        border: none !important;
        padding: 15px 30px !important;
        border-radius: 10px !important;
        font-weight: 600 !important;
        font-size: 1.1rem !important;
        box-shadow: 0 5px 15px rgba(0,123,255,0.3) !important;
        transition: all 0.3s ease !important;
    }
    
    .btn-primary:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 25px rgba(0,123,255,0.4) !important;
    }
    
    /* Text areas and inputs */
    .gr-textbox textarea, .gr-textbox input {
        border-radius: 10px !important;
        border: 2px solid #e9ecef !important;
        padding: 15px !important;
        font-size: 14px !important;
        transition: all 0.3s ease !important;
    }
    
    .gr-textbox textarea:focus, .gr-textbox input:focus {
        border-color: #007bff !important;
        box-shadow: 0 0 0 3px rgba(0,123,255,0.1) !important;
    }
    
    /* File upload styling */
    .gr-file {
        border: 2px dashed #007bff !important;
        border-radius: 15px !important;
        padding: 30px !important;
        text-align: center !important;
        background: rgba(0,123,255,0.05) !important;
        transition: all 0.3s ease !important;
    }
    
    .gr-file:hover {
        background: rgba(0,123,255,0.1) !important;
        border-color: #0056b3 !important;
    }
    
    /* Section headers */
    .section-header {
        color: #2c3e50;
        font-size: 1.3rem;
        font-weight: 700;
        margin-bottom: 15px;
        padding-bottom: 10px;
        border-bottom: 3px solid #007bff;
        display: flex;
        align-items: center;
        gap: 10px;
    }
    
    /* Status indicators */
    .status-indicator {
        display: inline-block;
        padding: 5px 12px;
        border-radius: 20px;
        font-size: 0.9rem;
        font-weight: 600;
        margin-left: 10px;
    }
    
    .status-success {
        background: #d4edda;
        color: #155724;
        border: 1px solid #c3e6cb;
    }
    
    .status-warning {
        background: #fff3cd;
        color: #856404;
        border: 1px solid #ffeaa7;
    }
    
    /* Examples section */
    .examples-section {
        background: linear-gradient(135deg, #fff3e0 0%, #ffe0b2 100%);
        padding: 20px;
        border-radius: 15px;
        margin: 20px;
        border: 1px solid #ffcc02;
    }
    
    /* Footer */
    .footer-section {
        background: #f8f9fa;
        padding: 30px;
        text-align: center;
        color: #6c757d;
        border-top: 1px solid #dee2e6;
    }
    
    /* Responsive design */
    @media (max-width: 768px) {
        .container {
            margin: 10px;
            border-radius: 10px;
        }
        
        .main-header h1 {
            font-size: 2rem;
        }
        
        .input-section, .output-section {
            margin: 10px;
            padding: 15px;
        }
    }
    """
    
    with gr.Blocks(css=css, title="🎯 AI Resume Editor - Powered by DeepSeek R1", theme=gr.themes.Soft()) as interface:
        # Header Section
        with gr.Row(elem_classes="main-header"):
            gr.HTML("""
            <div class="main-header">
                <h1>🎯 AI Resume Editor</h1>
                <p>✨ Powered by DeepSeek R1 • Transform your resume for any job opportunity</p>
            </div>
            """)
        
        # Status Section
        with gr.Row():
            with gr.Column():
                gr.HTML("""
                <div style="text-align: center; padding: 20px; background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%); margin: 20px; border-radius: 15px; border: 1px solid #2196f3;">
                    <h3 style="color: #1565c0; margin: 0;">🚀 Ready to Transform Your Resume</h3>
                    <p style="color: #1976d2; margin: 10px 0 0 0;">Upload your resume, add a job description, and let AI tailor it perfectly for you!</p>
                </div>
                """)
        
        with gr.Row():
            with gr.Column(scale=1, elem_classes="input-section"):
                gr.HTML("""
                <div class="section-header">
                    📄 <span>Input Your Resume</span>
                </div>
                """)
                
                with gr.Tabs():
                    with gr.TabItem("📝 Text Input"):
                        gr.HTML("<p style='color: #6c757d; margin-bottom: 10px;'><i>Copy and paste your resume text below</i></p>")
                        resume_input = gr.Textbox(
                            label="Resume Content",
                            placeholder="📝 Paste your complete resume content here...\n\nInclude:\n• Personal information\n• Professional summary\n• Work experience\n• Education\n• Skills\n• Projects (if applicable)",
                            lines=14,
                            max_lines=18,
                            show_label=False
                        )
                    
                    with gr.TabItem("📎 PDF Upload"):
                        gr.HTML("<p style='color: #6c757d; margin-bottom: 10px;'><i>Upload your resume as a PDF file</i></p>")
                        pdf_input = gr.File(
                            label="📎 Drop your PDF resume here or click to browse",
                            file_types=[".pdf"],
                            type="filepath",
                            show_label=False
                        )
                        pdf_text_preview = gr.Textbox(
                            label="📖 Extracted Text Preview",
                            lines=10,
                            max_lines=12,
                            interactive=False,
                            placeholder="📄 Upload a PDF to see the extracted text here...\n\nThis preview shows what text was extracted from your PDF.",
                            show_label=False
                        )
                
                gr.HTML("""
                <div class="section-header" style="margin-top: 30px;">
                    💼 <span>Target Job Description</span>
                </div>
                """)
                gr.HTML("<p style='color: #6c757d; margin-bottom: 10px;'><i>Paste the complete job posting you're applying for</i></p>")
                job_input = gr.Textbox(
                    label="Job Requirements",
                    placeholder="💼 Paste the complete job description here...\n\nInclude:\n• Job title and company\n• Required qualifications\n• Preferred skills\n• Job responsibilities\n• Company culture details",
                    lines=10,
                    max_lines=14,
                    show_label=False
                )
                
                with gr.Row():
                    edit_btn = gr.Button(
                        "🚀 Transform Resume with AI", 
                        variant="primary", 
                        size="lg",
                        elem_classes="btn-primary"
                    )
            
            with gr.Column(scale=1, elem_classes="output-section"):
                gr.HTML("""
                <div class="section-header">
                    📝 <span>AI-Enhanced Resume</span>
                    <span class="status-indicator status-success">DeepSeek R1</span>
                </div>
                """)
                gr.HTML("<p style='color: #6c757d; margin-bottom: 10px;'><i>Your resume optimized for the target position</i></p>")
                edited_output = gr.Textbox(
                    label="Tailored Resume Content",
                    placeholder="🎆 Your AI-enhanced resume will appear here...\n\nThe resume will be:\n• Tailored to match job requirements\n• Optimized with relevant keywords\n• Professionally structured\n• Ready for application",
                    lines=14,
                    max_lines=18,
                    interactive=False,
                    show_label=False
                )
                
                gr.HTML("""
                <div class="section-header" style="margin-top: 30px;">
                    📥 <span>Download Options</span>
                </div>
                """)
                gr.HTML("<p style='color: #6c757d; margin-bottom: 10px;'><i>Download your enhanced resume as a formatted PDF</i></p>")
                pdf_download = gr.File(
                    label="📎 Professional PDF Resume",
                    interactive=False,
                    show_label=False
                )
                
                gr.HTML("""
                <div class="section-header" style="margin-top: 30px;">
                    📊 <span>AI Analysis & Insights</span>
                </div>
                """)
                gr.HTML("<p style='color: #6c757d; margin-bottom: 10px;'><i>Detailed analysis of your resume optimization</i></p>")
                analysis_output = gr.Textbox(
                    label="Resume Analysis Report",
                    placeholder="📈 AI analysis will appear here...\n\nYou'll see:\n• Skills matching analysis\n• Keyword optimization report\n• Improvement recommendations\n• Competitive insights",
                    lines=10,
                    max_lines=14,
                    interactive=False,
                    show_label=False
                )
        
        # Example inputs for testing
        gr.Markdown("### 🔍 Try These Examples")
        
        example_resume = """John Doe
Software Developer

Experience:
- 3 years Python development
- Built web applications using Flask
- Database management with PostgreSQL
- Team collaboration and code reviews

Skills:
- Python, HTML, CSS, JavaScript
- Git, Linux, Problem-solving
- Communication, Teamwork

Education:
- BS Computer Science, 2021
"""
        
        example_job = """Senior Python Developer
We are looking for an experienced Python developer to join our team.

Requirements:
- 3+ years Python experience
- Experience with Django or Flask
- Knowledge of AWS cloud services
- Docker containerization
- Agile development methodology
- Strong communication skills
- Experience with React.js is a plus

Responsibilities:
- Develop scalable web applications
- Collaborate with cross-functional teams
- Implement best practices for code quality
"""
        
        gr.Examples(
            examples=[[example_resume, example_job]],
            inputs=[resume_input, job_input],
            label="Click to load example"
        )
        
        # PDF preview functionality
        def preview_pdf(pdf_file):
            if pdf_file is None:
                return ""
            try:
                return editor.extract_text_from_pdf(pdf_file)
            except Exception as e:
                return f"Error reading PDF: {str(e)}"
        
        # Wrapper function for the edit button
        def edit_resume_wrapper(resume_text, job_desc, pdf_file):
            result = editor.edit_resume(resume_text, job_desc, pdf_file)
            if len(result) == 3:
                edited_text, analysis, pdf_path = result
                return edited_text, analysis, pdf_path
            else:
                # Fallback for compatibility
                return result[0], result[1], None
        
        # Connect PDF upload to preview
        pdf_input.change(
            fn=preview_pdf,
            inputs=[pdf_input],
            outputs=[pdf_text_preview]
        )
        
        # Connect the edit button to the function
        edit_btn.click(
            fn=edit_resume_wrapper,
            inputs=[resume_input, job_input, pdf_input],
            outputs=[edited_output, analysis_output, pdf_download]
        )
        
        # Footer Section
        gr.HTML("""
        <div class="footer-section">
            <div style="max-width: 800px; margin: auto;">
                <h3 style="color: #2c3e50; margin-bottom: 20px;">🚀 Setup Instructions</h3>
                
                <div style="text-align: left; margin-bottom: 30px;">
                    <p><strong>1.</strong> Ensure Ollama is running: <code>ollama serve</code></p>
                    <p><strong>2.</strong> Install DeepSeek R1 model: <code>ollama pull deepseek-r1:latest</code></p>
                    <p><strong>3.</strong> Install required packages: <code>pip install ollama PyPDF2 reportlab gradio</code></p>
                </div>
                
                <h3 style="color: #2c3e50; margin-bottom: 20px;">📋 Features</h3>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 15px; margin-bottom: 30px;">
                    <div style="background: #f8f9fa; padding: 15px; border-radius: 10px; border-left: 4px solid #007bff;">
                        <strong>🔍 Resume Analysis</strong><br>
                        <small>Identifies matching and missing skills</small>
                    </div>
                    <div style="background: #f8f9fa; padding: 15px; border-radius: 10px; border-left: 4px solid #28a745;">
                        <strong>🎯 Keyword Optimization</strong><br>
                        <small>Suggests relevant keywords from job description</small>
                    </div>
                    <div style="background: #f8f9fa; padding: 15px; border-radius: 10px; border-left: 4px solid #ffc107;">
                        <strong>📄 Professional Formatting</strong><br>
                        <small>Maintains resume structure and LaTeX output</small>
                    </div>
                    <div style="background: #f8f9fa; padding: 15px; border-radius: 10px; border-left: 4px solid #dc3545;">
                        <strong>💡 AI Recommendations</strong><br>
                        <small>Provides actionable improvement suggestions</small>
                    </div>
                </div>
                
                <hr style="border: none; height: 1px; background: #dee2e6; margin: 30px 0;">
                
                <div style="text-align: center; color: #6c757d;">
                    <p style="margin: 10px 0;">✨ <strong>Developed by Khadija Nadeem</strong> ✨</p>
                    <p style="margin: 5px 0;">📧 <a href="mailto:khadija.nadeem714@gmail.com" style="color: #007bff; text-decoration: none;">khadija.nadeem714@gmail.com</a></p>
                    <p style="margin: 15px 0 5px 0; font-size: 0.9rem;">Powered by <strong>DeepSeek R1</strong> • Built with <strong>Gradio</strong> & <strong>Python</strong></p>
                    <p style="margin: 5px 0; font-size: 0.8rem; opacity: 0.8;">© 2024 AI Resume Editor - Transform your career with AI</p>
                </div>
            </div>
        </div>
        """)
    
    return interface

if __name__ == "__main__":
    interface = create_interface()
    interface.launch(
        server_name="127.0.0.1",
        server_port=None,  # Let Gradio find an available port
        share=True,
        debug=True
    )
