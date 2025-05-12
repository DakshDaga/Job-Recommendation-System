
# import streamlit as st
# import sqlite3
# import hashlib
# import os
# from question_engine import QuestionEngine
# from dotenv import load_dotenv
# import json

# # Initialize environment and database
# load_dotenv()

# st.set_page_config(
#     page_title="AI Based Career Guide",
#     page_icon="🚀",                
#     layout="wide",
#     initial_sidebar_state="expanded"
# )

# # Database functions
# def init_db():
#     conn = sqlite3.connect('career_app.db')
#     c = conn.cursor()
#     c.execute('''CREATE TABLE IF NOT EXISTS users
#                  (id INTEGER PRIMARY KEY AUTOINCREMENT,
#                   username TEXT UNIQUE,
#                   email TEXT UNIQUE,
#                   password_hash TEXT,
#                   created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    
   
#     c.execute('''CREATE TABLE IF NOT EXISTS user_responses
#                  (user_id INTEGER,
#                   question_id TEXT,
#                   response TEXT,
#                   timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
#                   FOREIGN KEY(user_id) REFERENCES users(id),
#                   UNIQUE(user_id, question_id))''')
#     conn.commit()
#     conn.close()

# def hash_password(password):
#     salt = os.getenv("PASSWORD_SALT", "default_salt")
#     return hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000).hex()

# def register_user(username, email, password):
#     conn = sqlite3.connect('career_app.db')
#     c = conn.cursor()
#     try:
#         c.execute("INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
#                  (username, email, hash_password(password)))
#         conn.commit()
#         return True
#     except sqlite3.IntegrityError:
#         return False
#     finally:
#         conn.close()

# def verify_user(username, password):
#     conn = sqlite3.connect('career_app.db')
#     c = conn.cursor()
#     c.execute("SELECT id, password_hash FROM users WHERE username = ?", (username,))
#     result = c.fetchone()
#     conn.close()
#     if result:
#         user_id, stored_hash = result
#         if stored_hash == hash_password(password):
#             return user_id
#     return None

# def save_user_responses(user_id, responses):
#     conn = sqlite3.connect('career_app.db')
#     c = conn.cursor()
#     try:
#         for q_id, response in responses.items():
#             if isinstance(response, list):
#                 response = json.dumps(response)
#             c.execute("""INSERT OR REPLACE INTO user_responses 
#                           (user_id, question_id, response) VALUES (?, ?, ?)""",
#                       (user_id, q_id, response))
#         conn.commit()
#     finally:
#         conn.close()

# def load_user_responses(user_id):
#     conn = sqlite3.connect('career_app.db')
#     c = conn.cursor()
#     c.execute("SELECT question_id, response FROM user_responses WHERE user_id = ?", (user_id,))
#     results = c.fetchall()
#     conn.close()
    
#     responses = {}
#     for q_id, response in results:
#         try:
#             responses[q_id] = json.loads(response)
#         except json.JSONDecodeError:
#             responses[q_id] = response
#     return responses


# init_db()

# # Authentication pages
# def show_login():
#     st.title("AI BASED CAREER RECOMMENDER")
#     st.subheader("Login to your account")
    
#     with st.form("login_form"):
#         username = st.text_input("Username")
#         password = st.text_input("Password", type="password")
        
#         if st.form_submit_button("Login"):
#             user_id = verify_user(username, password)
#             if user_id:
#                 st.session_state.user_id = user_id
#                 st.session_state.username = username
#                 st.session_state.authenticated = True
                
               
#                 st.session_state.user_responses = load_user_responses(user_id)
#                 st.rerun()
#             else:
#                 st.error("Invalid username or password")
    
#     if st.button("New user? Register here"):
#         st.session_state.show_register = True
#         st.rerun()

# def show_register():
#     st.title("Create New Account")
    
#     with st.form("register_form"):
#         username = st.text_input("Username (must be unique)")
#         email = st.text_input("Email address")
#         password = st.text_input("Password", type="password")
#         confirm_password = st.text_input("Confirm password", type="password")
        
#         if st.form_submit_button("Register"):
#             if password != confirm_password:
#                 st.error("Passwords do not match")
#             elif len(password) < 6:
#                 st.error("Password must be at least 6 characters")
#             else:
#                 if register_user(username, email, password):
#                     st.success("Registration successful! Please login")
#                     st.session_state.show_register = False
#                     st.rerun()
#                 else:
#                     st.error("Username or email already exists")
    
