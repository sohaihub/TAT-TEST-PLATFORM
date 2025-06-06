import streamlit as st
import smtplib
import ssl
import os
import json
import time
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict, Any
import hashlib
import uuid

# Set page config
st.set_page_config(
    page_title="TAT Technical Assessment Platform", 
    layout="wide", 
    page_icon="🎯",
    initial_sidebar_state="collapsed"
)

# Custom CSS for better UI
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    .test-container {
        background: #f8f9fa;
        padding: 2rem;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .timer-display {
        position: fixed;
        top: 20px;
        right: 20px;
        background: #ff6b6b;
        color: white;
        padding: 10px 20px;
        border-radius: 25px;
        font-weight: bold;
        font-size: 18px;
        z-index: 1000;
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
    .question-card {
        background: white;
        padding: 1.5rem;
        border-radius: 8px;
        border-left: 4px solid #667eea;
        margin-bottom: 1rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .score-display {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 2rem;
        border-radius: 10px;
        text-align: center;
        margin: 2rem 0;
    }
    .login-form {
        max-width: 400px;
        margin: 0 auto;
        padding: 2rem;
        background: white;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
</style>
""", unsafe_allow_html=True)

# Email configuration
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

# Test questions database
TEST_QUESTIONS = [
    {
        "id": 1,
        "question": "What is the planned timeline for the TAT MVP development?",
        "options": [
            "Q2 2024 for development, Q3 2024 for launch",
            "Q3 2024 for development, Q4 2024 for testing and launch",
            "Q4 2024 for development, Q1 2025 for launch",
            "Q1 2025 for development, Q2 2025 for launch"
        ],
        "correct_answer": 1,
        "explanation": "According to the TAT roadmap, Q3 2024 is allocated for MVP development (Sprints 1-4), and Q4 2024 is for testing and launch (Sprints 5-6)."
    },
    {
        "id": 2,
        "question": "Which of the following is NOT a core feature of the TAT MVP?",
        "options": [
            "Resume Analyser AI model",
            "LMS Library Integration",
            "Video Interview Recording",
            "NLP for Candidate Responses"
        ],
        "correct_answer": 2,
        "explanation": "The core MVP features are Resume Analyser, LMS Library Integration, NLP for Candidate Responses, and Evaluator System. Video Interview Recording is not mentioned as a core MVP feature."
    },
    {
        "id": 3,
        "question": "Which cloud provider is preferred for hosting the TAT system?",
        "options": [
            "Microsoft Azure",
            "Google Cloud Platform",
            "Amazon Web Services (AWS)",
            "IBM Cloud"
        ],
        "correct_answer": 2,
        "explanation": "According to the technical documentation, AWS (Amazon Web Services) is mentioned as the preferred cloud provider for the TAT system."
    },
    {
        "id": 4,
        "question": "What is the primary problem TAT aims to solve for recruiters?",
        "options": [
            "Finding candidates with specific certifications",
            "Efficiently assessing candidates' technical skills",
            "Managing candidate databases",
            "Conducting video interviews"
        ],
        "correct_answer": 1,
        "explanation": "The primary job to be done for recruiters is to efficiently assess candidates' technical skills and ensure they are well-suited for the roles they are hiring for."
    },
    {
        "id": 5,
        "question": "What does TAT stand for in the context of this technical assessment system?",
        "options": [
            "Technical Assessment Tool",
            "Talent Acquisition Technology",
            "Test Analysis Tool",
            "Technical Aptitude Test"
        ],
        "correct_answer": 0,
        "explanation": "TAT stands for Technical Assessment Tool, which is an AI/ML-based automated technical interview system designed to assess candidates' technical capabilities."
    },
    {
        "id": 6,
        "question": "Which frontend technologies are mentioned in the TAT tech stack?",
        "options": [
            "React.js, Angular, Bootstrap",
            "HTML, CSS, JavaScript, React.js/Vue.js, Tailwind CSS/Bootstrap",
            "Vue.js, Svelte, Material-UI",
            "Angular, TypeScript, Sass"
        ],
        "correct_answer": 1,
        "explanation": "The tech stack specifically mentions HTML, CSS, JavaScript, React.js/Vue.js, and Tailwind CSS/Bootstrap for frontend development."
    },
    {
        "id": 7,
        "question": "What is the duration of Sprint 1 in the TAT development roadmap?",
        "options": [
            "Aug 30 - Sep 1",
            "Sep 1 - Sep 14",
            "Sep 15 - Sep 28",
            "Sep 29 - Oct 12"
        ],
        "correct_answer": 1,
        "explanation": "Sprint 1 (Resume Analyser Development) is scheduled from Sep 1 - Sep 14 according to the agile roadmap."
    },
    {
        "id": 8,
        "question": "Which ML/NLP libraries are mentioned in the TAT tech stack?",
        "options": [
            "Scikit-learn, Keras, OpenCV",
            "TensorFlow, PyTorch, Pandas",
            "Scikit-learn, TensorFlow/PyTorch, SpaCy/NLTK",
            "BERT, GPT, Transformers only"
        ],
        "correct_answer": 2,
        "explanation": "The tech stack mentions Scikit-learn, TensorFlow/PyTorch, and SpaCy/NLTK as the ML and NLP libraries."
    },
    {
        "id": 9,
        "question": "What is included in the Evaluator System features?",
        "options": [
            "Only response assessment and feedback",
            "Response assessment, code editor integration, fairness control, and real-time image capture",
            "Just automated grading",
            "Only bias control mechanisms"
        ],
        "correct_answer": 1,
        "explanation": "The Evaluator System includes response assessment and feedback, code editor/IDE integration, fairness and bias control, and real-time image capture and comparison."
    },
    {
        "id": 10,
        "question": "When is the official launch planned for TAT?",
        "options": [
            "November 10-17, 2024",
            "December 8-15, 2024",
            "Q1 2025",
            "Q2 2025"
        ],
        "correct_answer": 1,
        "explanation": "The official launch is planned for Release 2 (Post-MVP) during December 8-15, 2024, which includes final testing and official launch activities."
    }
]

# Initialize session state
def initialize_session_state():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if "user_email" not in st.session_state:
        st.session_state.user_email = ""
    if "user_name" not in st.session_state:
        st.session_state.user_name = ""
    if "test_started" not in st.session_state:
        st.session_state.test_started = False
    if "test_completed" not in st.session_state:
        st.session_state.test_completed = False
    if "start_time" not in st.session_state:
        st.session_state.start_time = None
    if "end_time" not in st.session_state:
        st.session_state.end_time = None
    if "current_question" not in st.session_state:
        st.session_state.current_question = 0
    if "answers" not in st.session_state:
        st.session_state.answers = {}
    if "time_remaining" not in st.session_state:
        st.session_state.time_remaining = 3600  # 1 hour in seconds

def send_email(recipient_email: str, subject: str, body: str, sender_email: str, sender_password: str):
    """Send email notification"""
    try:
        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = sender_email
        message["To"] = recipient_email
        
        html_part = MIMEText(body, "html")
        message.attach(html_part)
        
        context = ssl.create_default_context()
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls(context=context)
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, recipient_email, message.as_string())
        return True
    except Exception as e:
        st.error(f"Failed to send email: {str(e)}")
        return False

def authenticate_user(email: str, password: str):
    """Simple authentication using email and password"""
    # In a real application, you would validate against a database
    # For demo purposes, we'll use a simple validation
    if email and "@" in email and len(password) >= 6:
        return True
    return False

def calculate_score(answers: Dict[int, int]) -> tuple:
    """Calculate test score and detailed results"""
    correct_count = 0
    total_questions = len(TEST_QUESTIONS)
    detailed_results = []
    
    for question in TEST_QUESTIONS:
        user_answer = answers.get(question["id"], -1)
        is_correct = user_answer == question["correct_answer"]
        if is_correct:
            correct_count += 1
        
        detailed_results.append({
            "question": question["question"],
            "user_answer": question["options"][user_answer] if user_answer >= 0 else "Not answered",
            "correct_answer": question["options"][question["correct_answer"]],
            "is_correct": is_correct,
            "explanation": question["explanation"]
        })
    
    score_percentage = (correct_count / total_questions) * 100
    return score_percentage, correct_count, total_questions, detailed_results

def format_time(seconds: int) -> str:
    """Format seconds into MM:SS format"""
    minutes = seconds // 60
    seconds = seconds % 60
    return f"{minutes:02d}:{seconds:02d}"

def login_page():
    """Display login page"""
    st.markdown("""
    <div class="main-header">
        <h1>🎯 TAT Technical Assessment Platform</h1>
        <p>AI-Powered Technical Interview System</p>
    </div>
    """, unsafe_allow_html=True)
    
    with st.container():
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown('<div class="login-form">', unsafe_allow_html=True)
            st.markdown("### 🔐 User Authentication")
            
            with st.form("login_form", clear_on_submit=False):
                name = st.text_input("👤 Full Name", placeholder="Enter your full name")
                email = st.text_input("📧 Email Address", placeholder="Enter your email")
                password = st.text_input("🔒 Password", type="password", placeholder="Enter password (min 6 characters)")
                
                receiver_email = st.text_input("📨 Receiver Email", placeholder="Email to send results (HR/Recruiter)")
                
                st.markdown("---")
                st.markdown("**📋 Test Information:**")
                st.info("""
                • **Duration:** 60 minutes
                • **Questions:** 10 MCQs
                • **Topics:** TAT System Features, Roadmap, Tech Stack
                • **Passing Score:** 70%
                """)
                
                submitted = st.form_submit_button("🚀 Start Test", type="primary", use_container_width=True)
                
                if submitted:
                    if not name or not email or not password or not receiver_email:
                        st.error("❌ Please fill in all fields")
                    elif not authenticate_user(email, password):
                        st.error("❌ Invalid credentials. Email must be valid and password must be at least 6 characters.")
                    else:
                        st.session_state.authenticated = True
                        st.session_state.user_name = name
                        st.session_state.user_email = email
                        st.session_state.receiver_email = receiver_email
                        st.success("✅ Authentication successful! Starting test...")
                        time.sleep(1)
                        st.rerun()
            
            st.markdown('</div>', unsafe_allow_html=True)

def test_page():
    """Display test page"""
    # Initialize test if not started
    if not st.session_state.test_started:
        st.session_state.test_started = True
        st.session_state.start_time = datetime.now()
    
    # Calculate time remaining
    if st.session_state.start_time:
        elapsed_time = (datetime.now() - st.session_state.start_time).total_seconds()
        st.session_state.time_remaining = max(0, 3600 - int(elapsed_time))
        
        # Auto-submit if time is up
        if st.session_state.time_remaining <= 0:
            st.session_state.test_completed = True
            st.session_state.end_time = datetime.now()
            st.rerun()
    
    # Display timer
    st.markdown(f"""
    <div class="timer-display">
        ⏰ {format_time(st.session_state.time_remaining)}
    </div>
    """, unsafe_allow_html=True)
    
    # Header
    st.markdown(f"""
    <div class="main-header">
        <h1>📝 TAT Technical Assessment</h1>
        <p>Welcome, {st.session_state.user_name}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Progress bar
    progress = (st.session_state.current_question) / len(TEST_QUESTIONS)
    st.progress(progress, text=f"Question {st.session_state.current_question + 1} of {len(TEST_QUESTIONS)}")
    
    # Current question
    if st.session_state.current_question < len(TEST_QUESTIONS):
        question = TEST_QUESTIONS[st.session_state.current_question]
        
        st.markdown('<div class="test-container">', unsafe_allow_html=True)
        st.markdown(f'<div class="question-card">', unsafe_allow_html=True)
        
        st.markdown(f"### Question {question['id']}")
        st.markdown(f"**{question['question']}**")
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Answer options
        with st.form(f"question_{question['id']}", clear_on_submit=False):
            selected_option = st.radio(
                "Select your answer:",
                options=range(len(question['options'])),
                format_func=lambda x: f"{chr(65+x)}) {question['options'][x]}",
                key=f"q_{question['id']}"
            )
            
            col1, col2, col3 = st.columns([1, 1, 1])
            
            with col1:
                if st.form_submit_button("⬅️ Previous", disabled=st.session_state.current_question == 0):
                    st.session_state.answers[question["id"]] = selected_option
                    st.session_state.current_question -= 1
                    st.rerun()
            
            with col2:
                if st.form_submit_button("➡️ Next", type="primary"):
                    st.session_state.answers[question["id"]] = selected_option
                    if st.session_state.current_question < len(TEST_QUESTIONS) - 1:
                        st.session_state.current_question += 1
                    st.rerun()
            
            with col3:
                if st.form_submit_button("✅ Submit Test", type="secondary"):
                    st.session_state.answers[question["id"]] = selected_option
                    st.session_state.test_completed = True
                    st.session_state.end_time = datetime.now()
                    st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Question navigation
        st.markdown("### 📋 Question Navigation")
        cols = st.columns(10)
        for i, q in enumerate(TEST_QUESTIONS):
            with cols[i]:
                status = "✅" if q["id"] in st.session_state.answers else "⭕"
                if st.button(f"{status} {i+1}", key=f"nav_{i}"):
                    if st.session_state.current_question < len(TEST_QUESTIONS):
                        current_q = TEST_QUESTIONS[st.session_state.current_question]
                        # Save current answer if any option is selected
                        if f"q_{current_q['id']}" in st.session_state:
                            st.session_state.answers[current_q["id"]] = st.session_state[f"q_{current_q['id']}"]
                    st.session_state.current_question = i
                    st.rerun()

def results_page():
    """Display results page"""
    score_percentage, correct_count, total_questions, detailed_results = calculate_score(st.session_state.answers)
    
    # Calculate test duration
    test_duration = st.session_state.end_time - st.session_state.start_time
    duration_minutes = int(test_duration.total_seconds() // 60)
    duration_seconds = int(test_duration.total_seconds() % 60)
    
    # Display results
    st.markdown(f"""
    <div class="score-display">
        <h1>🎉 Test Completed!</h1>
        <h2>Score: {score_percentage:.1f}% ({correct_count}/{total_questions})</h2>
        <p>Duration: {duration_minutes}m {duration_seconds}s</p>
        <p>Completed at: {st.session_state.end_time.strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Performance analysis
    if score_percentage >= 70:
        st.success("🎯 **Excellent Performance!** You have passed the assessment.")
    elif score_percentage >= 50:
        st.warning("⚠️ **Good Effort!** You may need to review some concepts.")
    else:
        st.error("❌ **Needs Improvement** Please review the study materials.")
    
    # Detailed results
    with st.expander("📊 Detailed Results", expanded=True):
        for i, result in enumerate(detailed_results, 1):
            status = "✅" if result["is_correct"] else "❌"
            st.markdown(f"**{i}. {result['question']}**")
            st.markdown(f"Your Answer: {result['user_answer']} {status}")
            if not result["is_correct"]:
                st.markdown(f"Correct Answer: {result['correct_answer']}")
                st.info(f"💡 {result['explanation']}")
            st.markdown("---")
    
    # Email results
    st.markdown("### 📧 Email Results")
    
    # Email configuration
    with st.expander("Email Settings", expanded=False):
        sender_email = st.text_input("Sender Email (Gmail)", value="", help="Enter the Gmail address to send from")
        sender_password = st.text_input("App Password", type="password", help="Gmail App Password (not regular password)")
        
        st.info("💡 **Setup Gmail App Password:**\n1. Enable 2FA on Gmail\n2. Go to Google Account Settings\n3. Security > App Passwords\n4. Generate password for 'Mail'")
    
    if st.button("📨 Send Results Email", type="primary"):
        if not sender_email or not sender_password:
            st.error("Please provide sender email and app password")
        else:
            # Prepare email content
            email_subject = f"TAT Assessment Results - {st.session_state.user_name}"
            
            email_body = f"""
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="background: linear-gradient(90deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; text-align: center;">
                    <h1>TAT Technical Assessment Results</h1>
                </div>
                
                <div style="padding: 20px;">
                    <h2>Candidate Information</h2>
                    <p><strong>Name:</strong> {st.session_state.user_name}</p>
                    <p><strong>Email:</strong> {st.session_state.user_email}</p>
                    <p><strong>Test Date:</strong> {st.session_state.end_time.strftime('%Y-%m-%d %H:%M:%S')}</p>
                    
                    <h2>Test Results</h2>
                    <div style="background: #f8f9fa; padding: 15px; border-radius: 5px; margin: 10px 0;">
                        <p><strong>Score:</strong> {score_percentage:.1f}% ({correct_count}/{total_questions})</p>
                        <p><strong>Duration:</strong> {duration_minutes}m {duration_seconds}s</p>
                        <p><strong>Status:</strong> {'PASSED' if score_percentage >= 70 else 'FAILED'}</p>
                    </div>
                    
                    <h2>Detailed Results</h2>
                    <table style="width: 100%; border-collapse: collapse; margin-top: 10px;">
                        <tr style="background-color: #f2f2f2;">
                            <th style="border: 1px solid #ddd; padding: 8px; text-align: left;">Question</th>
                            <th style="border: 1px solid #ddd; padding: 8px; text-align: center;">Result</th>
                        </tr>
            """
            
            for i, result in enumerate(detailed_results, 1):
                status = "✅ Correct" if result["is_correct"] else "❌ Incorrect"
                email_body += f"""
                        <tr>
                            <td style="border: 1px solid #ddd; padding: 8px;">{i}. {result['question'][:50]}...</td>
                            <td style="border: 1px solid #ddd; padding: 8px; text-align: center;">{status}</td>
                        </tr>
                """
            
            email_body += """
                    </table>
                    
                    <div style="margin-top: 30px; padding: 15px; background: #e7f3ff; border-radius: 5px;">
                        <p><em>This is an automated email from the TAT Technical Assessment Platform.</em></p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            # Send email
            with st.spinner("Sending email..."):
                if send_email(st.session_state.receiver_email, email_subject, email_body, sender_email, sender_password):
                    st.success(f"✅ Results sent successfully to {st.session_state.receiver_email}")
                else:
                    st.error("❌ Failed to send email. Please check your credentials.")
    
    # Restart option
    st.markdown("---")
    if st.button("🔄 Take Another Test", type="secondary"):
        # Reset all session state
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

def main():
    """Main application logic"""
    initialize_session_state()
    
    if not st.session_state.authenticated:
        login_page()
    elif not st.session_state.test_completed:
        test_page()
    else:
        results_page()

if __name__ == "__main__":
    main()