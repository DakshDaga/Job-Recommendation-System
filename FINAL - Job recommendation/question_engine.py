import json
import os
import numpy as np
from typing import Dict, List, Optional
import google.generativeai as genai
from dotenv import load_dotenv
import logging

# Initialize logging
logging.basicConfig(filename='engine.log', level=logging.ERROR)

class QuestionEngine:
    def __init__(self):
        self.question_counter = 0
        load_dotenv()
        self._configure_gemini()
        
        # Load data files
        with open('data/jobs.json', 'r') as f:
            self.jobs_data = json.load(f)
            self.jobs = self.jobs_data['jobs']
        
        with open('data/questions.json', 'r') as f:
            self.questions_data = json.load(f)
        
        # Initialize question structures
        self.basic_questions = {
            "q1": self.questions_data['start']
        }
        
        # Precompute embeddings
        self.job_embeddings = self._precompute_job_embeddings()
        self.field_info = self.questions_data.get('metadata', {}).get('field_info', {})

    def _configure_gemini(self):
        """Configure Gemini API with error handling"""
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")
        
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-pro')  # Initialize the model here

    def search_jobs(self, query):
        """Enhanced career search with more details"""
        prompt = f"""Provide comprehensive career information for: {query}
        
        Return JSON with these fields (fill ALL fields):
        {{
            "title": "Job title",
            "industry": "Primary industry",
            "description": "Detailed 3-4 sentence job description",
            "responsibilities": ["List", "of", "typical", "responsibilities"],
            "qualifications": ["Required", "education", "and", "certifications"],
            "skills": ["Technical", "and", "soft", "skills"],
            "salary": "Typical salary range (e.g. '$60,000 - $120,000')",
            "experience": "Required experience level",
            "outlook": "Job market outlook"
        }}
        
        Example for 'data scientist':
        {{
            "title": "Data Scientist",
            "industry": "Technology",
            "description": "Data scientists analyze complex data to extract insights...",
            "responsibilities": ["Develop machine learning models", "Clean datasets", "Create visualizations"],
            "qualifications": ["Bachelor's in CS", "Python proficiency", "Statistics knowledge"],
            "skills": ["Python", "SQL", "Machine Learning", "Data Visualization"],
            "salary": "$90,000 - $150,000",
            "experience": "2-5 years",
            "outlook": "Growing faster than average"
        }}"""
        
        try:
            response = self.model.generate_content(prompt)
            response_text = response.text.strip()
            
            # Improved response parsing
            if '```json' in response_text:
                response_text = response_text.split('```json')[1].split('```')[0].strip()
            
            result = json.loads(response_text)
            
            # Ensure all fields exist
            required_fields = ['title', 'description', 'salary', 'qualifications', 'skills']
            for field in required_fields:
                if field not in result:
                    result[field] = "Information not available"
            
            return [result]  # Return as list for consistency
        
        except Exception as e:
            print(f"Search error: {str(e)}")
            return [{
                "title": query,
                "error": "Could not retrieve detailed information"
            }]
        
    def _precompute_job_embeddings(self) -> Dict[str, List[float]]:
        """Precompute embeddings for all jobs with error handling"""
        embeddings = {}
        for job in self.jobs:
            try:
                text = f"{job['title']} {job['industry']} {' '.join(job.get('skills', []))} {job.get('description', '')}"
                embeddings[job['id']] = self._get_embedding(text)
            except Exception as e:
                logging.error(f"Error embedding job {job['id']}: {str(e)}")
                embeddings[job['id']] = [0.0] * 768
        return embeddings

    def _get_embedding(self, text: str) -> List[float]:
        """Get text embedding using Gemini with robust error handling"""
        try:
            result = genai.embed_content(
                model="models/embedding-001",
                content=text,
                task_type="RETRIEVAL_DOCUMENT"
            )
            return result['embedding']
        except Exception as e:
            logging.error(f"Embedding error: {str(e)}")
            return [0.0] * 768  

    def get_first_question(self) -> Dict:
        """Get the initial question with validation"""
        question = self.basic_questions.get("q1")
        if not question:
            raise ValueError("Initial question not found")
        return question

    def get_next_question(self, user_responses: Dict) -> Optional[Dict]:
        """Generate the next question with comprehensive validation"""
        try:
            new_question = self._generate_ai_question(user_responses)
            
           
            if not isinstance(new_question, dict):
                new_question = self._get_fallback_question(user_responses)
            
           
            required_fields = ['id', 'text', 'type']
            for field in required_fields:
                if field not in new_question:
                    new_question = self._get_fallback_question(user_responses)
                    break
            
           
            if new_question['type'] in ['mcq', 'multi_select'] and 'options' not in new_question:
                new_question['options'] = ["Option 1", "Option 2"]
            
           
            if len(user_responses) >= 5:  
                return None
                
            return new_question
            
        except Exception as e:
            logging.error(f"Error generating next question: {str(e)}")
            return self._get_fallback_question(user_responses)

    def _generate_ai_question(self, user_responses: Dict) -> Dict:
        """Generates counselling-style follow-up questions"""
        try:
            context = self._build_conversation_context(user_responses)
            
            prompt = f"""Act as a career counsellor. Generate exactly ONE follow-up question in JSON format based on this conversation:
            {context}
            
            Rules:
            1. Question should explore: skills, education, experience, or preferences
            2. MUST use this format:
            {{
                "id": "gen_[number]",
                "text": "Your question here?",
                "type": "mcq/multi_select",
                "options": ["A", "B"]  // for mcq/multi_select
            }}
            3. Make it sound natural like a counsellor"""
            
            response = self.model.generate_content(prompt)
            response_text = response.text.strip()
            
           
            if response_text.startswith('```json'):
                response_text = response_text[7:-3].strip()
            
            question = json.loads(response_text)
            
            
            if not any(keyword in question['text'].lower() for keyword in ['skill', 'educat', 'experien', 'prefer', 'work', 'like']):
                question['text'] = "What skills would you like to develop further?"
            
            return question
        
        except Exception:
            return self._get_fallback_question(user_responses)

    def _build_conversation_context(self, user_responses: Dict) -> str:
        """Build context string from user responses"""
        lines = []
        for qid, ans in user_responses.items():
            q_text = self.basic_questions.get(qid, {}).get('text', qid)
            lines.append(f"Q: {q_text}\nA: {ans}")
        return "\n".join(lines) if lines else "No prior responses"

    def _get_fallback_question(self, user_responses: Dict) -> Dict:
        """Returns counselling-style questions based on conversation flow"""
        
        
        if not user_responses:
            return self.questions_data['start']
        
        answered_questions = len(user_responses)
        
        
        if answered_questions == 1:
            interest = user_responses.get('q1', '').lower()
            if 'tech' in interest:
                return {
                    "id": "q2_tech",
                    "text": "Which technical skills do you have experience with?",
                    "type": "multi_select",
                    "options": self.questions_data['metadata']['skill_areas']['technical']
                }
            elif 'creative' in interest:
                return {
                    "id": "q2_creative",
                    "text": "Which creative skills best describe you?",
                    "type": "multi_select",
                    "options": self.questions_data['metadata']['skill_areas']['creative']
                }
            else:
                return {
                    "id": "q2_general",
                    "text": "What are your strongest skills?",
                    "type": "multi_select",
                    "options": [
                        "Communication", "Problem Solving", 
                        "Leadership", "Analytical Thinking"
                    ]
                }
        
        
        elif answered_questions == 2:
            return {
                "id": "q3_edu",
                "text": "What is your highest education level?",
                "type": "mcq",
                "options": self.questions_data['metadata']['education_levels']
            }
        
       
        elif answered_questions == 3:
            return {
                "id": "q4_exp",
                "text": "How many years of relevant experience do you have?",
                "type": "mcq",
                "options": [
                    "No experience", 
                    "1-3 years", 
                    "4-6 years", 
                    "7+ years"
                ]
            }
        
       
        elif answered_questions == 4:
            return {
                "id": "q5_pref",
                "text": "What work environment do you prefer?",
                "type": "mcq",
                "options": [
                    "Office setting",
                    "Remote work",
                    "Hybrid (office + remote)",
                    "Field/on-site work"
                ]
            }
        
       
        return {
            "id": "q_final",
            "text": "Any specific certifications or specializations?",
            "type": "text"
        }

    def generate_recommendations(self, user_responses: Dict) -> List[Dict]:
        """Generate personalized job recommendations with error handling"""
        if not user_responses:
            return []
        
        try:
            profile_text = self._create_user_profile(user_responses)
            user_embedding = self._get_embedding(profile_text)
            
            recommendations = []
            for job in self.jobs:
                try:
                    similarity = self._calculate_job_match(job, user_embedding, user_responses)
                    recommendations.append({
                        **job,
                        'match_score': similarity,
                        'match_reason': self._get_match_reason(job, user_responses)
                    })
                except Exception as e:
                    logging.error(f"Error processing job {job['id']}: {str(e)}")
                    continue
            
            return sorted(recommendations, key=lambda x: x['match_score'], reverse=True)[:10]
        
        except Exception as e:
            logging.error(f"Recommendation generation failed: {str(e)}")
            return []

    def _calculate_job_match(self, job: Dict, user_embedding: List[float], user_responses: Dict) -> float:
        """Calculate job match score (0-100) with weighted factors"""
        try:
            
            similarity = self._cosine_similarity(user_embedding, self.job_embeddings[job['id']]) * 70
            
            
            if user_responses.get('q1', '').lower() == job['industry'].lower():
                similarity += 15
            
           
            user_skills = [
                v.lower() for v in user_responses.values() 
                if isinstance(v, str)
            ] + [
                item.lower() for sublist in user_responses.values() 
                if isinstance(sublist, list) for item in sublist
            ]
            
            job_skills = [s.lower() for s in job.get('skills', [])]
            skill_match = len(set(user_skills) & set(job_skills))
            similarity += min(15, skill_match * 3)
            
            return min(100, round(similarity, 1))
        
        except Exception as e:
            logging.error(f"Match calculation error for job {job['id']}: {str(e)}")
            return 0.0

    def _get_match_reason(self, job: Dict, user_responses: Dict) -> str:
        """Generate explanation for job match"""
        reasons = []
        
      
        if user_responses.get('q1', '').lower() == job['industry'].lower():
            reasons.append(f"Matches your interest in {job['industry']}")
        
       
        user_skills = [
            v.lower() for v in user_responses.values() 
            if isinstance(v, str)
        ] + [
            item.lower() for sublist in user_responses.values() 
            if isinstance(sublist, list) for item in sublist
        ]
        
        common_skills = set(user_skills) & set(s.lower() for s in job.get('skills', []))
        if common_skills:
            reasons.append(f"Matches your skills: {', '.join(common_skills)}")
        
        return "; ".join(reasons) if reasons else "Good potential match"

    def _create_user_profile(self, user_responses: Dict) -> str:
        """Create text profile from responses"""
        profile = []
        for qid, ans in user_responses.items():
            q_text = self.basic_questions.get(qid, {}).get('text', qid)
            if isinstance(ans, list):
                profile.append(f"{q_text}: {', '.join(ans)}")
            else:
                profile.append(f"{q_text}: {ans}")
        return "\n".join(profile)

    def _cosine_similarity(self, a: List[float], b: List[float]) -> float:
        """Calculate cosine similarity between vectors"""
        try:
            return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
        except Exception as e:
            logging.error(f"Cosine similarity error: {str(e)}")
            return 0.0