#     if st.button("← Back to login"):
#         st.session_state.show_register = False
#         st.rerun()

# # Main application
# def career_counselling_app():
#     @st.cache_resource
#     def init_engine():
#         return QuestionEngine()

#     engine = init_engine()

   
#     if 'user_responses' not in st.session_state:
#         st.session_state.user_responses = {}
#     if 'current_question' not in st.session_state:
#         st.session_state.current_question = engine.get_first_question()
#     if 'recommendations' not in st.session_state:
#         st.session_state.recommendations = None

    
#     with st.sidebar:
#         st.markdown(f"### Welcome, {st.session_state.username}!")
#         st.markdown("---")
        
#         if st.session_state.user_responses:
#             st.markdown("**Your profile:**")
#             for q, ans in st.session_state.user_responses.items():
#                 if isinstance(ans, list):
#                     ans = ", ".join(ans)
#                 st.caption(f"{q.split('_')[-1]}. {ans[:30]}...")
        
#         if st.button("Logout"):
           
#             save_user_responses(
#                 st.session_state.user_id,
#                 st.session_state.user_responses
#             )
#             st.session_state.clear()
#             st.rerun()

#     # Main app UI
#     st.title("AI Career Counselling")
#     st.caption("Answer questions to discover your ideal career path")

#     def render_question(question):
#         """Render counselling-style questions"""
#         if not isinstance(question, dict):
#             st.error("System error - loading question")
#             question = {
#                 "id": "fallback_q",
#                 "text": "Which of these best describes you?",
#                 "type": "mcq",
#                 "options": ["Technical", "Creative", "Analytical", "Social"]
#             }

#         question_id = question.get('id', "unknown")
#         st.subheader(question.get('text', "Please answer:"))
        
       
#         q_type = question.get('type', 'mcq')
#         if q_type not in ['mcq', 'multi_select']:
#             q_type = 'mcq'

#         if q_type == 'mcq':
#             options = question.get('options', [])
#             cols = st.columns(2)
#             for i, option in enumerate(options):
#                 with cols[i % 2]:
#                     if st.button(
#                         option,
#                         key=f"opt_{question_id}_{i}",
#                         use_container_width=True,
#                         on_click=lambda o=option: handle_answer(question, o)
#                     ):
#                         pass

#         elif q_type == 'multi_select':
#             options = question.get('options', [])
#             selected = st.multiselect(
#                 "Select all that apply:",
#                 options,
#                 key=f"ms_{question_id}"
#             )
#             if st.button("Submit", type="primary"):
#                 if selected:
#                     handle_answer(question, selected)
#                 else:
#                     st.warning("Please select at least one option")

#     def handle_answer(question, answer):
#         """Process user answers"""
#         question_id = question.get('id', f"temp_{hash(str(question))}")
#         st.session_state.user_responses[question_id] = answer

        
#         next_question = engine.get_next_question(st.session_state.user_responses)
        
#         if next_question is None:
#             st.session_state.recommendations = engine.generate_recommendations(
#                 st.session_state.user_responses
#             )
#         else:
#             st.session_state.current_question = next_question
        
#         st.rerun()

#     def show_recommendations():
#         """Display career recommendations"""
#         st.success("🎯 Your Personalized Career Matches")
#         st.divider()
        
#         for idx, job in enumerate(st.session_state.recommendations, 1):
#             with st.expander(f"{idx}. {job['title']} ({job.get('match_score', 0)}%)", expanded=idx==1):
#                 col1, col2 = st.columns([3,1])
                
#                 with col1:
#                     st.markdown(f"**Industry:** {job.get('industry', 'N/A')}")
#                     st.markdown(f"**Match Reason:** {job.get('match_reason', 'High compatibility')}")
#                     st.markdown(f"**Description:** {job.get('description', 'No description available')}")
                    
#                 with col2:
#                     st.markdown(f"**Salary:** {job.get('salary', 'Not specified')}")
#                     st.markdown(f"**Experience:** {job.get('experience_level', 'Varies')}")
#                     st.markdown(f"**Type:** {', '.join(job.get('job_type', [])) if job.get('job_type') else 'N/A'}")
                
#                 st.progress(min(job.get('match_score', 0)/100, 1.0))
                
