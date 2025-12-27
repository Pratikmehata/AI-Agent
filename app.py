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

# ============================================
# CONFIGURATION
# ============================================
app = Flask(__name__)
CORS(app)

# Simple logging for Railway
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
MODEL_NAME = os.environ.get("MODEL_NAME", "gemini-1.5-flash")
TEMPERATURE = float(os.environ.get("TEMPERATURE", 0.7))
MAX_TOKENS = int(os.environ.get("MAX_TOKENS", 3000))
PORT = int(os.environ.get("PORT", 5000))

# Initialize model globally
gemini_model = None
DEMO_MODE = False

def setup_gemini():
    """Setup Gemini API"""
    global gemini_model, DEMO_MODE
    
    if not GOOGLE_API_KEY:
        logger.warning("GOOGLE_API_KEY not found. Running in demo mode.")
        DEMO_MODE = True
        return
    
    try:
        genai.configure(api_key=GOOGLE_API_KEY)
        logger.info("✅ Google Gemini API configured")
        
        # Try to initialize model
        try:
            gemini_model = genai.GenerativeModel(MODEL_NAME)
            logger.info(f"✅ Using model: {MODEL_NAME}")
            DEMO_MODE = False
        except Exception as e:
            logger.error(f"⚠️ Model error: {e}")
            logger.info("🔧 Trying fallback models...")
            
            # Try fallback models
            fallback_models = [
                "gemini-1.5-flash",
                "gemini-1.5-pro",
                "gemini-1.0-pro"
            ]
            
            for model_name in fallback_models:
                try:
                    gemini_model = genai.GenerativeModel(model_name)
                    logger.info(f"✅ Using fallback model: {model_name}")
                    DEMO_MODE = False
                    break
                except:
                    continue
            
            if gemini_model is None:
                logger.error("❌ No working model found. Using demo mode.")
                DEMO_MODE = True
                
    except Exception as e:
        logger.error(f"❌ Gemini setup failed: {e}")
        DEMO_MODE = True

# Initialize Gemini
setup_gemini()

# ============================================
# HELPER FUNCTIONS
# ============================================
def get_gemini_response(prompt, temperature=TEMPERATURE):
    """Get response from Gemini API"""
    if DEMO_MODE or gemini_model is None:
        logger.info("📱 DEMO MODE: Simulating response")
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
        return """# 🎯 3-Month Learning Roadmap

## 📅 **Month 1: Foundation Building**
### **Week 1-2: Core Fundamentals**
- Python programming
- Data analysis basics
- **Project:** Basic analysis

### **Week 3-4: Machine Learning Intro**
- Supervised learning
- Model evaluation
- **Project:** Predictive model

## **Month 2: Core Development**
### **Week 5-8: Advanced Topics**
- Neural networks
- Deep learning basics
- **Project:** Image classifier

## **Month 3: Production**
### **Week 9-12: Deployment**
- Model deployment
- Docker basics
- **Capstone:** Complete project"""
    
    else:
        return f"""# 🌟 Your Learning Journey

## 🎯 Welcome!
This roadmap guides you from current skills to job-ready professional.

## 📊 **Timeline**
- **Week 4:** Foundation complete
- **Week 8:** Portfolio ready
- **Week 12:** Interview prep

## 🚀 **Next Steps**
1. Set up environment
2. Start learning materials
3. Build projects

**Consistency beats intensity! 🎯**"""

# ============================================
# AI AGENTS WORKFLOW
# ============================================
def market_analyst_agent(career_goal, current_skills):
    """Market Analyst: Identify required skills and trends"""
    logger.info(f"📈 Analyzing: {career_goal}")
    
    prompt = f"""Analyze job market for {career_goal}. Skills: {current_skills}.
    
Provide analysis with:
1. Top technical skills needed
2. Key soft skills
3. Salary expectations
4. Growth opportunities
    
Format: Clear bullet points."""
    
    response = get_gemini_response(prompt, temperature=0.5)
    return response

