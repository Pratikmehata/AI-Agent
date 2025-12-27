import os
import time
import json
from datetime import datetime
from flask import Flask, render_template, request, Response, jsonify
from flask_cors import CORS
import markdown2
import google.generativeai as genai
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================
# CONFIGURATION - UPDATED MODEL NAMES
# ============================================
app = Flask(__name__)
CORS(app)

# Get configuration from environment variables
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
# UPDATED: Use correct model name
MODEL_NAME = os.environ.get("MODEL_NAME", "gemini-2.5-flash")
SECRET_KEY = os.environ.get("FLASK_SECRET_KEY", os.urandom(24))
TEMPERATURE = float(os.environ.get("TEMPERATURE", 0.7))
MAX_TOKENS = int(os.environ.get("MAX_TOKENS", 3000))
PORT = int(os.environ.get("PORT", 5001))

# ============================================
# API SETUP WITH MODEL VALIDATION
# ============================================
def setup_gemini():
    """Setup Gemini API with proper model validation"""
    if not GOOGLE_API_KEY:
        logger.error("❌ GOOGLE_API_KEY not found in environment variables!")
        logger.error("   Please create a .env file with your API key")
        return None, True
    
    try:
        genai.configure(api_key=GOOGLE_API_KEY)
        logger.info("✅ Google Gemini API configured successfully")
        
        # Test the model
        try:
            model = genai.GenerativeModel(MODEL_NAME)
            # Quick test call
            test_response = model.generate_content("Hello")
            logger.info(f"✅ Model '{MODEL_NAME}' is available and working")
            return model, False
        except Exception as model_error:
            logger.error(f"⚠️ Model '{MODEL_NAME}' not available: {model_error}")
            
            # Try alternative models
            alternative_models = [
                "gemini-3-flash-preview",
                "gemini-1.0-pro",
                "gemini-pro",
                "models/gemini-1.5-pro-latest",  # Full path
                "models/gemini-pro"
            ]
            
            for alt_model in alternative_models:
                try:
                    logger.info(f"🔧 Trying alternative model: {alt_model}")
                    model = genai.GenerativeModel(alt_model)
                    test_response = model.generate_content("Hello")
                    logger.info(f"✅ Found working model: {alt_model}")
                    # Update MODEL_NAME
                    os.environ["MODEL_NAME"] = alt_model
                    return model, False
                except:
                    continue
            
            logger.error("❌ No working model found. Using demo mode.")
            return None, True
            
    except Exception as e:
        logger.error(f"❌ Failed to configure Gemini: {e}")
        return None, True

# Initialize Gemini
gemini_model, DEMO_MODE = setup_gemini()

app.secret_key = SECRET_KEY

# ============================================
# HELPER FUNCTIONS
# ============================================
def get_gemini_response(prompt, temperature=TEMPERATURE):
    """Get response from Gemini API"""
    if DEMO_MODE or gemini_model is None:
        logger.warning("DEMO MODE: Simulating API response")
        time.sleep(0.5)
        return get_demo_response(prompt)
    
    try:
        response = gemini_model.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(
                temperature=temperature,
                max_output_tokens=MAX_TOKENS,
                top_p=0.95,
                top_k=40
            )
        )
        return response.text
    except Exception as e:
        logger.error(f"⚠️ Gemini API Error: {e}")
        return get_demo_response(prompt)

