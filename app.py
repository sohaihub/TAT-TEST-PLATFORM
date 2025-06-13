import streamlit as st
import smtplib
import ssl
import time
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict, Any
import hashlib
import uuid
import google.generativeai as genai
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Configure Gemini API
genai.configure(api_key="AIzaSyDDHNQB3EyoVsmAZi6Gh-aaEyVFl-F7-bI")
model = genai.GenerativeModel('gemini-1.5-flash')

# Email configuration
EMAIL_ADDRESS = "fathimasoha8@gmail.com"
EMAIL_PASSWORD = "rmso vplv yfxj ohga"  # WARNING: Hardcoding credentials is insecure for production
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

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

# Test questions database (100 questions, abbreviated for brevity)
TEST_QUESTIONS = [
    {
        "id": 1,
        "question": "What is the primary purpose of the TAT Resume Analyzer?",
        "options": [
            "Generates job descriptions",
            "Manages candidate email notifications",
            "Scores resumes based on industry standards",
            "Conducts AI-based interviews"
        ],
        "correct_answer": 2,
        "explanation": "The Resume Analyzer scores resumes based on adherence to industry standards, with non-standard resumes receiving lower scores (Hyrdragon.pdf, Page 1)."
    },
    {
        "id": 2,
        "question": "Which Smart Proctoring feature detects noise during assessments?",
        "options": [
            "Audio detection",
            "Eyeball tracking",
            "Tab switching deactivation",
            "Multi person detection"
        ],
        "correct_answer": 0,
        "explanation": "Audio detection is a Smart Proctoring feature that identifies noise during assessments (Hyrdragon.pdf, Page 1)."
    },
    {
        "id": 3,
        "question": "What does the Matchmaker feature in TAT provide?",
        "options": [
            "Automated question generation",
            "Real-time coding feedback",
            "Candidate video interview scheduling",
            "Suitability score for resumes against job descriptions"
        ],
        "correct_answer": 3,
        "explanation": "The Matchmaker compares job descriptions with resumes and provides a suitability score (Hyrdragon.pdf, Page 1)."
    },
    {
        "id": 4,
        "question": "How many types of assessments are included in TAT's Skill Testing?",
        "options": [
            "6",
            "5",
            "3",
            "4"
        ],
        "correct_answer": 1,
        "explanation": "Skill Testing includes 5 types of assessments: MCQ, technical code, syntax-based code, video conferencing, and others (Hyrdragon.pdf, Page 1)."
    },
    {
        "id": 5,
        "question": "What does the AI-Powered Assessment Feedback provide?",
        "options": [
            "Proctoring alerts",
            "Job role creation",
            "Resume formatting",
            "Detailed candidate performance metrics"
        ],
        "correct_answer": 3,
        "explanation": "AI-Powered Assessment Feedback offers detailed feedback on candidate performance with metrics and scores (Hyrdragon.pdf, Page 1)."
    },
    {
        "id": 6,
        "question": "Which Smart Proctoring feature prevents candidates from leaving the test window?",
        "options": [
            "Face mismatch detection",
            "Deactivate tab switching and Esc option",
            "Multi person detection",
            "Audio detection"
        ],
        "correct_answer": 1,
        "explanation": "Smart Proctoring deactivates tab switching and the Esc option to prevent cheating (Hyrdragon.pdf, Page 1)."
    },
    {
        "id": 7,
        "question": "What inputs are used for Automated Question Generation in TAT?",
        "options": [
            "Topics, number of questions, and difficulty levels",
            "Candidate emails",
            "Resume scores",
            "Job salary ranges"
        ],
        "correct_answer": 0,
        "explanation": "Automated Question Generation uses inputs like topics, number of questions, and difficulty levels (Hyrdragon.pdf, Page 2)."
    },
    {
        "id": 8,
        "question": "What is the role of the AI bot in AI-Supported Video Interviewing?",
        "options": [
            "Manages candidate invitations",
            "Scores resumes",
            "Conducts interviews when needed",
            "Generates job descriptions"
        ],
        "correct_answer": 2,
        "explanation": "The AI bot can conduct interviews during AI-Supported Video Interviewing when needed (Hyrdragon.pdf, Page 2)."
    },
    {
        "id": 9,
        "question": "What does the Dynamic MCQs feature ensure?",
        "options": [
            "No time limits for questions",
            "Shuffled questions for each candidate",
            "Fixed questions for all candidates",
            "Manual question input only"
        ],
        "correct_answer": 1,
        "explanation": "Dynamic MCQs shuffle multiple-choice questions for each candidate (Hyrdragon.pdf, Page 2)."
    },
    {
        "id": 10,
        "question": "What can recruiters do with Customizable Assessment Options?",
        "options": [
            "Set candidate salaries",
            "Disable proctoring",
            "Upload candidate resumes",
            "Manually input assessment questions"
        ],
        "correct_answer": 3,
        "explanation": "Customizable Assessment Options allow recruiters to manually input questions for assessments (Hyrdragon.pdf, Page 2)."
    },
    {
        "id": 11,
        "question": "What login option is available on the TAT recruiter login page?",
        "options": [
            "Gmail login",
            "LinkedIn login",
            "Facebook login",
            "Twitter login"
        ],
        "correct_answer": 0,
        "explanation": "The recruiter login page supports Gmail login in addition to email and password (Hyrdragon.pdf, Page 2)."
    },
    {
        "id": 12,
        "question": "Which insight is available on the TAT recruiter dashboard?",
        "options": [
            "Proctoring violation logs",
            "Email insights (sent, responded, unread)",
            "Candidate social media profiles",
            "Job market trends"
        ],
        "correct_answer": 1,
        "explanation": "The dashboard provides email insights like sent, responded, and unread statuses (Hyrdragon.pdf, Page 2)."
    },
    {
        "id": 13,
        "question": "What is displayed in the TAT recruiter sidebar?",
        "options": [
            "Proctoring settings",
            "Candidate resumes",
            "Jobs and insights",
            "AI question templates"
        ],
        "correct_answer": 2,
        "explanation": "The sidebar displays jobs (active, inactive, draft, archive) and insights like resume score and email status (Hyrdragon.pdf, Page 2)."
    },
    {
        "id": 14,
        "question": "What can recruiters view in the notifications section of the TAT dashboard?",
        "options": [
            "Candidate salary expectations",
            "Weekly activity and test completions",
            "Job description templates",
            "Proctoring violation alerts"
        ],
        "correct_answer": 1,
        "explanation": "Notifications show weekly activity and test completion or candidate information (Hyrdragon.pdf, Page 2)."
    },
    {
        "id": 15,
        "question": "Which stage is NOT part of the TAT candidate journey status?",
        "options": [
            "Onboarded",
            "Applications",
            "Screened",
            "Shortlisted"
        ],
        "correct_answer": 0,
        "explanation": "The candidate journey includes Applications, Screened, Test completed, and Shortlisted, but not Onboarded (Hyrdragon.pdf, Page 2)."
    },
    {
        "id": 16,
        "question": "What is included in the TAT applicants distribution status?",
        "options": [
            "Candidate locations and salaries",
            "Total applicants, Yet to respond, Responded, Shortlisted",
            "Proctoring violation counts",
            "Resume scores only"
        ],
        "correct_answer": 1,
        "explanation": "Applicants distribution status includes Total applicants, Yet to respond, Responded, and Shortlisted (Hyrdragon.pdf, Page 2)."
    },
    {
        "id": 17,
        "question": "What does the TAT test performance distribution display?",
        "options": [
            "Assessment data (e.g., 70% score viewed)",
            "Candidate email responses",
            "Job salary ranges",
            "Proctoring settings"
        ],
        "correct_answer": 0,
        "explanation": "Test performance distribution shows assessment data, such as 70% score viewed (Hyrdragon.pdf, Page 2)."
    },
    {
        "id": 18,
        "question": "What is required to create a job in TAT?",
        "options": [
            "Job role, location, salary, and job description",
            "Candidate resumes",
            "Proctoring thresholds",
            "AI-generated questions"
        ],
        "correct_answer": 0,
        "explanation": "Creating a job requires uploading details like job role, location, salary, and job description (Hyrdragon.pdf, Page 3)."
    },
    {
        "id": 19,
        "question": "How many assessment rounds are currently live in TAT?",
        "options": [
            "5",
            "3",
            "4",
            "6"
        ],
        "correct_answer": 2,
        "explanation": "Four rounds are live (MCQ, Full Stack Developer, Syntax Based Programming, VC), with AI Bot Interview launching soon (Hyrdragon.pdf, Page 3)."
    },
    {
        "id": 20,
        "question": "Which round type is listed as 'coming soon' in TAT?",
        "options": [
            "Video Conferencing",
            "MCQ",
            "Full Stack Developer",
            "AI Bot Interview"
        ],
        "correct_answer": 3,
        "explanation": "The AI Bot Interview round is listed as 'coming soon' (Hyrdragon.pdf, Page 3)."
    },
    {
        "id": 21,
        "question": "What option is available for MCQ question selection in TAT?",
        "options": [
            "Proctoring-based selection",
            "AI generator only",
            "Manual only",
            "AI generator, manual, and question bank"
        ],
        "correct_answer": 3,
        "explanation": "MCQ questions can be selected via AI generator, manual input, or question bank options (Hyrdragon.pdf, Page 3)."
    },
    {
        "id": 22,
        "question": "What does the Full Stack Developer round in TAT involve?",
        "options": [
            "Video interviews",
            "Resume scoring",
            "Technical coding with development tasks",
            "Proctoring configuration"
        ],
        "correct_answer": 2,
        "explanation": "The Full Stack Developer round involves technical coding with development tasks and problem statements (Hyrdragon.pdf, Page 3)."
    },
    {
        "id": 23,
        "question": "What is the focus of the Syntax Based Programming round in TAT?",
        "options": [
            "AI question generation",
            "Test case-based coding programs",
            "Resume analysis",
            "HR interviews"
        ],
        "correct_answer": 1,
        "explanation": "Syntax Based Programming involves test case-based coding programs (Hyrdragon.pdf, Page 3)."
    },
    {
        "id": 24,
        "question": "What is the purpose of the Video Conferencing (VC) round in TAT?",
        "options": [
            "Proctoring setup",
            "Technical coding",
            "HR or Management interviews",
            "Resume scoring"
        ],
        "correct_answer": 2,
        "explanation": "The VC round is used for HR or Management interviews (Hyrdragon.pdf, Page 3)."
    },
    {
        "id": 25,
        "question": "Which configuration model is NOT part of TAT job setup?",
        "options": [
            "Smart Proctoring",
            "Candidate Salary Negotiation",
            "Shortlisting Option",
            "Activation Date and Time"
        ],
        "correct_answer": 1,
        "explanation": "Job setup includes Smart Proctoring, Shortlisting Option, Activation Date and Time, and Deadline, but not Salary Negotiation (Hyrdragon.pdf, Page 3)."
    },
    {
        "id": 26,
        "question": "What does the Smart Proctoring anti-cheating toggle allow?",
        "options": [
            "Enabling/disabling proctoring",
            "Disabling all proctoring features",
            "Setting question difficulty",
            "Uploading candidate resumes"
        ],
        "correct_answer": 0,
        "explanation": "The anti-cheating toggle allows enabling or disabling Smart Proctoring features (Hyrdragon.pdf, Page 3)."
    },
    {
        "id": 27,
        "question": "What is the purpose of the Shortlisting Option in TAT?",
        "options": [
            "Resume formatting",
            "Generating questions",
            "Manual or automated threshold-based shortlisting",
            "Proctoring alerts"
        ],
        "correct_answer": 2,
        "explanation": "The Shortlisting Option supports manual or automated threshold-based shortlisting, e.g., 70% (Hyrdragon.pdf, Page 3)."
    },
    {
        "id": 28,
        "question": "What is an example of a topic selectable for TAT assessments?",
        "options": [
            "Email drafting",
            "Salary negotiation",
            "Python",
            "Job location"
        ],
        "correct_answer": 2,
        "explanation": "Topics like Python, PHP, C++, and Azure can be selected for assessments (Hyrdragon.pdf, Page 3)."
    },
    {
        "id": 29,
        "question": "What is the maximum file size for CSV uploads in TAT?",
        "options": [
            "10MB",
            "2MB",
            "5MB",
            "3MB"
        ],
        "correct_answer": 2,
        "explanation": "The maximum file size for CSV uploads is 5MB, supporting up to 1200 applicants (Hyrdragon.pdf, Page 4)."
    },
    {
        "id": 30,
        "question": "How many applicants can a 5MB CSV upload support in TAT?",
        "options": [
            "1500",
            "500",
            "1200",
            "1000"
        ],
        "correct_answer": 2,
        "explanation": "A 5MB CSV upload can support up to 1200 applicants (Hyrdragon.pdf, Page 4)."
    },
    {
        "id": 31,
        "question": "What file formats are supported for resume uploads in TAT?",
        "options": [
            "DOC only",
            "PDF, DOC, DOCX",
            "PDF only",
            "TXT, PDF, DOC"
        ],
        "correct_answer": 1,
        "explanation": "Resume uploads support PDF, DOC, and DOCX formats (Hyrdragon.pdf, Page 4)."
    },
    {
        "id": 32,
        "question": "What is the maximum file size for resume uploads in TAT?",
        "options": [
            "2MB",
            "5MB",
            "3MB",
            "10MB"
        ],
        "correct_answer": 2,
        "explanation": "The maximum file size for resume uploads is 3MB, supporting up to 1000 files (Hyrdragon.pdf, Page 4)."
    },
    {
        "id": 33,
        "question": "What is analyzed during resume uploads in TAT?",
        "options": [
            "Job descriptions",
            "AI analyzer and Matchmaker scores",
            "Candidate emails",
            "Proctoring settings"
        ],
        "correct_answer": 1,
        "explanation": "Resume uploads are processed by the AI analyzer and Matchmaker, with scores viewed (Hyrdragon.pdf, Page 4)."
    },
    {
        "id": 34,
        "question": "What details are included in the TAT application form configuration?",
        "options": [
            "Only resume upload",
            "Name, email, location, experience, etc.",
            "Only email and name",
            "Only job description"
        ],
        "correct_answer": 1,
        "explanation": "The application form includes name, email, location, current job, position, company, experience, etc. (Hyrdragon.pdf, Page 4)."
    },
    {
        "id": 35,
        "question": "What happens after a candidate submits an application form in TAT?",
        "options": [
            "Recruiter review with 'We will review and get back' message",
            "Immediate shortlisting",
            "Automatic test assignment",
            "Resume deletion"
        ],
        "correct_answer": 0,
        "explanation": "After submission, candidates see 'We will review and get back to you soon,' and recruiters review the form (Hyrdragon.pdf, Page 4)."
    },
    {
        "id": 36,
        "question": "Where do candidate test results appear in TAT?",
        "options": [
            "Email notifications only",
            "Recruiter dashboard",
            "Candidate login page",
            "Job description page"
        ],
        "correct_answer": 1,
        "explanation": "Test results appear on the recruiter dashboard after candidate completion (Hyrdragon.pdf, Page 4)."
    },
    {
        "id": 37,
        "question": "What metrics are included in TAT’s AI feedback for assessments?",
        "options": [
            "Accuracy, time management, difficulty level, knowledge diversity",
            "Salary expectations",
            "Job location preferences",
            "Resume formatting"
        ],
        "correct_answer": 0,
        "explanation": "AI feedback includes metrics like accuracy, time management, difficulty level performance, and knowledge diversity (Hyrdragon.pdf, Page 4)."
    },
    {
        "id": 38,
        "question": "What decision options are available to recruiters after reviewing TAT results?",
        "options": [
            "Hired, Fired, Pending",
            "Selected, Waiting, Rejected",
            "Approved, Denied, Archived",
            "Shortlisted, Ignored, Deleted"
        ],
        "correct_answer": 1,
        "explanation": "Recruiters can mark candidates as Selected, Waiting, or Rejected based on results (Hyrdragon.pdf, Page 4)."
    },
    {
        "id": 39,
        "question": "When is an email sent to candidates in TAT based on results?",
        "options": [
            "For all candidates automatically",
            "For rejected candidates with manual send option",
            "Only for shortlisted candidates",
            "Never sent"
        ],
        "correct_answer": 1,
        "explanation": "Emails are sent for rejected candidates with a manual send checkbox, but not for waiting or shortlisted (Hyrdragon.pdf, Page 4)."
    },
    {
        "id": 40,
        "question": "What appears on the TAT report page?",
        "options": [
            "Attended candidate list and updated status",
            "Job descriptions",
            "Proctoring violation logs",
            "Resume templates"
        ],
        "correct_answer": 0,
        "explanation": "The report page shows the attended candidate list and updated status (Hyrdragon.pdf, Page 4)."
    },
    {
        "id": 41,
        "question": "What is required for a candidate to sign up in TAT?",
        "options": [
            "Name, mobile number, resume upload for Gmail login",
            "Job description",
            "Proctoring settings",
            "Salary details"
        ],
        "correct_answer": 0,
        "explanation": "For Gmail login, candidates must provide name, mobile number, and resume upload (Hyrdragon.pdf, Page 5)."
    },
    {
        "id": 42,
        "question": "What does the TAT assessment guideline screen display?",
        "options": [
            "Job salary details",
            "Timelines, proctoring, and marking information",
            "Resume scores",
            "Candidate emails"
        ],
        "correct_answer": 1,
        "explanation": "The assessment guideline screen shows timelines, proctoring information, and marking details (Hyrdragon.pdf, Page 5)."
    },
    {
        "id": 43,
        "question": "What action starts a TAT assessment for candidates?",
        "options": [
            "Uploading a resume",
            "Selecting a job role",
            "Typing 'START'",
            "Setting proctoring options"
        ],
        "correct_answer": 2,
        "explanation": "Candidates type 'START' to begin the test (Hyrdragon.pdf, Page 5)."
    },
    {
        "id": 44,
        "question": "What appears on the screen during a TAT assessment for violation purposes?",
        "options": [
            "Resume score",
            "Gmail watermark",
            "Job description",
            "Proctoring settings"
        ],
        "correct_answer": 1,
        "explanation": "A Gmail watermark appears on the screen for violation purposes (Hyrdragon.pdf, Page 5)."
    },
    {
        "id": 45,
        "question": "What permissions must candidates grant during a TAT assessment?",
        "options": [
            "Email access",
            "Job description editing",
            "Camera, photo capture, and microphone access",
            "Resume deletion"
        ],
        "correct_answer": 2,
        "explanation": "Candidates must allow camera access, photo capture, and microphone access (Hyrdragon.pdf, Page 5)."
    },
    {
        "id": 46,
        "question": "When does TAT’s Smart Proctoring start during an assessment?",
        "options": [
            "After resume upload",
            "After test completion",
            "When the test begins",
            "During job creation"
        ],
        "correct_answer": 2,
        "explanation": "Smart Proctoring starts when the test begins (Hyrdragon.pdf, Page 5)."
    },
    {
        "id": 47,
        "question": "What alerts candidates in the last moments of a TAT assessment?",
        "options": [
            "Resume score update",
            "Beep sound before 5 seconds",
            "Email notification",
            "Proctoring violation alert"
        ],
        "correct_answer": 1,
        "explanation": "A beep sound alerts candidates before 5 seconds of the assessment’s end (Hyrdragon.pdf, Page 5)."
    },
    {
        "id": 48,
        "question": "What can candidates do after completing a TAT assessment?",
        "options": [
            "Set proctoring thresholds",
            "Edit job descriptions",
            "Provide ratings and feedback",
            "Delete their resumes"
        ],
        "correct_answer": 2,
        "explanation": "Candidates can provide ratings and feedback about their experience after completing the assessment (Hyrdragon.pdf, Page 5)."
    },
    {
        "id": 49,
        "question": "How are TAT assessment results communicated to candidates?",
        "options": [
            "Through proctoring logs",
            "Via recruiter email",
            "On the candidate login page",
            "In job descriptions"
        ],
        "correct_answer": 1,
        "explanation": "Assessment results are sent to candidates via email by the recruiter (Hyrdragon.pdf, Page 5)."
    },
    {
        "id": 50,
        "question": "What is the primary goal of TAT for recruiters?",
        "options": [
            "Simplify technical candidate evaluation",
            "Increase hiring costs",
            "Manage employee onboarding",
            "Create job advertisements"
        ],
        "correct_answer": 0,
        "explanation": "TAT simplifies the hiring process by providing accurate, skill-based assessments for technical candidates (Hyrdragon.pdf, Page 1)."
    },
    {
        "id": 51,
        "question": "What feature of the TAT IDE supports coding assessments?",
        "options": [
            "Job description creation",
            "Compiling and debugging code",
            "Resume scoring",
            "Email notifications"
        ],
        "correct_answer": 1,
        "explanation": "The inbuilt IDE supports compiling and debugging code for real-time coding assessments (Hyrdragon.pdf, Page 1)."
    },
    {
        "id": 52,
        "question": "Which Smart Proctoring feature verifies candidate identity?",
        "options": [
            "Tab switching deactivation",
            "Candidate ID verification",
            "Audio detection",
            "Eyeball tracking"
        ],
        "correct_answer": 1,
        "explanation": "Smart Proctoring includes candidate ID verification to ensure identity (Hyrdragon.pdf, Page 1)."
    },
    {
        "id": 53,
        "question": "What does the AI-Supported Video Interviewing feature display?",
        "options": [
            "AI-processed questions",
            "Resume scores",
            "Proctoring alerts",
            "Job salary details"
        ],
        "correct_answer": 0,
        "explanation": "AI-Supported Video Interviewing displays AI-processed questions during interviews (Hyrdragon.pdf, Page 2)."
    },
    {
        "id": 54,
        "question": "What is the maximum number of questions allowed in a TAT coding round?",
        "options": [
            "10",
            "5",
            "15",
            "20"
        ],
        "correct_answer": 1,
        "explanation": "The maximum number of questions for a coding round is 5, as implied by the configuration options (Hyrdragon.pdf, Page 3)."
    },
    {
        "id": 55,
        "question": "What configuration option allows recruiters to set assessment deadlines?",
        "options": [
            "AI Question Generation",
            "Smart Proctoring",
            "Deadline and Expiration Date",
            "Shortlisting Option"
        ],
        "correct_answer": 2,
        "explanation": "Recruiters can set deadlines and expiration dates for assessments (Hyrdragon.pdf, Page 3)."
    },
    {
        "id": 56,
        "question": "What is the purpose of the TAT recruiter profile section?",
        "options": [
            "Proctoring configuration",
            "Photo upload, company description, and about me",
            "Resume analysis",
            "Question generation"
        ],
        "correct_answer": 1,
        "explanation": "The recruiter profile includes photo upload, company description, and about me (Hyrdragon.pdf, Page 2)."
    },
    {
        "id": 57,
        "question": "What does the TAT job sidebar display about job statuses?",
        "options": [
            "Proctoring violations",
            "Active, inactive, draft, and archive",
            "Candidate resumes",
            "Email templates"
        ],
        "correct_answer": 1,
        "explanation": "The job sidebar shows active, inactive, draft, and archive statuses (Hyrdragon.pdf, Page 2)."
    },
    {
        "id": 58,
        "question": "What is the benefit of TAT’s Matchmaker feature for recruiters?",
        "options": [
            "Better alignment of resumes with job requirements",
            "Automated proctoring",
            "Question shuffling",
            "Email tracking"
        ],
        "correct_answer": 0,
        "explanation": "Matchmaker ensures better alignment between job requirements and candidate resumes (Hyrdragon.pdf, Page 1)."
    },
    {
        "id": 59,
        "question": "What is the role of the text editor in TAT job creation?",
        "options": [
            "Proctoring setup",
            "Resume editing",
            "Writing job descriptions",
            "Question generation"
        ],
        "correct_answer": 2,
        "explanation": "A text editor is available for writing job descriptions during job creation (Hyrdragon.pdf, Page 3)."
    },
    {
        "id": 60,
        "question": "What does the TAT Smart Proctoring feature monitor for during assessments?",
        "options": [
            "Job descriptions",
            "Face not focused or mismatch",
            "Resume scores",
            "Email responses"
        ],
        "correct_answer": 1,
        "explanation": "Smart Proctoring monitors for face not focused or mismatch, among other features (Hyrdragon.pdf, Page 3)."
    },
    {
        "id": 61,
        "question": "What is the purpose of the question bank in TAT?",
        "options": [
            "Providing pre-existing questions for assessments",
            "Resume storage",
            "Proctoring configuration",
            "Email tracking"
        ],
        "correct_answer": 0,
        "explanation": "The question bank provides pre-existing questions for assessment creation (Hyrdragon.pdf, Page 3)."
    },
    {
        "id": 62,
        "question": "What does the TAT application form’s mandatory option allow?",
        "options": [
            "Disabling proctoring",
            "Requiring specific fields like name or email",
            "Optional resume uploads",
            "Automatic shortlisting"
        ],
        "correct_answer": 1,
        "explanation": "The mandatory option allows recruiters to require specific fields in the application form (Hyrdragon.pdf, Page 4)."
    },
    {
        "id": 63,
        "question": "What is generated after configuring a TAT application form?",
        "options": [
            "Proctoring report",
            "Resume score",
            "Application link",
            "Job description"
        ],
        "correct_answer": 2,
        "explanation": "A link is generated after the application form is configured (Hyrdragon.pdf, Page 4)."
    },
    {
        "id": 64,
        "question": "What appears on the TAT recruiter dashboard when a candidate completes a test?",
        "options": [
            "Resume template",
            "Notification of test completion",
            "Job description",
            "Proctoring settings"
        ],
        "correct_answer": 1,
        "explanation": "Test completion notifications appear on the recruiter dashboard (Hyrdragon.pdf, Page 4)."
    },
    {
        "id": 65,
        "question": "What score is displayed on the TAT recruiter dashboard after test completion?",
        "options": [
            "Proctoring violation score",
            "Overall and resume score (e.g., 60%)",
            "Job suitability score",
            "Email response score"
        ],
        "correct_answer": 1,
        "explanation": "The overall score and resume score (e.g., 60%) appear on the dashboard (Hyrdragon.pdf, Page 4)."
    },
    {
        "id": 66,
        "question": "What is included in TAT test details viewed by recruiters?",
        "options": [
            "Resume format",
            "Test topics and details",
            "Candidate salary",
            "Job location"
        ],
        "correct_answer": 1,
        "explanation": "Recruiters can view test topics and details after test completion (Hyrdragon.pdf, Page 4)."
    },
    {
        "id": 67,
        "question": "What is the purpose of TAT’s AI feedback metrics?",
        "options": [
            "Resume formatting",
            "Evaluating candidate performance",
            "Job creation",
            "Proctoring alerts"
        ],
        "correct_answer": 1,
        "explanation": "AI feedback metrics evaluate candidate performance in areas like accuracy and time management (Hyrdragon.pdf, Page 4)."
    },
    {
        "id": 68,
        "question": "What is the TAT ranking criteria for candidates with equal marks?",
        "options": [
            "Least time taken ranks higher",
            "Random selection",
            "Resume score",
            "Proctoring compliance"
        ],
        "correct_answer": 0,
        "explanation": "For equal marks, the candidate with the least time taken ranks higher (Hyrdragon.pdf, Page 5)."
    },
    {
        "id": 69,
        "question": "What does the TAT candidate login require for existing users?",
        "options": [
            "Resume deletion",
            "Password",
            "Job description",
            "Proctoring setup"
        ],
        "correct_answer": 1,
        "explanation": "Existing candidates log in with a password (Hyrdragon.pdf, Page 5)."
    },
    {
        "id": 70,
        "question": "What is the role of the TAT resume upload during candidate login?",
        "options": [
            "Email sending",
            "Triggering Resume Analyzer and Matchmaker",
            "Proctoring activation",
            "Job creation"
        ],
        "correct_answer": 1,
        "explanation": "Resume upload during login triggers the Resume Analyzer and Matchmaker (Hyrdragon.pdf, Page 5)."
    },
    {
        "id": 71,
        "question": "What type of questions can appear in the TAT code compiler?",
        "options": [
            "Resume-based questions",
            "Coding questions only",
            "MCQs only",
            "Job description questions"
        ],
        "correct_answer": 1,
        "explanation": "The code compiler supports coding questions during assessments (Hyrdragon.pdf, Page 5)."
    },
    {
        "id": 72,
        "question": "What does TAT’s Smart Proctoring detect besides noise?",
        "options": [
            "Face not focused and multi-person detection",
            "Resume errors",
            "Job description mismatches",
            "Email responses"
        ],
        "correct_answer": 0,
        "explanation": "Smart Proctoring detects face not focused and multi-person presence, among others (Hyrdragon.pdf, Page 5)."
    },
    {
        "id": 73,
        "question": "What is the purpose of the TAT for non-technical recruiters?",
        "options": [
            "Creating marketing campaigns",
            "Evaluating technical candidates",
            "Managing payroll",
            "Scheduling meetings"
        ],
        "correct_answer": 1,
        "explanation": "TAT helps non-technical recruiters evaluate candidates with technical skills (Hyrdragon.pdf, Page 1)."
    },
    {
        "id": 74,
        "question": "What is the TAT dashboard’s education insight distribution?",
        "options": [
            "High school and college",
            "Bachelors and Masters",
            "Certifications only",
            "Job roles"
        ],
        "correct_answer": 1,
        "explanation": "Education insights show distributions for bachelors and masters degrees (Hyrdragon.pdf, Page 2)."
    },
    {
        "id": 75,
        "question": "What is the TAT job creation process’s work type field used for?",
        "options": [
            "Proctoring setup",
            "Resume scoring",
            "Specifying job conditions (e.g., remote, on-site)",
            "Question generation"
        ],
        "correct_answer": 2,
        "explanation": "The work type field specifies job conditions like remote or on-site (Hyrdragon.pdf, Page 3)."
    },
    {
        "id": 76,
        "question": "What is the maximum number of resume files supported by TAT?",
        "options": [
            "1500",
            "1000",
            "500",
            "1200"
        ],
        "correct_answer": 1,
        "explanation": "Resume uploads support up to 1000 files (Hyrdragon.pdf, Page 4)."
    },
    {
        "id": 77,
        "question": "What is the TAT candidate invitation method besides CSV?",
        "options": [
            "Email invite with no limits",
            "Phone calls",
            "Social media posts",
            "In-person invites"
        ],
        "correct_answer": 0,
        "explanation": "Candidates can be invited via email with no limit on the number of invitations (Hyrdragon.pdf, Page 4)."
    },
    {
        "id": 78,
        "question": "What is the TAT recruiter’s action after candidate application review?",
        "options": [
            "Generate new questions",
            "Decide based on candidate information",
            "Delete candidate data",
            "Set proctoring thresholds"
        ],
        "correct_answer": 1,
        "explanation": "Recruiters decide on candidates based on their application information (Hyrdragon.pdf, Page 4)."
    },
    {
        "id": 79,
        "question": "What is the TAT assessment marking information about?",
        "options": [
            "Proctoring violations",
            "Ranking criteria like time taken",
            "Resume scores",
            "Job salaries"
        ],
        "correct_answer": 1,
        "explanation": "Marking information includes ranking criteria, such as least time taken for equal marks (Hyrdragon.pdf, Page 5)."
    },
    {
        "id": 80,
        "question": "What is the TAT’s primary benefit for hiring alignment?",
        "options": [
            "Manual assessments",
            "Better job requirement and candidate capability alignment",
            "Increasing costs",
            "Email management"
        ],
        "correct_answer": 1,
        "explanation": "TAT ensures better alignment between job requirements and candidate capabilities (Hyrdragon.pdf, Page 1)."
    },
    {
        "id": 81,
        "question": "What does the TAT Smart Proctoring’s face mismatch detect?",
        "options": [
            "Email issues",
            "Unauthorized candidates",
            "Incorrect resumes",
            "Job description errors"
        ],
        "correct_answer": 1,
        "explanation": "Face mismatch detection identifies unauthorized candidates during assessments (Hyrdragon.pdf, Page 3)."
    },
    {
        "id": 82,
        "question": "What is the TAT recruiter dashboard’s experience distribution insight?",
        "options": [
            "Proctoring violations",
            "Years of experience",
            "Candidate locations",
            "Job roles"
        ],
        "correct_answer": 1,
        "explanation": "Experience distribution shows years of candidate experience (Hyrdragon.pdf, Page 2)."
    },
    {
        "id": 83,
        "question": "What is the TAT job creation’s years of experience field used for?",
        "options": [
            "Resume generation",
            "Specifying required experience",
            "Proctoring setup",
            "Email tracking"
        ],
        "correct_answer": 1,
        "explanation": "The years of experience field specifies the required experience for the job role (Hyrdragon.pdf, Page 3)."
    },
    {
        "id": 84,
        "question": "What is the TAT’s automated shortlisting threshold customizable to?",
        "options": [
            "Resume score only",
            "Custom percentage (e.g., 70%)",
            "Fixed 50%",
            "Proctoring duration"
        ],
        "correct_answer": 1,
        "explanation": "The automated shortlisting threshold can be customized (e.g., 70%) (Hyrdragon.pdf, Page 3)."
    },
    {
        "id": 85,
        "question": "What is the TAT candidate’s action to submit an application?",
        "options": [
            "Create job description",
            "Fill details and submit",
            "Set proctoring",
            "Delete resume"
        ],
        "correct_answer": 1,
        "explanation": "Candidates fill in details and submit the application form (Hyrdragon.pdf, Page 4)."
    },
    {
        "id": 86,
        "question": "What is the TAT recruiter’s view of recent jobs on the dashboard?",
        "options": [
            "Visible and clickable to view details",
            "Hidden until published",
            "Only archived jobs",
            "Proctoring logs"
        ],
        "correct_answer": 0,
        "explanation": "Recent jobs are visible and available on the dashboard for recruiters to view (Hyrdragon.pdf, Page 2)."
    },
    {
        "id": 87,
        "question": "What is the purpose of the TAT Skill Testing feature?",
        "options": [
            "Job description creation",
            "Assessing various candidate skills",
            "Email management",
            "Resume scoring"
        ],
        "correct_answer": 1,
        "explanation": "Skill Testing assesses various candidate skills through MCQs, coding, and video conferencing (Hyrdragon.pdf, Page 1)."
    },
    {
        "id": 88,
        "question": "What does the TAT recruiter dashboard display about ongoing jobs?",
        "options": [
            "Proctoring settings",
            "Total applicants and status",
            "Resume templates",
            "Job market trends"
        ],
        "correct_answer": 1,
        "explanation": "The dashboard shows total applicants and ongoing job statuses (Hyrdragon.pdf, Page 2)."
    },
    {
        "id": 89,
        "question": "What is the TAT’s Smart Proctoring threshold used for?",
        "options": [
            "Resume scoring",
            "Automated shortlisting",
            "Question generation",
            "Email tracking"
        ],
        "correct_answer": 1,
        "explanation": "The Smart Proctoring threshold supports automated shortlisting (Hyrdragon.pdf, Page 1)."
    },
    {
        "id": 90,
        "question": "What is the TAT’s AI-Powered Assessment Feedback focused on?",
        "options": [
            "Proctoring violations",
            "Candidate performance metrics",
            "Job creation",
            "Resume formatting"
        ],
        "correct_answer": 1,
        "explanation": "AI-Powered Assessment Feedback provides detailed candidate performance metrics (Hyrdragon.pdf, Page 1)."
    },
    {
        "id": 91,
        "question": "What is the TAT’s Dynamic MCQs timeframe feature?",
        "options": [
            "Fixed questions for all",
            "Different question sets within a timeframe",
            "No time limits",
            "Manual question input"
        ],
        "correct_answer": 1,
        "explanation": "Dynamic MCQs provide different sets of questions within a set timeframe (Hyrdragon.pdf, Page 2)."
    },
    {
        "id": 92,
        "question": "What is the TAT recruiter login page’s create account option?",
        "options": [
            "Social media only",
            "Email and password",
            "Proctoring setup",
            "Resume upload"
        ],
        "correct_answer": 1,
        "explanation": "The login page allows account creation with email and password (Hyrdragon.pdf, Page 2)."
    },
    {
        "id": 93,
        "question": "What does the TAT recruiter dashboard’s resume score insight show?",
        "options": [
            "Proctoring violations",
            "Resume adherence to standards",
            "Job salary ranges",
            "Email responses"
        ],
        "correct_answer": 1,
        "explanation": "The resume score insight shows adherence to industry standards (Hyrdragon.pdf, Page 2)."
    },
    {
        "id": 94,
        "question": "What is the TAT job creation’s location field used for?",
        "options": [
            "Proctoring setup",
            "Specifying job location",
            "Resume scoring",
            "Question generation"
        ],
        "correct_answer": 1,
        "explanation": "The location field specifies the job’s location (Hyrdragon.pdf, Page 3)."
    },
    {
        "id": 95,
        "question": "What is the TAT’s question type configuration for assessments?",
        "options": [
            "Resume-based only",
            "Easy, Medium, Hard with number and duration",
            "Proctoring thresholds",
            "Email templates"
        ],
        "correct_answer": 1,
        "explanation": "Question types are configured as Easy, Medium, or Hard with number and duration (Hyrdragon.pdf, Page 3)."
    },
    {
        "id": 96,
        "question": "What is the TAT’s candidate application form review process?",
        "options": [
            "Automatic deletion",
            "Recruiter decision based on information",
            "Proctoring activation",
            "Question generation"
        ],
        "correct_answer": 1,
        "explanation": "Recruiters review and decide based on candidate application information (Hyrdragon.pdf, Page 4)."
    },
    {
        "id": 97,
        "question": "What is the TAT’s test completion notification process?",
        "options": [
            "Email to candidates only",
            "Displayed on recruiter dashboard",
            "Proctoring log update",
            "Resume deletion"
        ],
        "correct_answer": 1,
        "explanation": "Test completion notifications appear on the recruiter dashboard (Hyrdragon.pdf, Page 4)."
    },
    {
        "id": 98,
        "question": "What is the TAT’s assessment guideline’s marking detail?",
        "options": [
            "Proctoring violations",
            "Least time taken for equal marks",
            "Resume scores",
            "Job salaries"
        ],
        "correct_answer": 1,
        "explanation": "Marking details include least time taken for equal marks ranking (Hyrdragon.pdf, Page 5)."
    },
    {
        "id": 99,
        "question": "What is the TAT’s candidate feedback process after assessment?",
        "options": [
            "Proctoring setup",
            "Ratings and feedback submission",
            "Resume deletion",
            "Job creation"
        ],
        "correct_answer": 1,
        "explanation": "Candidates can submit ratings and feedback after completing assessments (Hyrdragon.pdf, Page 5)."
    },
    {
        "id": 100,
        "question": "What is the TAT’s Smart Proctoring’s multi-person detection for?",
        "options": [
            "Resume scoring",
            "Detecting unauthorized individuals",
            "Email tracking",
            "Question generation"
        ],
        "correct_answer": 1,
        "explanation": "Multi-person detection identifies unauthorized individuals during assessments (Hyrdragon.pdf, Page 1)."
    }
]

    # ... (remaining 99 questions omitted for brevity, same as previous code)

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
    if "ai_feedback" not in st.session_state:
        st.session_state.ai_feedback = {"candidate": "", "evaluator": ""}
    if "receiver_email" not in st.session_state:
        st.session_state.receiver_email = ""