#                 if job.get('skills'):
#                     st.markdown(f"**Key Skills:** {', '.join(job['skills'][:5])}")
#                 if job.get('certifications'):
#                     st.markdown(f"**Certifications:** {', '.join(job['certifications'])}")
                
#                 if job.get('url'):
#                     st.markdown(f"[🔗 Learn more]({job['url']})")

#         if st.button("🔄 Start New Session", type="primary"):
           
#             save_user_responses(
#                 st.session_state.user_id,
#                 st.session_state.user_responses
#             )
#             st.session_state.user_responses = {}
#             st.session_state.current_question = engine.get_first_question()
#             st.session_state.recommendations = None
#             st.rerun()

#     # Main render logic
#     if st.session_state.recommendations is not None:
#         show_recommendations()
#     else:
#         render_question(st.session_state.current_question)

# # App routing
# if 'authenticated' not in st.session_state:
#     st.session_state.authenticated = False

# if not st.session_state.authenticated:
#     if st.session_state.get('show_register'):
#         show_register()
#     else:
#         show_login()
# else:
#     career_counselling_app()


# st.divider()
# st.caption("© 2024 Career Counselling Pro | Secure AI-Powered Career Guidance")



import streamlit as st
import sqlite3
import hashlib
import os
from question_engine import QuestionEngine
from dotenv import load_dotenv
import json

# Initialize environment and database
load_dotenv()