def get_demo_response(prompt):
    """Generate demo responses when API is unavailable"""
    prompt_lower = prompt.lower()
    
    if "market analyst" in prompt_lower or "analyze" in prompt_lower:
        return """**Market Analysis for AI Engineer**

**Top Technical Skills:**
1. Python (Advanced)
2. Machine Learning & Deep Learning
3. TensorFlow/PyTorch
4. Data Analysis & Statistics
5. Cloud Platforms (AWS/Azure/GCP)
6. SQL & Databases
7. Docker & Kubernetes

**Essential Soft Skills:**
- Problem-solving
- Communication
- Critical thinking
- Team collaboration
- Adaptability

**Salary Ranges:**
- Entry: $90,000 - $120,000
- Mid: $120,000 - $180,000
- Senior: $180,000 - $300,000+

**Growth Outlook:**
- 30% annual job growth
- High demand across industries
- Remote work opportunities increasing"""
    
    elif "curriculum" in prompt_lower or "learning plan" in prompt_lower:
        return """# 🎯 3-Month AI Engineer Learning Roadmap

## 📅 **Month 1: Foundation Building**
### **Week 1-2: Python & Data Fundamentals**
- Advanced Python programming
- NumPy, Pandas, Matplotlib
- Data cleaning and preprocessing
- **Project:** Exploratory data analysis

### **Week 3-4: Machine Learning Basics**
- Supervised vs unsupervised learning
- Regression and classification
- Model evaluation metrics
- **Project:** Predictive modeling

## **Month 2: Core AI Development**
### **Week 5-8: Deep Learning & Neural Networks**
- Neural network fundamentals
- CNN for computer vision
- RNN/LSTM for sequences
- **Project:** Image classifier

## **Month 3: Specialization & Production**
### **Week 9-12: MLOps & Deployment**
- Model deployment strategies
- Docker containers
- CI/CD pipelines
- **Capstone:** End-to-end AI application

## 📚 **Learning Resources**
- Coursera: Machine Learning by Andrew Ng
- Fast.ai: Practical Deep Learning
- YouTube: FreeCodeCamp, Sentdex
- Books: "Hands-On Machine Learning"

## 🏆 **Portfolio Projects**
1. Stock price predictor
2. Image recognition app  
3. Chatbot with NLP
4. Recommendation system"""
    
    else:
        return f"""# 🌟 Your AI Learning Journey

## 🎯 Welcome to Your Career Transformation!
This roadmap guides you from your current skills to becoming a job-ready AI professional.

## 📊 **Achievement Timeline**
- **Week 4:** Foundation projects complete
- **Week 8:** Intermediate portfolio ready
- **Week 12:** Job interview preparation

## 💪 **Weekly Schedule Template**
**Monday-Thursday (Learning):**
- 7-9 PM: Core concepts & exercises
- 9-9:30 PM: Review & notes

**Friday (Practice):**
- 7-10 PM: Project development

**Saturday (Deep Work):**
- 10 AM - 2 PM: Major milestones

**Sunday (Planning):**
- 1 hour: Weekly review & planning

## 🚀 **Immediate Next Steps**
1. Set up Python environment
2. Install essential libraries
3. Join AI communities
4. Start Week 1 materials

**Remember:** Consistency beats intensity. Daily progress compounds into mastery! 🎯"""

# ============================================
# AI AGENTS WORKFLOW
# ============================================
def market_analyst_agent(career_goal, current_skills):
    """Market Analyst: Identify required skills and trends"""
    logger.info(f"📈 Market Analyst analyzing: {career_goal}")
    
    prompt = f"""Analyze the job market for {career_goal}. Current skills: {current_skills}.
    
Provide a concise analysis with:
1. Top 5-7 technical skills needed
2. Key soft skills
3. Salary expectations
4. Growth opportunities
    
Format: Clear bullet points."""
    
    response = get_gemini_response(prompt, temperature=0.5)
    logger.info("✅ Market analysis complete")
    return response

def curriculum_designer_agent(career_goal, current_skills, learning_style, market_analysis):
    """Curriculum Designer: Create structured learning plan"""
    logger.info(f"📚 Curriculum Designer planning for: {career_goal}")
    
    prompt = f"""Create a 12-week learning plan for {career_goal}.
    
Existing Skills: {current_skills}
Learning Style: {learning_style}
    
Design a practical roadmap with:
- Weekly learning objectives
- Recommended resources
- Practice exercises
- Weekly projects
    
Format in Markdown with clear sections."""
    
    response = get_gemini_response(prompt, temperature=0.7)
    logger.info("✅ Curriculum design complete")
    return response

def chief_strategist_agent(career_goal, learning_plan):
    """Chief Strategist: Format final plan with motivation"""
    logger.info(f"🎯 Chief Strategist finalizing: {career_goal}")
    
    prompt = f"""Transform this learning plan into an inspiring roadmap for {career_goal}:
    
{learning_plan}
    
Add:
1. Motivational introduction
2. Clear milestone markers  
3. Weekly schedule template
4. Success strategies
5. Encouraging conclusion
    
Use engaging Markdown with emojis."""
    
    response = get_gemini_response(prompt, temperature=0.6)
    logger.info("✅ Chief strategist complete")
    return response