def send_email(recipient_email: str, subject: str, body: str) -> bool:
    """Send email notification using hardcoded credentials"""
    logger.debug(f"Attempting to send email to {recipient_email}")
    try:
        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = EMAIL_ADDRESS
        message["To"] = recipient_email
        
        html_part = MIMEText(body, "html")
        message.attach(html_part)
        
        context = ssl.create_default_context()
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            logger.debug(f"Connecting to SMTP server {SMTP_SERVER}:{SMTP_PORT}")
            server.starttls(context=context)
            logger.debug("Initiating TLS connection")
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            logger.debug("SMTP login successful")
            server.sendmail(EMAIL_ADDRESS, recipient_email, message.as_string())
            logger.debug("Email sent successfully")
        return True
    except smtplib.SMTPAuthenticationError as auth_err:
        logger.error(f"SMTP Authentication Error: {str(auth_err)}")
        st.error(f"Failed to send email: Authentication error. Please verify the email address and app password.")
        return False
    except smtplib.SMTPException as smtp_err:
        logger.error(f"SMTP Error: {str(smtp_err)}")
        st.error(f"Failed to send email: SMTP error - {str(smtp_err)}")
        return False
    except Exception as e:
        logger.error(f"General Error sending email: {str(e)}")
        st.error(f"Failed to send email: {str(e)}")
        return False