# Database functions
def init_db():
    conn = sqlite3.connect('career_app.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  username TEXT UNIQUE,
                  email TEXT UNIQUE,
                  password_hash TEXT,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS user_responses
                 (user_id INTEGER,
                  question_id TEXT,
                  response TEXT,
                  timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY(user_id) REFERENCES users(id),
                  UNIQUE(user_id, question_id))''')
    conn.commit()
    conn.close()

def hash_password(password):
    salt = os.getenv("PASSWORD_SALT", "default_salt")
    return hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000).hex()

def register_user(username, email, password):
    conn = sqlite3.connect('career_app.db')
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
                 (username, email, hash_password(password)))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def verify_user(username, password):
    conn = sqlite3.connect('career_app.db')
    c = conn.cursor()
    c.execute("SELECT id, password_hash FROM users WHERE username = ?", (username,))
    result = c.fetchone()
    conn.close()
    if result:
        user_id, stored_hash = result
        if stored_hash == hash_password(password):
            return user_id
    return None

def save_user_responses(user_id, responses):
    conn = sqlite3.connect('career_app.db')
    c = conn.cursor()
    try:
        for q_id, response in responses.items():
            if isinstance(response, list):
                response = json.dumps(response)
            c.execute("""INSERT OR REPLACE INTO user_responses 
                          (user_id, question_id, response) VALUES (?, ?, ?)""",
                      (user_id, q_id, response))
        conn.commit()
    finally:
        conn.close()

def load_user_responses(user_id):
    conn = sqlite3.connect('career_app.db')
    c = conn.cursor()
    c.execute("SELECT question_id, response FROM user_responses WHERE user_id = ?", (user_id,))
    results = c.fetchall()
    conn.close()
    
    responses = {}
    for q_id, response in results:
        try:
            responses[q_id] = json.loads(response)
        except json.JSONDecodeError:
            responses[q_id] = response
    return responses

def delete_user_data(user_id):
    conn = sqlite3.connect('career_app.db')
    c = conn.cursor()
    try:
        c.execute("DELETE FROM user_responses WHERE user_id = ?", (user_id,))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error deleting data: {str(e)}")
        return False
    finally:
        conn.close()

# Initialize database
init_db()

# Page configuration
st.set_page_config(
    page_title="AI Career Guide Pro",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .st-emotion-cache-1y4p8pa {
        padding: 2rem;
    }
    .stButton button {
        width: 100%;
    }
    .stMarkdown h1 {
        color: #2b5876;
    }
    .st-expander {
        border: 1px solid #e1e4e8;
        border-radius: 8px;
        padding: 1rem;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# Authentication pages
def show_login():
    st.title("🔐 AI Career Guide Pro Login")
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        
        if st.form_submit_button("Login"):
            user_id = verify_user(username, password)
            if user_id:
                st.session_state.user_id = user_id
                st.session_state.username = username
                st.session_state.authenticated = True
                st.session_state.user_responses = load_user_responses(user_id)
                st.session_state.current_page = "questionnaire"
            else:
                st.error("Invalid username or password")
    
    if st.button("New user? Register here"):
        st.session_state.show_register = True

def show_register():
    st.title("📝 Create New Account")
    with st.form("register_form"):
        username = st.text_input("Choose a username")
        email = st.text_input("Email address")
        password = st.text_input("Create password", type="password")
        confirm_password = st.text_input("Confirm password", type="password")
        
        if st.form_submit_button("Register"):
            if password != confirm_password:
                st.error("Passwords don't match")
            elif len(password) < 6:
                st.error("Password must be at least 6 characters")
            else:
                if register_user(username, email, password):
                    st.success("Registration successful! Please login")
                    st.session_state.show_register = False
                else:
                    st.error("Username or email already exists")
    
    if st.button("← Back to login"):
        st.session_state.show_register = False

# Career Explorer Page
def show_career_explorer():
    st.title("🔍 Career Explorer")
    st.write("Discover detailed information about different careers")
    
    with st.form("job_search_form"):
        search_query = st.text_input(
            "Search for careers (e.g. 'data scientist', 'graphic designer')",
            placeholder="Be specific for better results"
        )
        
        if st.form_submit_button("Search Careers", type="primary"):
            if search_query:
                with st.spinner(f"Analyzing {search_query} careers..."):
                    try:
                        engine = QuestionEngine()
                        results = engine.search_jobs(search_query)
                        st.session_state.job_search_results = results
                    except Exception as e:
                        st.error(f"Search error: {str(e)}")
                        st.session_state.job_search_results = None
    
    if 'job_search_results' in st.session_state:
        if st.session_state.job_search_results:
            st.divider()
            st.subheader("Career Details")
            
            for job in st.session_state.job_search_results:
                with st.expander(f"**{job.get('title', 'Career Information')}**", expanded=True):
                    # Improved layout with more details
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        st.markdown("**📝 Description**")
                        st.write(job.get('description', 'No description available'))
                        
                        st.markdown("**🎯 Key Responsibilities**")
                        st.write(job.get('responsibilities', 'Not specified'))
                        
                        st.markdown("**📚 Qualifications**")
                        st.write(job.get('qualifications', 'Not specified'))
                    
                    with col2:
                        st.markdown("**💰 Salary Range**")
                        st.write(job.get('salary', 'Varies by experience'))
                        
                        st.markdown("**📅 Experience Level**")
                        st.write(job.get('experience', 'Entry-level to Senior'))
                        
                        st.markdown("**🌍 Industry**")
                        st.write(job.get('industry', 'Various industries'))
                        
                        if job.get('skills'):
                            st.markdown("**🛠️ Key Skills**")
                            st.write(", ".join(job['skills']))
        else:
            st.warning("No detailed information found. Try a more specific job title.")


# Main Questionnaire Page
def show_questionnaire():
    engine = QuestionEngine()
    
    # Initialize session
    if 'user_responses' not in st.session_state:
        st.session_state.user_responses = load_user_responses(st.session_state.user_id) or {}
    if 'current_question' not in st.session_state:
        st.session_state.current_question = engine.get_first_question()
    if 'recommendations' not in st.session_state:
        st.session_state.recommendations = None
    
    # Progress bar
    if st.session_state.user_responses:
        progress = min(len(st.session_state.user_responses) / 5, 1.0)
        st.progress(progress, text=f"Questionnaire Progress: {int(progress*100)}%")
    
    # Main content
    if st.session_state.recommendations:
        show_recommendations()
    else:
        render_question(st.session_state.current_question)

def render_question(question):
    if not isinstance(question, dict):
        st.error("System error - loading question")
        question = {
            "id": "fallback_q",
            "text": "Which of these best describes you?",
            "type": "mcq",
            "options": ["Technical", "Creative", "Analytical", "Social"]
        }

    question_id = question.get('id', "unknown")
    st.subheader(question.get('text', "Please answer:"))
    
    # Using on_click handler properly
    if question.get('type') == 'mcq':
        options = question.get('options', [])
        cols = st.columns(2)
        for i, option in enumerate(options):
            with cols[i % 2]:
                if st.button(
                    option,
                    key=f"opt_{question_id}_{i}",
                    on_click=lambda o=option: handle_answer(question, o),
                    use_container_width=True
                ):
                    pass  # Handled by on_click

    elif question.get('type') == 'multi_select':
        selected = st.multiselect(
            "Select all that apply:",
            question.get('options', []),
            key=f"ms_{question_id}"
        )
        if st.button("Submit", key=f"submit_{question_id}", type="primary"):
            if selected:
                handle_answer(question, selected)
            else:
                st.warning("Please select at least one option")


def handle_answer(question, answer):
    """Process user answers"""
    question_id = question.get('id', f"temp_{hash(str(question))}")
    st.session_state.user_responses[question_id] = answer

    # Get next question or recommendations
    engine = QuestionEngine()
    next_question = engine.get_next_question(st.session_state.user_responses)
    
    if next_question is None:
        st.session_state.recommendations = engine.generate_recommendations(
            st.session_state.user_responses
        )
    else:
        st.session_state.current_question = next_question
    
    # Save responses
    save_user_responses(st.session_state.user_id, st.session_state.user_responses)

def show_recommendations():
    """Display career recommendations"""
    st.success("🎯 Your Personalized Career Matches")
    st.divider()
    
    for idx, job in enumerate(st.session_state.recommendations, 1):
        with st.expander(f"{idx}. {job['title']} ({job.get('match_score', 0)}%)", expanded=idx==1):
            col1, col2 = st.columns([3,1])
            
            with col1:
                st.markdown(f"**Industry:** {job.get('industry', 'N/A')}")
                st.markdown(f"**Match Reason:** {job.get('match_reason', 'High compatibility')}")
                st.markdown(f"**Description:** {job.get('description', 'No description available')}")
                
            with col2:
                st.markdown(f"**Salary:** {job.get('salary', 'Not specified')}")
                st.markdown(f"**Experience:** {job.get('experience_level', 'Varies')}")
                st.markdown(f"**Type:** {', '.join(job.get('job_type', [])) if job.get('job_type') else 'N/A'}")
            
            st.progress(min(job.get('match_score', 0)/100, 1.0))
            
            if job.get('skills'):
                st.markdown(f"**Key Skills:** {', '.join(job['skills'][:5])}")
            if job.get('certifications'):
                st.markdown(f"**Certifications:** {', '.join(job['certifications'])}")
            
            if job.get('url'):
                st.markdown(f"[🔗 Learn more]({job['url']})")

    if st.button("🔄 Start New Session", type="primary"):
        st.session_state.user_responses = {}
        st.session_state.current_question = QuestionEngine().get_first_question()
        st.session_state.recommendations = None

# Account Settings Page
def show_account_settings():
    st.title("⚙️ Account Settings")
    st.write(f"Logged in as: **{st.session_state.username}**")
    
    st.subheader("Data Management")
    if st.button("🧹 Erase My Questionnaire Data", type="secondary"):
        if st.session_state.get('confirm_delete'):
            if delete_user_data(st.session_state.user_id):
                st.session_state.user_responses = {}
                st.session_state.current_question = QuestionEngine().get_first_question()
                st.success("All your questionnaire data has been erased")
                st.session_state.confirm_delete = False
            else:
                st.error("Failed to delete data")
        else:
            st.session_state.confirm_delete = True
            st.warning("Click again to confirm permanent deletion")
    
    if st.session_state.get('confirm_delete'):
        st.error("This will permanently delete all your questionnaire responses!")
    
    st.subheader("Security")
    if st.button("🔒 Change Password", disabled=True, help="Coming soon"):
        pass

# Main App Router
def main_app():
    # Sidebar navigation
    with st.sidebar:
        st.markdown(f"### 👋 Welcome, {st.session_state.username}!")
        st.divider()
        
        page = st.radio("Navigation", [
            "Career Questionnaire",
            "Career Explorer", 
            "Account Settings"
        ], label_visibility="collapsed")
        
        st.divider()
        if st.button("🚪 Logout", use_container_width=True):
            save_user_responses(st.session_state.user_id, st.session_state.user_responses)
            st.session_state.clear()
    
    # Page routing
    if page == "Career Questionnaire":
        show_questionnaire()
    elif page == "Career Explorer":
        show_career_explorer()
    elif page == "Account Settings":
        show_account_settings()

# App initialization
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    if st.session_state.get('show_register'):
        show_register()
    else:
        show_login()
else:
    main_app()

# Footer
st.divider()
st.caption("© 2024 AI Career Guide Pro | Secure AI-Powered Career Guidance")