# ============================================
# FLASK ROUTES
# ============================================
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate():
    career_goal = request.form.get('career_goal', '').strip()
    current_skills = request.form.get('current_skills', '').strip()
    learning_style = request.form.get('learning_style', 'balanced').strip()
    
    logger.info(f"📥 Request: {career_goal}")
    
    if not career_goal:
        def error_stream():
            yield "data: ERROR: Please enter a career goal\n\n"
        return Response(error_stream(), mimetype='text/event-stream')
    
    def generate_stream(career_goal, current_skills, learning_style):
        try:
            yield "data: 🤖 Step 1/3: Market Analyst analyzing trends...\n\n"
            time.sleep(0.5)
            
            market_analysis = market_analyst_agent(career_goal, current_skills)
            yield "data: ✅ Market analysis complete!\n\n"
            time.sleep(0.5)
            
            yield "data: 📚 Step 2/3: Curriculum Designer creating plan...\n\n"
            time.sleep(0.5)
            
            learning_plan = curriculum_designer_agent(career_goal, current_skills, learning_style, market_analysis)
            yield "data: ✅ Learning plan structured!\n\n"
            time.sleep(0.5)
            
            yield "data: 🎯 Step 3/3: Chief Strategist finalizing...\n\n"
            time.sleep(0.5)
            
            final_output = chief_strategist_agent(career_goal, learning_plan)
            html_output = markdown2.markdown(final_output, extras=['fenced-code-blocks', 'tables'])
            
            result_html = f"""
            <div class="result-header">
                <div style="text-align: center; margin-bottom: 30px;">
                    <i class="fas fa-rocket" style="font-size: 48px; color: #10b981; margin-bottom: 15px;"></i>
                    <h2 style="color: #f59e0b; margin-bottom: 10px;">Your AI-Powered Learning Roadmap</h2>
                    <p style="color: #cbd5e1; font-size: 1.1rem;">Target: <strong>{career_goal}</strong></p>
                    <div style="margin-top: 10px; padding: 6px 12px; background: rgba(99, 102, 241, 0.2); border-radius: 20px; display: inline-block;">
                        <span style="color: #cbd5e1; font-size: 0.9rem;">
                            <i class="fas fa-robot"></i> {'DEMO MODE' if DEMO_MODE else 'LIVE AI - ' + MODEL_NAME}
                        </span>
                    </div>
                </div>
            </div>
            <div class="result-card">
                <div class="roadmap-content">
                    {html_output}
                </div>
                <div style="margin-top: 40px; padding-top: 20px; border-top: 1px solid rgba(255,255,255,0.1); text-align: center;">
                    <a href="/" class="btn-secondary" style="display: inline-flex; align-items: center; gap: 8px; padding: 12px 24px; border-radius: 8px; background: #4f46e5; color: white; text-decoration: none; font-weight: 600;">
                        <i class="fas fa-arrow-left"></i> Create Another Plan
                    </a>
                </div>
            </div>
            """
            
            yield f"result: {json.dumps(result_html)}\n\n"
            
        except Exception as e:
            logger.error(f"❌ Generation error: {e}")
            yield f"data: ERROR: {str(e)}\n\n"
    
    return Response(
        generate_stream(career_goal, current_skills, learning_style),
        mimetype='text/event-stream'
    )

@app.route('/health')
def health():
    return jsonify({
        "status": "healthy",
        "service": "edu-recommender",
        "model": MODEL_NAME,
        "mode": "demo" if DEMO_MODE else "live",
        "timestamp": datetime.now().isoformat()
    })

@app.route('/models')
def list_models():
    """List available Gemini models"""
    try:
        if GOOGLE_API_KEY:
            genai.configure(api_key=GOOGLE_API_KEY)
            models = genai.list_models()
            model_names = [model.name for model in models]
            return jsonify({
                "success": True,
                "models": model_names,
                "count": len(model_names)
            })
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
    return jsonify({"message": "API key not configured"})

# ============================================
# MAIN EXECUTION
# ============================================
if __name__ == '__main__':
    print("\n" + "="*60)
    print("🚀 EDU-RECOMMENDER AI SYSTEM")
    print("="*60)
    print(f"\n🌐 URL: http://localhost:{PORT}/")
    print(f"🤖 Model: {MODEL_NAME}")
    print(f"🔧 Mode: {'DEMO' if DEMO_MODE else 'LIVE'}")
    
    if DEMO_MODE:
        print("\n⚠️  Running in DEMO MODE")
        print("   To enable AI features:")
        print("   1. Get API key: https://makersuite.google.com/app/apikey")
        print("   2. Add to .env: GOOGLE_API_KEY=your_key_here")
    else:
        print(f"\n✅ AI System Ready with model: {MODEL_NAME}")
    
    print("\n📡 Available Models Endpoint:")
    print(f"   http://localhost:{PORT}/models")
    print("\n" + "="*60)
    
    app.run(host='0.0.0.0', port=PORT, debug=True, use_reloader=False)