def authenticate_user(email: str, password: str) -> bool:
    """Simple authentication using email and password"""
    if email and "@" in email and len(password) >= 6:
        return True
    return False

def generate_ai_feedback(answers: Dict[int, int], detailed_results: List[Dict[str, Any]]) -> tuple:
    """Generate AI-based feedback using Gemini API"""
    incorrect_questions = [
        f"Question {result['question']}: Answered '{result['user_answer']}', Correct: '{result['correct_answer']}'"
        for result in detailed_results if not result["is_correct"]
    ]
    
    candidate_prompt = f"""
    You are an AI-powered assessment tool providing feedback for a candidate who completed a 100-question MCQ test on the Technical Assessment Tool (TAT) system. The candidate's score is {st.session_state.score_percentage:.1f}%. Below are the questions they answered incorrectly:

    {', '.join(incorrect_questions) if incorrect_questions else 'None'}

    Provide detailed feedback (200-300 words) including:
    - Overall performance assessment
    - Strengths demonstrated
    - Areas for improvement based on incorrect answers
    - Specific recommendations for skill enhancement
    """
    
    evaluator_prompt = f"""
    You are an AI-powered assessment tool providing a report for a recruiter evaluating a candidate's performance on a 100-question MCQ test for the Technical Assessment Tool (TAT) system. The candidate's score is {st.session_state.score_percentage:.1f}%. Below are the questions answered incorrectly:

    {', '.join(incorrect_questions) if incorrect_questions else 'None'}

    Provide a concise report (150-200 words) including:
    - Summary of candidate performance
    - Key metrics (accuracy, knowledge diversity)
    - Suitability for technical roles based on test performance
    - Recommendations for next steps in the hiring process
    """
    
    try:
        candidate_response = model.generate_content(candidate_prompt)
        evaluator_response = model.generate_content(evaluator_prompt)
        return candidate_response.text, evaluator_response.text
    except Exception as e:
        logger.error(f"Error generating AI feedback: {str(e)}")
        return (
            f"Error generating candidate feedback: {str(e)}",
            f"Error generating evaluator feedback: {str(e)}"
        )

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
    st.session_state.score_percentage = score_percentage
    return score_percentage, correct_count, total_questions, detailed_results

