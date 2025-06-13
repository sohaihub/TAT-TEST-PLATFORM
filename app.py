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
        "question": "What is the primary function of the TAT Resume Analyzer?",
        "options": [
            "Conducts video interviews",
            "Scores resumes based on industry standards",
            "Generates job descriptions",
            "Manages candidate databases"
        ],
        "correct_answer": 1,
        "explanation": "The Resume Analyzer analyzes resumes against industry standards and scores them based on adherence, with non-standard resumes receiving lower scores (Hyrdragon.pdf, Page 1)."
    },
    {
        "id": 2,
        "question": "Which feature of TAT's Smart Proctoring detects unauthorized individuals during assessments?",
        "options": [
            "Audio detection",
            "Eyeball tracking",
            "Multi person & object detection",
            "Tab switching deactivation"
        ],
        "correct_answer": 2,
        "explanation": "Multi person & object detection is a Smart Proctoring feature that identifies unauthorized individuals or objects during assessments (Hyrdragon.pdf, Page 1)."
    },
    {
        "id": 3,
        "question": "What is the timeline for Sprint 3 in the TAT MVP development?",
        "options": [
            "Sep 1 - Sep 14",
            "Sep 15 - Sep 28",
            "Sep 29 - Oct 12",
            "Oct 13 - Nov 9"
        ],
        "correct_answer": 2,
        "explanation": "Sprint 3, focused on developing and integrating the Question Generator, is scheduled from Sep 29 - Oct 12 (PRD TAT.ai, Page 12)."
    },
    {
        "id": 4,
        "question": "Which backend language is primarily used in the TAT tech stack?",
        "options": [
            "Java",
            "Python",
            "Ruby",
            "PHP"
        ],
        "correct_answer": 1,
        "explanation": "Python is the primary backend language for TAT, used with frameworks like Django or Flask (PRD TAT.ai, Page 9)."
    },
    {
        "id": 5,
        "question": "What is the purpose of the Matchmaker feature in TAT?",
        "options": [
            "Generates assessment questions",
            "Compares job descriptions with resumes",
            "Conducts AI-supported video interviews",
            "Provides real-time feedback"
        ],
        "correct_answer": 1,
        "explanation": "The Matchmaker compares job descriptions with resumes and provides a suitability score (Hyrdragon.pdf, Page 1)."
    },
    {
        "id": 6,
        "question": "Which NLP library is explicitly mentioned for TAT's NLP tasks?",
        "options": [
            "NLTK",
            "Gensim",
            "TextBlob",
            "CoreNLP"
        ],
        "correct_answer": 0,
        "explanation": "SpaCy and NLTK are mentioned for NLP tasks in the TAT tech stack (PRD TAT.ai, Page 10)."
    },
    {
        "id": 7,
        "question": "What is the file size limit for CSV uploads when inviting candidates?",
        "options": [
            "2MB",
            "3MB",
            "5MB",
            "10MB"
        ],
        "correct_answer": 2,
        "explanation": "The CSV upload limit for inviting candidates is 5MB, supporting up to 1200 applicants (Hyrdragon.pdf, Page 4)."
    },
    {
        "id": 8,
        "question": "Which cloud service is NOT listed as a potential hosting provider for TAT?",
        "options": [
            "AWS",
            "Google Cloud Platform",
            "Microsoft Azure",
            "Oracle Cloud"
        ],
        "correct_answer": 3,
        "explanation": "AWS, Google Cloud Platform, and Microsoft Azure are listed as potential cloud providers, but Oracle Cloud is not (PRD TAT.ai, Page 10)."
    },
    {
        "id": 9,
        "question": "What feature allows recruiters to manually input assessment questions?",
        "options": [
            "Dynamic MCQs",
            "Customizable Assessment Options",
            "AI-Supported Video Interviewing",
            "Smart Proctoring"
        ],
        "correct_answer": 1,
        "explanation": "Customizable Assessment Options allow recruiters to manually input questions for assessments (Hyrdragon.pdf, Page 2)."
    },
    {
        "id": 10,
        "question": "What is the goal of TAT's Evaluator System regarding fairness?",
        "options": [
            "Automated scheduling",
            "Ensure fairness and unbiased evaluations",
            "Real-time feedback delivery",
            "Resume data extraction"
        ],
        "correct_answer": 1,
        "explanation": "The Evaluator System ensures fairness and unbiased evaluations through features like fairness and bias control (PRD TAT.ai, Page 8)."
    },
    {
        "id": 11,
        "question": "What is the maximum file size for resume uploads in TAT?",
        "options": [
            "2MB",
            "3MB",
            "5MB",
            "10MB"
        ],
        "correct_answer": 1,
        "explanation": "The maximum file size for resume uploads (PDF, DOC, DOCX) is 3MB, supporting up to 1000 files (Hyrdragon.pdf, Page 4)."
    },
    {
        "id": 12,
        "question": "Which sprint focuses on integrating the LMS Library data?",
        "options": [
            "Sprint 1",
            "Sprint 2",
            "Sprint 3",
            "Sprint 4"
        ],
        "correct_answer": 1,
        "explanation": "Sprint 2 (Sep 15 - Sep 28) focuses on integrating the LMS Library data provided by Raj's team (PRD TAT.ai, Page 12)."
    },
    {
        "id": 13,
        "question": "Which database is NOT mentioned for TAT's tech stack?",
        "options": [
            "PostgreSQL",
            "MySQL",
            "MongoDB",
            "Oracle Database"
        ],
        "correct_answer": 3,
        "explanation": "PostgreSQL, MySQL, and MongoDB are mentioned as database options, but Oracle Database is not (PRD TAT.ai, Page 9)."
    },
    {
        "id": 14,
        "question": "What feature of TAT shuffles multiple-choice questions for each candidate?",
        "options": [
            "Smart Proctoring",
            "Dynamic MCQs",
            "AI-Supported Video Interviewing",
            "Customizable Assessment Options"
        ],
        "correct_answer": 1,
        "explanation": "Dynamic MCQs shuffle multiple-choice questions for each candidate to ensure varied assessments (Hyrdragon.pdf, Page 2)."
    },
    {
        "id": 15,
        "question": "What is the duration of Sprint 4 in the TAT MVP roadmap?",
        "options": [
            "Sep 29 - Oct 12",
            "Oct 13 - Nov 9",
            "Nov 10 - Nov 23",
            "Nov 24 - Dec 7"
        ],
        "correct_answer": 1,
        "explanation": "Sprint 4, focused on NLP and Evaluator System development, runs from Oct 13 - Nov 9 (PRD TAT.ai, Page 12)."
    },
    {
        "id": 16,
        "question": "Which of the following is a goal of the TAT system?",
        "options": [
            "Increase candidate onboarding time",
            "Reduce time-to-hire",
            "Limit candidate feedback",
            "Manual interview scheduling"
        ],
        "correct_answer": 1,
        "explanation": "A key goal of TAT is to reduce time-to-hire by automating the technical interview process (PRD TAT.ai, Page 6)."
    },
    {
        "id": 17,
        "question": "What type of authentication is used in the TAT system?",
        "options": [
            "SAML",
            "OAuth 2.0",
            "Kerberos",
            "Basic Authentication"
        ],
        "correct_answer": 1,
        "explanation": "The TAT tech stack uses OAuth 2.0 and JWT for authentication (PRD TAT.ai, Page 11)."
    },
    {
        "id": 18,
        "question": "What is the purpose of the Skill Testing feature in TAT?",
        "options": [
            "Resume scoring",
            "Job description creation",
            "Assessing various candidate skills",
            "Email notification management"
        ],
        "correct_answer": 2,
        "explanation": "Skill Testing includes assessments like MCQs, technical coding, and video conferencing to evaluate candidate skills (Hyrdragon.pdf, Page 1)."
    },
    {
        "id": 19,
        "question": "Which tool is used for frontend testing in the TAT tech stack?",
        "options": [
            "PyTest",
            "Jest",
            "Mocha",
            "Selenium"
        ],
        "correct_answer": 1,
        "explanation": "Jest is specified for frontend testing in the TAT tech stack (PRD TAT.ai, Page 9)."
    },
    {
        "id": 20,
        "question": "What happens if Raj's LMS Library is not ready by Sep 14?",
        "options": [
            "Delay the entire project",
            "Use a dummy dataset",
            "Skip LMS integration",
            "Outsource the LMS"
        ],
        "correct_answer": 1,
        "explanation": "If Raj's LMS is not ready by Sep 14, a dummy dataset will be used for Sprint 2 (PRD TAT.ai, Page 12)."
    },
    {
        "id": 21,
        "question": "Which round type is NOT currently available in TAT?",
        "options": [
            "MCQ",
            "Full Stack Developer",
            "Syntax Based Programming",
            "AI Bot Interview"
        ],
        "correct_answer": 3,
        "explanation": "The AI Bot Interview round is listed as 'coming soon' and not currently available (Hyrdragon.pdf, Page 3)."
    },
    {
        "id": 22,
        "question": "What is the focus of Release 1 in the TAT release plan?",
        "options": [
            "NLP and Evaluator System",
            "Resume Analyser and Question Generator",
            "UI/UX Finalization",
            "Post-Launch Enhancements"
        ],
        "correct_answer": 1,
        "explanation": "Release 1 (Nov 10-17, 2024) includes Resume Analyser, LMS Library Integration, and Question Generator (PRD TAT.ai, Page 3)."
    },
    {
        "id": 23,
        "question": "Which framework is used for backend development in TAT?",
        "options": [
            "Spring",
            "Django",
            "Laravel",
            "Ruby on Rails"
        ],
        "correct_answer": 1,
        "explanation": "Django or Flask is used for backend development in Python (PRD TAT.ai, Page 9)."
    },
    {
        "id": 24,
        "question": "What does the Smart Proctoring feature deactivate to prevent cheating?",
        "options": [
            "Audio input",
            "Tab switching and Esc option",
            "Video feed",
            "Keyboard shortcuts"
        ],
        "correct_answer": 1,
        "explanation": "Smart Proctoring deactivates tab switching and the Esc option to prevent cheating (Hyrdragon.pdf, Page 1)."
    },
    {
        "id": 25,
        "question": "When is the TAT beta launch scheduled?",
        "options": [
            "Sep 29 - Oct 12",
            "Oct 13 - Nov 9",
            "Nov 10 - Nov 23",
            "Dec 8 - Dec 15"
        ],
        "correct_answer": 2,
        "explanation": "The beta launch is part of Sprint 5, scheduled for Nov 10 - Nov 23 (PRD TAT.ai, Page 13)."
    },
    {
        "id": 26,
        "question": "Which of the following is a use case for TAT?",
        "options": [
            "Payroll management",
            "Initial technical screening",
            "Employee training",
            "Project management"
        ],
        "correct_answer": 1,
        "explanation": "Initial technical screening is a key use case for TAT, filtering unqualified candidates (PRD TAT.ai, Page 6)."
    },
    {
        "id": 27,
        "question": "What is the maximum number of questions allowed for a coding round?",
        "options": [
            "5",
            "10",
            "15",
            "20"
        ],
        "correct_answer": 1,
        "explanation": "The maximum number of questions for a coding round is 10 (Hyrdragon.pdf, Page 15)."
    },
    {
        "id": 28,
        "question": "Which library is used for data manipulation in the TAT backend?",
        "options": [
            "Pandas",
            "Matplotlib",
            "Seaborn",
            "SciPy"
        ],
        "correct_answer": 0,
        "explanation": "Pandas is specified for data manipulation and analysis in the TAT backend (PRD TAT.ai, Page 9)."
    },
    {
        "id": 29,
        "question": "What is included in the candidate application form configuration?",
        "options": [
            "Only email and name",
            "Name, email, location, experience, etc.",
            "Only resume upload",
            "Only job description"
        ],
        "correct_answer": 1,
        "explanation": "The application form includes details like name, email, location, current job, position, company, and experience (Hyrdragon.pdf, Page 4)."
    },
    {
        "id": 30,
        "question": "Which sprint involves finalizing the UI/UX design?",
        "options": [
            "Sprint 3",
            "Sprint 4",
            "Sprint 5",
            "Sprint 6"
        ],
        "correct_answer": 3,
        "explanation": "Sprint 6 (Nov 24 - Dec 7) focuses on finalizing UI/UX design and integration (PRD TAT.ai, Page 13)."
    },
    {
        "id": 31,
        "question": "What is the purpose of the AI-Powered Assessment Feedback in TAT?",
        "options": [
            "Job description creation",
            "Detailed candidate performance feedback",
            "Resume extraction",
            "Question shuffling"
        ],
        "correct_answer": 1,
        "explanation": "AI-Powered Assessment Feedback provides detailed feedback on candidate performance with metrics and scores (Hyrdragon.pdf, Page 1)."
    },
    {
        "id": 32,
        "question": "Which monitoring tool is mentioned in the TAT tech stack?",
        "options": [
            "Nagios",
            "Prometheus",
            "Zabbix",
            "Nagios"
        ],
        "correct_answer": 1,
        "explanation": "Prometheus or Grafana is mentioned for performance monitoring in the TAT tech stack (PRD TAT.ai, Page 11)."
    },
    {
        "id": 33,
        "question": "What is the purpose of the Skill Gap Analysis in TAT?",
        "options": [
            "Scheduling interviews",
            "Identifying candidate skill deficiencies",
            "Generating job descriptions",
            "Tracking candidate progress"
        ],
        "correct_answer": 1,
        "explanation": "Skill Gap Analysis identifies and evaluates candidates' current skill levels and highlights areas needing improvement (PRD TAT.ai, Page 4)."
    },
    {
        "id": 34,
        "question": "Which of the following is a component of TAT's Evaluator System?",
        "options": [
            "Resume upload",
            "Code editor integration",
            "Job posting",
            "Email notifications"
        ],
        "correct_answer": 1,
        "explanation": "The Evaluator System includes code editor/IDE integration for coding assessments (PRD TAT.ai, Page 8)."
    },
    {
        "id": 35,
        "question": "What is the duration per question in a coding round as set by the recruiter?",
        "options": [
            "Fixed 1 minute",
            "Manually set by recruiter",
            "Fixed 5 minutes",
            "No time limit"
        ],
        "correct_answer": 1,
        "explanation": "The duration per question in a coding round is manually set by the recruiter (Hyrdragon.pdf, Page 15)."
    },
    {
        "id": 36,
        "question": "Which cloud provider service is used for scalable compute instances in TAT?",
        "options": [
            "AWS EC2",
            "Azure Blob Storage",
            "GCP Cloud SQL",
            "AWS S3"
        ],
        "correct_answer": 0,
        "explanation": "AWS EC2 is used for scalable compute instances in the TAT hosting infrastructure (PRD TAT.ai, Page 10)."
    },
    {
        "id": 37,
        "question": "What feature allows candidates to track their skill progress in TAT?",
        "options": [
            "Skill Tracking",
            "Resume Analyzer",
            "Matchmaker",
            "Dynamic MCQs"
        ],
        "correct_answer": 0,
        "explanation": "Skill Tracking allows candidates to track their progress in acquiring and mastering skills (PRD TAT.ai, Page 5)."
    },
    {
        "id": 38,
        "question": "What is the purpose of the recruiter dashboard in TAT?",
        "options": [
            "Candidate resume storage",
            "Manage assessments and view results",
            "Generate AI questions",
            "Conduct video interviews"
        ],
        "correct_answer": 1,
        "explanation": "The recruiter dashboard is designed to manage assessments and view results (PRD TAT.ai, Page 8)."
    },
    {
        "id": 39,
        "question": "Which sprint includes pre-sprint planning for TAT?",
        "options": [
            "Sprint 0",
            "Sprint 1",
            "Sprint 2",
            "Sprint 3"
        ],
        "correct_answer": 0,
        "explanation": "Sprint 0 (Aug 30 - Sep 1) involves pre-sprint planning to finalize project goals and scope (PRD TAT.ai, Page 12)."
    },
    {
        "id": 40,
        "question": "What is the file format supported for resume uploads in TAT?",
        "options": [
            "PDF only",
            "PDF, DOC, DOCX",
            "DOC only",
            "TXT, PDF, DOC"
        ],
        "correct_answer": 1,
        "explanation": "TAT supports PDF, DOC, and DOCX formats for resume uploads (Hyrdragon.pdf, Page 4)."
    },
    {
        "id": 41,
        "question": "Which of the following is an operational dependency for TAT?",
        "options": [
            "Budget allocation",
            "Timely beta testing feedback",
            "Frontend framework selection",
            "ML model training"
        ],
        "correct_answer": 1,
        "explanation": "Timely feedback from beta testing is an operational dependency for final refinements (PRD TAT.ai, Page 4)."
    },
    {
        "id": 42,
        "question": "What is the purpose of the AI-Supported Video Interviewing feature?",
        "options": [
            "Resume scoring",
            "Displaying AI-processed questions",
            "Automated scheduling",
            "Skill gap analysis"
        ],
        "correct_answer": 1,
        "explanation": "AI-Supported Video Interviewing displays AI-processed questions during video interviews (Hyrdragon.pdf, Page 2)."
    },
    {
        "id": 43,
        "question": "Which tool is used for CI/CD in the TAT tech stack?",
        "options": [
            "Travis CI",
            "Jenkins",
            "CircleCI",
            "Bamboo"
        ],
        "correct_answer": 1,
        "explanation": "Jenkins, GitHub Actions, or GitLab CI/CD are used for CI/CD in the TAT tech stack (PRD TAT.ai, Page 11)."
    },
    {
        "id": 44,
        "question": "What is the maximum number of applicants supported by CSV upload?",
        "options": [
            "500",
            "1000",
            "1200",
            "1500"
        ],
        "correct_answer": 2,
        "explanation": "CSV upload supports up to 1200 applicants (Hyrdragon.pdf, Page 4)."
    },
    {
        "id": 45,
        "question": "Which sprint is responsible for the Question Generator development?",
        "options": [
            "Sprint 1",
            "Sprint 2",
            "Sprint 3",
            "Sprint 4"
        ],
        "correct_answer": 2,
        "explanation": "Sprint 3 (Sep 29 - Oct 12) focuses on developing and integrating the Question Generator (PRD TAT.ai, Page 12)."
    },
    {
        "id": 46,
        "question": "What type of testing is conducted to ensure TAT components work together?",
        "options": [
            "Unit Testing",
            "Integration Testing",
            "User Acceptance Testing",
            "Performance Testing"
        ],
        "correct_answer": 1,
        "explanation": "Integration Testing ensures different TAT components work together seamlessly (PRD TAT.ai, Page 8)."
    },
    {
        "id": 47,
        "question": "Which feature provides certificates upon assessment completion?",
        "options": [
            "Skill Certification",
            "Skill Tracking",
            "Resume Analyzer",
            "Matchmaker"
        ],
        "correct_answer": 0,
        "explanation": "Skill Certification provides certificates or badges upon successful completion of assessments (PRD TAT.ai, Page 5)."
    },
    {
        "id": 48,
        "question": "What is the focus of Sprint 5 in the TAT roadmap?",
        "options": [
            "Resume Analyser",
            "LMS Integration",
            "Beta Testing",
            "Official Launch"
        ],
        "correct_answer": 2,
        "explanation": "Sprint 5 (Nov 10 - Nov 23) involves comprehensive testing and beta launch (PRD TAT.ai, Page 13)."
    },
    {
        "id": 49,
        "question": "Which security measure is used for secure communication in TAT?",
        "options": [
            "Firewall",
            "SSL/TLS",
            "VPN",
            "Intrusion Detection"
        ],
        "correct_answer": 1,
        "explanation": "SSL/TLS is used for secure communication in the TAT tech stack (PRD TAT.ai, Page 11)."
    },
    {
        "id": 50,
        "question": "What is the role of the Matchmaker in the TAT system?",
        "options": [
            "Generates questions",
            "Compares resumes to job descriptions",
            "Conducts proctoring",
            "Manages email notifications"
        ],
        "correct_answer": 1,
        "explanation": "The Matchmaker compares job descriptions with resumes to provide a suitability score (Hyrdragon.pdf, Page 1)."
    },
    {
        "id": 51,
        "question": "Which of the following is a feature of the TAT recruiter dashboard?",
        "options": [
            "Code editor",
            "Sourcing funnel chart",
            "Resume upload",
            "Question generator"
        ],
        "correct_answer": 1,
        "explanation": "The recruiter dashboard includes a sourcing funnel chart with 5 fields (Hyrdragon.pdf, Page 14)."
    },
    {
        "id": 52,
        "question": "What is the duration of Sprint 6 in the TAT roadmap?",
        "options": [
            "Nov 10 - Nov 23",
            "Nov 24 - Dec 7",
            "Dec 8 - Dec 15",
            "Sep 29 - Oct 12"
        ],
        "correct_answer": 1,
        "explanation": "Sprint 6 runs from Nov 24 - Dec 7, focusing on UI/UX finalization (PRD TAT.ai, Page 13)."
    },
    {
        "id": 53,
        "question": "Which data pipeline tool is mentioned in the TAT tech stack?",
        "options": [
            "Apache Spark",
            "Apache Kafka",
            "Hadoop",
            "Flink"
        ],
        "correct_answer": 1,
        "explanation": "Apache Kafka is one of the data pipeline tools mentioned for TAT (PRD TAT.ai, Page 10)."
    },
    {
        "id": 54,
        "question": "What is the purpose of the Automated Question Generation feature?",
        "options": [
            "Resume scoring",
            "Generating questions based on topics and difficulty",
            "Conducting video interviews",
            "Providing real-time feedback"
        ],
        "correct_answer": 1,
        "explanation": "Automated Question Generation creates questions based on topics, number of questions, and difficulty levels (Hyrdragon.pdf, Page 2)."
    },
    {
        "id": 55,
        "question": "Which sprint involves the official TAT launch?",
        "options": [
            "Sprint 4",
            "Sprint 5",
            "Sprint 6",
            "Sprint 7"
        ],
        "correct_answer": 3,
        "explanation": "Sprint 7 (Dec 8 - Dec 15) includes the official launch of TAT (PRD TAT.ai, Page 13)."
    },
    {
        "id": 56,
        "question": "What is the purpose of the Skill-Based Practice Questions feature?",
        "options": [
            "Resume analysis",
            "Providing practice questions for skills",
            "Job description creation",
            "Email management"
        ],
        "correct_answer": 1,
        "explanation": "Skill-Based Practice Questions generate practice questions aligned with targeted skills (PRD TAT.ai, Page 5)."
    },
    {
        "id": 57,
        "question": "Which of the following is a component of the TAT candidate journey?",
        "options": [
            "Payroll processing",
            "Applications, Screened, Shortlisted",
            "Employee onboarding",
            "Performance reviews"
        ],
        "correct_answer": 1,
        "explanation": "The candidate journey includes stages like Applications, Screened, and Shortlisted (Hyrdragon.pdf, Page 2)."
    },
    {
        "id": 58,
        "question": "What is the role of the UI/UX Designer in the TAT project?",
        "options": [
            "Develop ML models",
            "Design user-friendly interfaces",
            "Manage infrastructure",
            "Conduct beta testing"
        ],
        "correct_answer": 1,
        "explanation": "The UI/UX Designer designs user-friendly interfaces to ensure a good user experience (PRD TAT.ai, Page 12)."
    },
    {
        "id": 59,
        "question": "Which testing tool is used for backend testing in TAT?",
        "options": [
            "Jest",
            "PyTest",
            "Mocha",
            "Cypress"
        ],
        "correct_answer": 1,
        "explanation": "PyTest is used for backend testing in the TAT tech stack (PRD TAT.ai, Page 11)."
    },
    {
        "id": 60,
        "question": "What is the buffer time allocated for TAT's marketing activities?",
        "options": [
            "1-2 weeks",
            "2-3 weeks",
            "3-4 weeks",
            "4-5 weeks"
        ],
        "correct_answer": 1,
        "explanation": "A buffer time of 2-3 weeks is allocated for marketing activities and staging work (PRD TAT.ai, Page 13)."
    },
    {
        "id": 61,
        "question": "Which feature allows candidates to upload resumes for skill gap analysis?",
        "options": [
            "Matchmaker",
            "Resume Analyzer",
            "Skill Testing",
            "Evaluator System"
        ],
        "correct_answer": 1,
        "explanation": "The Resume Analyzer allows candidates to upload resumes for skill gap analysis (PRD TAT.ai, Page 8)."
    },
    {
        "id": 62,
        "question": "What is the purpose of the Real-Time Image Capture in the Evaluator System?",
        "options": [
            "Resume scoring",
            "Ensuring fairness via image comparison",
            "Generating questions",
            "Scheduling interviews"
        ],
        "correct_answer": 1,
        "explanation": "Real-Time Image Capture compares images to ensure fairness and prevent cheating (PRD TAT.ai, Page 8)."
    },
    {
        "id": 63,
        "question": "Which of the following is a competitor to TAT?",
        "options": [
            "Zoom",
            "Mettl",
            "Slack",
            "Trello"
        ],
        "correct_answer": 1,
        "explanation": "Mettl is listed as a competitor to the TAT system (PRD TAT.ai, Page 7)."
    },
    {
        "id": 64,
        "question": "What is the purpose of the LMS Library Integration in TAT?",
        "options": [
            "Resume scoring",
            "Providing learning materials",
            "Question generation",
            "Proctoring"
        ],
        "correct_answer": 1,
        "explanation": "LMS Library Integration provides learning materials for candidates (PRD TAT.ai, Page 5)."
    },
    {
        "id": 65,
        "question": "Which sprint involves comprehensive testing for TAT?",
        "options": [
            "Sprint 3",
            "Sprint 4",
            "Sprint 5",
            "Sprint 6"
        ],
        "correct_answer": 2,
        "explanation": "Sprint 5 (Nov 10 - Nov 23) involves comprehensive testing and beta launch (PRD TAT.ai, Page 13)."
    },
    {
        "id": 66,
        "question": "What is the role of the DevOps Engineer in the TAT project?",
        "options": [
            "Develop AI models",
            "Manage infrastructure and deployment",
            "Design UI/UX",
            "Conduct testing"
        ],
        "correct_answer": 1,
        "explanation": "The DevOps Engineer manages infrastructure and ensures smooth deployment (PRD TAT.ai, Page 12)."
    },
    {
        "id": 67,
        "question": "Which feature allows recruiters to set a threshold for automated shortlisting?",
        "options": [
            "Smart Proctoring",
            "Shortlisting Option",
            "Dynamic MCQs",
            "Resume Analyzer"
        ],
        "correct_answer": 1,
        "explanation": "The Shortlisting Option allows recruiters to set a threshold for automated shortlisting (Hyrdragon.pdf, Page 3)."
    },
    {
        "id": 68,
        "question": "Which of the following is a frontend framework option for TAT?",
        "options": [
            "Django",
            "React.js",
            "Flask",
            "Express.js"
        ],
        "correct_answer": 1,
        "explanation": "React.js or Vue.js are frontend framework options for TAT (PRD TAT.ai, Page 9)."
    },
    {
        "id": 69,
        "question": "What is the purpose of the Performance Analytics feature in TAT?",
        "options": [
            "Resume extraction",
            "Assessing assessment effectiveness",
            "Question generation",
            "Proctoring"
        ],
        "correct_answer": 1,
        "explanation": "Performance Analytics provides tools to assess the effectiveness of assessments and candidate skills (PRD TAT.ai, Page 5)."
    },
    {
        "id": 70,
        "question": "Which sprint includes the development of the NLP system?",
        "options": [
            "Sprint 2",
            "Sprint 3",
            "Sprint 4",
            "Sprint 5"
        ],
        "correct_answer": 2,
        "explanation": "Sprint 4 (Oct 13 - Nov 9) includes the development of the NLP system (PRD TAT.ai, Page 12)."
    },
    {
        "id": 71,
        "question": "What is the maximum duration per MCQ question in TAT?",
        "options": [
            "30 seconds",
            "1 minute",
            "2 minutes",
            "5 minutes"
        ],
        "correct_answer": 1,
        "explanation": "The duration for MCQ questions is 1 minute per question (Hyrdragon.pdf, Page 15)."
    },
    {
        "id": 72,
        "question": "Which of the following is a resource dependency for TAT?",
        "options": [
            "Cloud provider selection",
            "Availability of skilled personnel",
            "Beta testing feedback",
            "NLP library integration"
        ],
        "correct_answer": 1,
        "explanation": "Availability of skilled personnel is a resource dependency for TAT (PRD TAT.ai, Page 4)."
    },
    {
        "id": 73,
        "question": "What feature allows candidates to provide feedback on their TAT experience?",
        "options": [
            "Skill Testing",
            "Assessment Completion",
            "Resume Analyzer",
            "Matchmaker"
        ],
        "correct_answer": 1,
        "explanation": "Candidates can provide ratings and feedback about their experience at assessment completion (Hyrdragon.pdf, Page 5)."
    },
    {
        "id": 74,
        "question": "Which of the following is a TAT candidate screen?",
        "options": [
            "Recruiter profile",
            "Upload resume",
            "Job creation",
            "Dashboard insights"
        ],
        "correct_answer": 1,
        "explanation": "Upload resume is a candidate screen in TAT (Hyrdragon.pdf, Page 16)."
    },
    {
        "id": 75,
        "question": "What is the purpose of the Interactive Simulations feature in TAT?",
        "options": [
            "Resume scoring",
            "Offering coding challenges",
            "Job description creation",
            "Email notifications"
        ],
        "correct_answer": 1,
        "explanation": "Interactive Simulations offer simulations and coding challenges for real-world problems (PRD TAT.ai, Page 5)."
    },
    {
        "id": 76,
        "question": "Which sprint involves bug fixes based on beta feedback?",
        "options": [
            "Sprint 4",
            "Sprint 5",
            "Sprint 6",
            "Sprint 7"
        ],
        "correct_answer": 3,
        "explanation": "Sprint 7 (Dec 8 - Dec 15) involves final adjustments based on beta testing feedback (PRD TAT.ai, Page 13)."
    },
    {
        "id": 77,
        "question": "What is the role of the Content Specialist in the TAT project?",
        "options": [
            "Develop AI models",
            "Prepare documentation",
            "Manage infrastructure",
            "Conduct testing"
        ],
        "correct_answer": 1,
        "explanation": "The Content Specialist prepares documentation and study materials (PRD TAT.ai, Page 12)."
    },
    {
        "id": 78,
        "question": "Which of the following is a TAT recruiter screen change?",
        "options": [
            "Add video conferencing",
            "Remove New response from sourcing funnel",
            "Add resume upload",
            "Change question generator"
        ],
        "correct_answer": 1,
        "explanation": "The recruiter dashboard change includes removing New response from the sourcing funnel chart (Hyrdragon.pdf, Page 14)."
    },
    {
        "id": 79,
        "question": "What is the purpose of the Automated Scheduling feature in TAT?",
        "options": [
            "Resume analysis",
            "Automate interview bookings",
            "Generate questions",
            "Provide feedback"
        ],
        "correct_answer": 1,
        "explanation": "Automated Scheduling integrates features to automate interview and assessment bookings (PRD TAT.ai, Page 5)."
    },
    {
        "id": 80,
        "question": "Which tool is used for version control in TAT?",
        "options": [
            "SVN",
            "Git",
            "Mercurial",
            "Perforce"
        ],
        "correct_answer": 1,
        "explanation": "Git is used for version control with GitHub or GitLab for repository management (PRD TAT.ai, Page 9)."
    },
    {
        "id": 81,
        "question": "What is the purpose of the Real-Time Feedback feature in TAT?",
        "options": [
            "Resume scoring",
            "Enhance candidate learning",
            "Question generation",
            "Proctoring"
        ],
        "correct_answer": 1,
        "explanation": "Real-Time Feedback provides immediate performance feedback to enhance candidate learning (PRD TAT.ai, Page 5)."
    },
    {
        "id": 82,
        "question": "Which of the following is a TAT candidate screen change?",
        "options": [
            "Add job creation",
            "Add first name, last name to upload resume page",
            "Change dashboard layout",
            "Remove assessment list"
        ],
        "correct_answer": 1,
        "explanation": "The upload resume page for candidates includes adding first name, last name, and mobile number fields (Hyrdragon.pdf, Page 16)."
    },
    {
        "id": 83,
        "question": "What is the role of the Customer Support Specialist in TAT?",
        "options": [
            "Develop AI models",
            "Handle user queries during beta and launch",
            "Design UI/UX",
            "Conduct testing"
        ],
        "correct_answer": 1,
        "explanation": "The Customer Support Specialist handles user queries during beta and launch (PRD TAT.ai, Page 12)."
    },
    {
        "id": 84,
        "question": "Which feature allows recruiters to sort candidates by location?",
        "options": [
            "Assessment Report",
            "Recruiter Dashboard",
            "Talent Pool",
            "Insights"
        ],
        "correct_answer": 0,
        "explanation": "The Assessment Report includes a popup for sorting candidates by location and alphabet (Hyrdragon.pdf, Page 15)."
    },
    {
        "id": 85,
        "question": "What is the purpose of the Skill Endorsements feature in TAT?",
        "options": [
            "Resume scoring",
            "Allowing recruiters to validate skills",
            "Question generation",
            "Proctoring"
        ],
        "correct_answer": 1,
        "explanation": "Skill Endorsements allow recruiters or mentors to endorse and validate acquired skills (PRD TAT.ai, Page 5)."
    },
    {
        "id": 86,
        "question": "Which sprint includes the development of the Resume Analyser?",
        "options": [
            "Sprint 1",
            "Sprint 2",
            "Sprint 3",
            "Sprint 4"
        ],
        "correct_answer": 0,
        "explanation": "Sprint 1 (Sep 1 - Sep 14) focuses on developing and integrating the Resume Analyser (PRD TAT.ai, Page 12)."
    },
    {
        "id": 87,
        "question": "What is the purpose of the Job Creation process in TAT?",
        "options": [
            "Resume analysis",
            "Uploading job details like role and salary",
            "Generating questions",
            "Proctoring"
        ],
        "correct_answer": 1,
        "explanation": "Job Creation involves uploading details like job role, location, salary, and job description (Hyrdragon.pdf, Page 3)."
    },
    {
        "id": 88,
        "question": "Which of the following is a TAT dashboard insight?",
        "options": [
            "Code editor",
            "Email insights",
            "Question generator",
            "Proctoring"
        ],
        "correct_answer": 1,
        "explanation": "Email insights (sent, responded, unread) are part of the TAT dashboard insights (Hyrdragon.pdf, Page 2)."
    },
    {
        "id": 89,
        "question": "What is the purpose of the Assessment Guideline screen for candidates?",
        "options": [
            "Resume upload",
            "Display timelines and proctoring information",
            "Generate questions",
            "Provide feedback"
        ],
        "correct_answer": 1,
        "explanation": "The Assessment Guideline screen displays timelines, proctoring information, and marking details (Hyrdragon.pdf, Page 16)."
    },
    {
        "id": 90,
        "question": "Which of the following is a TAT technical dependency?",
        "options": [
            "Marketing strategy",
            "LMS Library integration",
            "Budget allocation",
            "User training"
        ],
        "correct_answer": 1,
        "explanation": "Integration with the LMS Library is a technical dependency for TAT (PRD TAT.ai, Page 3)."
    },
    {
        "id": 91,
        "question": "What is the purpose of the Assessment Instruction screen in TAT?",
        "options": [
            "Resume scoring",
            "Providing test instructions",
            "Question generation",
            "Proctoring"
        ],
        "correct_answer": 1,
        "explanation": "The Assessment Instruction screen provides instructions for candidates before the test (Hyrdragon.pdf, Page 16)."
    },
    {
        "id": 92,
        "question": "Which of the following is a feature of the TAT code IDE?",
        "options": [
            "Resume upload",
            "Multiple questions for a single assessment",
            "Job description creation",
            "Email notifications"
        ],
        "correct_answer": 1,
        "explanation": "The Assessment Code IDE supports multiple questions for a single assessment and displays a timer (Hyrdragon.pdf, Page 16)."
    },
    {
        "id": 93,
        "question": "What is the role of the Marketing Specialist in the TAT project?",
        "options": [
            "Develop AI models",
            "Plan and execute marketing strategy",
            "Design UI/UX",
            "Conduct testing"
        ],
        "correct_answer": 1,
        "explanation": "The Marketing Specialist plans and executes the marketing strategy for the MVP launch (PRD TAT.ai, Page 12)."
    },
    {
        "id": 94,
        "question": "Which of the following is a TAT recruiter screen?",
        "options": [
            "Assessment Code IDE",
            "Recruiter Dashboard",
            "Upload resume",
            "Assessment Guideline"
        ],
        "correct_answer": 1,
        "explanation": "The Recruiter Dashboard is a recruiter screen in TAT (Hyrdragon.pdf, Page 14)."
    },
    {
        "id": 95,
        "question": "What is the purpose of the Talent Pool in TAT?",
        "options": [
            "Resume scoring",
            "Managing candidate data",
            "Question generation",
            "Proctoring"
        ],
        "correct_answer": 1,
        "explanation": "The Talent Pool is used for managing candidate data (Hyrdragon.pdf, Page 15)."
    },
    {
        "id": 96,
        "question": "Which sprint involves user training and support preparation?",
        "options": [
            "Sprint 4",
            "Sprint 5",
            "Sprint 6",
            "Sprint 7"
        ],
        "correct_answer": 3,
        "explanation": "Sprint 7 (Dec 8 - Dec 15) includes preparing user training and support materials (PRD TAT.ai, Page 9)."
    },
    {
        "id": 97,
        "question": "What is the purpose of the Email Insights feature in TAT?",
        "options": [
            "Resume analysis",
            "Tracking email status (sent, responded, unread)",
            "Question generation",
            "Proctoring"
        ],
        "correct_answer": 1,
        "explanation": "Email Insights tracks email status (sent, responded, unread) on the dashboard (Hyrdragon.pdf, Page 2)."
    },
    {
        "id": 98,
        "question": "Which of the following is a TAT candidate screen?",
        "options": [
            "Recruiter profile",
            "Assessment Completion",
            "Job creation",
            "Dashboard insights"
        ],
        "correct_answer": 1,
        "explanation": "Assessment Completion is a candidate screen in TAT (Hyrdragon.pdf, Page 16)."
    },
    {
        "id": 99,
        "question": "What is the purpose of the Feedback Loop in TAT?",
        "options": [
            "Resume scoring",
            "Informing assessment improvements",
            "Question generation",
            "Proctoring"
        ],
        "correct_answer": 1,
        "explanation": "The Feedback Loop uses skill-based learning outcomes to inform assessment improvements (PRD TAT.ai, Page 6)."
    },
    {
        "id": 100,
        "question": "Which of the following is a TAT resource allocation role?",
        "options": [
            "Customer Support Specialist",
            "External Consultant",
            "Third-Party Vendor",
            "Beta Tester"
        ],
        "correct_answer": 0,
        "explanation": "The Customer Support Specialist is a resource allocation role for handling user queries (PRD TAT.ai, Page 12)."
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