def curriculum_designer_agent(career_goal, current_skills, learning_style, market_analysis):
    """Curriculum Designer: Create structured learning plan"""
    logger.info(f"📚 Planning for: {career_goal}")
    
    prompt = f"""Create 12-week learning plan for {career_goal}.
    
Skills: {current_skills}
Style: {learning_style}
    
Design roadmap with:
- Weekly objectives
- Resources
- Practice exercises
- Projects
    
Format in Markdown."""
    
    response = get_gemini_response(prompt, temperature=0.7)
    return response

def chief_strategist_agent(career_goal, learning_plan):
    """Chief Strategist: Format final plan"""
    logger.info(f"🎯 Finalizing: {career_goal}")
    
    prompt = f"""Transform this into inspiring roadmap for {career_goal}:
    
{learning_plan}
    
Add motivation and clear milestones."""
    
    response = get_gemini_response(prompt, temperature=0.6)
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
    
    if not career_goal:
        return jsonify({"error": "Please enter a career goal"}), 400
    
    def generate_stream():
        try:
            yield "data: 🤖 Step 1/3: Analyzing market trends...\n\n"
            market_analysis = market_analyst_agent(career_goal, current_skills)
            yield "data: ✅ Market analysis complete!\n\n"
            time.sleep(0.5)
            
            yield "data: 📚 Step 2/3: Creating learning plan...\n\n"
            learning_plan = curriculum_designer_agent(career_goal, current_skills, learning_style, market_analysis)
            yield "data: ✅ Learning plan structured!\n\n"
            time.sleep(0.5)
            
            yield "data: 🎯 Step 3/3: Finalizing roadmap...\n\n"
            final_output = chief_strategist_agent(career_goal, learning_plan)
            html_output = markdown2.markdown(final_output, extras=['fenced-code-blocks', 'tables'])
            
            result_html = f"""
            <div style="text-align: center; margin-bottom: 30px;">
                <h2 style="color: #f59e0b;">🚀 Your AI-Powered Learning Roadmap</h2>
                <p style="color: #cbd5e1;">Target: <strong>{career_goal}</strong></p>
                <div style="margin-top: 10px; padding: 6px 12px; background: rgba(99, 102, 241, 0.2); border-radius: 20px; display: inline-block;">
                    <span style="color: #cbd5e1; font-size: 0.9rem;">
                        <i class="fas fa-robot"></i> {'DEMO MODE' if DEMO_MODE else 'LIVE AI'}
                    </span>
                </div>
            </div>
            <div style="background: rgba(255,255,255,0.05); padding: 30px; border-radius: 10px;">
                {html_output}
            </div>
            <div style="margin-top: 30px; text-align: center;">
                <a href="/" style="padding: 12px 24px; border-radius: 8px; background: #4f46e5; color: white; text-decoration: none;">
                    ← Create Another Plan
                </a>
            </div>
            """
            
            yield f"result: {json.dumps(result_html)}\n\n"
            
        except Exception as e:
            logger.error(f"Generation error: {e}")
            yield f"data: ERROR: {str(e)}\n\n"
    
    return Response(generate_stream(), mimetype='text/event-stream')

@app.route('/health')
def health():
    return jsonify({
        "status": "healthy",
        "model": MODEL_NAME,
        "mode": "demo" if DEMO_MODE else "live",
        "timestamp": datetime.now().isoformat()
    })

# ============================================
# STARTUP
# ============================================
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    
    print("\n" + "="*50)
    print("🚀 EDU-RECOMMENDER")
    print("="*50)
    print(f"🌐 http://0.0.0.0:{port}")
    print(f"🤖 Model: {MODEL_NAME}")
    print(f"🔧 Mode: {'DEMO' if DEMO_MODE else 'LIVE'}")
    print("="*50)
    
    app.run(host='0.0.0.0', port=port, debug=False)