def generate_and_send_report(answers: Dict[int, int], receiver_email: str):
    """Generate report and send it to the manager"""
    logger.debug(f"Generating and sending report to {receiver_email}")
    score_percentage, correct_count, total_questions, detailed_results = calculate_score(answers)
    
    # Generate AI feedback
    candidate_feedback, evaluator_feedback = generate_ai_feedback(answers, detailed_results)
    st.session_state.ai_feedback["candidate"] = candidate_feedback
    st.session_state.ai_feedback["evaluator"] = evaluator_feedback
    
    # Calculate test duration
    test_duration = st.session_state.end_time - st.session_state.start_time
    duration_minutes = int(test_duration.total_seconds() // 60)
    duration_seconds = int(test_duration.total_seconds() % 60)
    
    # Generate email body
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
            
            <h2>AI-Powered Evaluator Feedback</h2>
            <p>{st.session_state.ai_feedback["evaluator"]}</p>
            
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
    with st.spinner("Sending report to manager..."):
        if send_email(receiver_email, email_subject, email_body):
            st.success(f"✅ Report sent successfully to {receiver_email}")
            logger.debug(f"Report successfully sent to {receiver_email}")
        else:
            st.error(f"❌ Failed to send report to {receiver_email}. Please check logs or try again.")
            logger.error(f"Failed to send report to {receiver_email}")

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
                receiver_email = st.text_input("📨 Manager Email", placeholder="Email to send results (Manager/Recruiter)")
                
                st.markdown("---")
                st.markdown("**📋 Test Information:**")
                st.info("""
                • **Duration:** 60 minutes
                • **Questions:** 100 MCQs
                • **Topics:** TAT System Features, Roadmap, Tech Stack
                • **Passing Score:** 70%
                """)
                
                submitted = st.form_submit_button("🚀 Start Test", type="primary", use_container_width=True)
                
                if submitted:
                    if not all([name, email, password, receiver_email]):
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
    if not st.session_state.test_started:
        st.session_state.test_started = True
        st.session_state.start_time = datetime.now()
        logger.debug("Test started")
    
    if st.session_state.start_time:
        elapsed_time = (datetime.now() - st.session_state.start_time).total_seconds()
        st.session_state.time_remaining = max(0, 3600 - int(elapsed_time))
        
        if st.session_state.time_remaining <= 0:
            st.session_state.test_completed = True
            st.session_state.end_time = datetime.now()
            logger.debug("Test timed out, generating report")
            generate_and_send_report(st.session_state.answers, st.session_state.receiver_email)
            st.rerun()
    
    st.markdown(f"""
    <div class="timer-display">
        ⏰ {format_time(st.session_state.time_remaining)}
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown(f"""
    <div class="main-header">
        <h1>📝 TAT Technical Assessment</h1>
        <p>Welcome, {st.session_state.user_name}</p>
    </div>
    """, unsafe_allow_html=True)
    
    progress = (st.session_state.current_question) / len(TEST_QUESTIONS)
    st.progress(progress, text=f"Question {st.session_state.current_question + 1} of {len(TEST_QUESTIONS)}")
    
    if st.session_state.current_question < len(TEST_QUESTIONS):
        question = TEST_QUESTIONS[st.session_state.current_question]
        
        st.markdown('<div class="test-container">', unsafe_allow_html=True)
        st.markdown(f'<div class="question-card">', unsafe_allow_html=True)
        
        st.markdown(f"### Question {question['id']}")
        st.markdown(f"**{question['question']}**")
        st.markdown('</div>', unsafe_allow_html=True)
        
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
                    logger.debug("Test submitted, generating report")
                    generate_and_send_report(st.session_state.answers, st.session_state.receiver_email)
                    st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown("### 📋 Question Navigation")
        cols = st.columns(10)
        for i, q in enumerate(TEST_QUESTIONS):
            if i % 10 == 0 and i > 0:
                cols = st.columns(10)
            with cols[i % 10]:
                status = "✅" if q["id"] in st.session_state.answers else "⭕"
                if st.button(f"{status} {i+1}", key=f"nav_{i}"):
                    if st.session_state.current_question < len(TEST_QUESTIONS):
                        current_q = TEST_QUESTIONS[st.session_state.current_question]
                        if f"q_{current_q['id']}" in st.session_state:
                            st.session_state.answers[current_q["id"]] = st.session_state[f"q_{current_q['id']}"]
                    st.session_state.current_question = i
                    st.rerun()

def results_page():
    """Display results page"""
    score_percentage, correct_count, total_questions, detailed_results = calculate_score(st.session_state.answers)
    
    # Generate AI feedback if not already done
    if not st.session_state.ai_feedback["candidate"]:
        candidate_feedback, evaluator_feedback = generate_ai_feedback(st.session_state.answers, detailed_results)
        st.session_state.ai_feedback["candidate"] = candidate_feedback
        st.session_state.ai_feedback["evaluator"] = evaluator_feedback
    
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
    
    # AI Feedback for candidate
    st.markdown("### 🤖 AI-Powered Feedback")
    st.markdown(st.session_state.ai_feedback["candidate"])
    
    # Detailed results
    with st.expander("📊 Detailed Results", expanded=False):
        for i, result in enumerate(detailed_results, 1):
            status = "✅" if result["is_correct"] else "❌"
            st.markdown(f"**{i}. {result['question']}**")
            st.markdown(f"Your Answer: {result['user_answer']} {status}")
            if not result["is_correct"]:
                st.markdown(f"Correct Answer: {result['correct_answer']}")
                st.info(f"💡 {result['explanation']}")
            st.markdown("---")
    
    st.markdown("---")
    if st.button("🔄 Take Another Test", type="secondary"):
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
