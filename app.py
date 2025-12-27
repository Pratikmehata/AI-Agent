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
# PRODUCTION CONFIGURATION FOR RAILWAY
# ============================================
app = Flask(__name__)
CORS(app)

# Production settings
app.config.update(
    SECRET_KEY=os.environ.get("FLASK_SECRET_KEY", os.urandom(24)),
    SESSION_COOKIE_SECURE=True,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
    MAX_CONTENT_LENGTH=16 * 1024 * 1024,
)

# Configure logging for Railway
if os.environ.get("RAILWAY_ENVIRONMENT"):
    # Railway logs to stdout
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        handlers=[logging.StreamHandler()]
    )
else:
    # Local development logging
    logging.basicConfig(level=logging.DEBUG)

logger = logging.getLogger(__name__)

# ============================================
# CONFIGURATION VARIABLES
# ============================================
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
MODEL_NAME = os.environ.get("MODEL_NAME", "gemini-1.5-flash")
TEMPERATURE = float(os.environ.get("TEMPERATURE", 0.7))
MAX_TOKENS = int(os.environ.get("MAX_TOKENS", 3000))
PORT = int(os.environ.get("PORT", 5000))
APP_ENV = os.environ.get("RAILWAY_ENVIRONMENT", "development")

# ============================================
# API SETUP WITH RAILWAY-OPTIMIZED FALLBACK
# ============================================
def setup_gemini():
    """Setup Gemini API with Railway-optimized fallback"""
    if not GOOGLE_API_KEY:
        logger.warning("GOOGLE_API_KEY not found. Running in demo mode.")
        return None, True
    
    try:
        genai.configure(api_key=GOOGLE_API_KEY)
        logger.info("✅ Google Gemini API configured")
        
        # Try available models (Railway optimized)
        models_to_try = [
            MODEL_NAME,
            "gemini-1.5-flash",  # Most reliable for production
            "gemini-1.5-pro",
            "gemini-1.0-pro",
            "models/gemini-pro"
        ]
        
        for model_name in models_to_try:
            try:
                logger.info(f"🔧 Testing model: {model_name}")
                model = genai.GenerativeModel(model_name)
                # Quick test with timeout for Railway
                test_response = model.generate_content(
                    "Hello",
                    request_options={"timeout": 5}
                )
                logger.info(f"✅ Using model: {model_name}")
                return model, False
            except Exception as e:
                logger.debug(f"Model {model_name} not available: {str(e)[:80]}")
                continue
        
        logger.error("❌ No working model found. Using demo mode.")
        return None, True
        
    except Exception as e:
        logger.error(f"❌ Gemini setup failed: {e}")
        return None, True

# Initialize Gemini
gemini_model, DEMO_MODE = setup_gemini()

# ============================================
# HELPER FUNCTIONS (KEEP FROM ORIGINAL)
# ============================================
def get_gemini_response(prompt, temperature=TEMPERATURE):
    """Get response from Gemini API with Railway timeout"""
    if DEMO_MODE or gemini_model is None:
        logger.info("DEMO MODE: Simulating API response")
        time.sleep(0.5)
        return get_demo_response(prompt)
    
    try:
        # Add timeout for Railway environment
        response = gemini_model.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(
                temperature=temperature,
                max_output_tokens=MAX_TOKENS,
                top_p=0.95,
                top_k=40
            ),
            request_options={"timeout": 30}  # 30-second timeout for Railway
        )
        return response.text
    except Exception as e:
        logger.error(f"⚠️ Gemini API Error: {e}")
        return get_demo_response(prompt)

# Keep your existing get_demo_response() function unchanged
def get_demo_response(prompt):
    """Generate demo responses when API is unavailable"""
    # ... (keep your existing demo response code exactly as is)

# Keep your existing agent functions unchanged:
# market_analyst_agent(), curriculum_designer_agent(), chief_strategist_agent()

# ============================================
# RAILWAY-OPTIMIZED ROUTES
# ============================================
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate():
    """Generate learning roadmap with Railway-optimized streaming"""
    # Input validation
    career_goal = request.form.get('career_goal', '').strip()
    current_skills = request.form.get('current_skills', '').strip()
    learning_style = request.form.get('learning_style', 'balanced').strip()
    
    if not career_goal:
        def error_stream():
            yield "data: ERROR: Please enter a career goal\n\n"
        return Response(error_stream(), mimetype='text/event-stream')
    
    def generate_stream(career_goal, current_skills, learning_style):
        try:
            # Step 1: Market Analysis
            yield "data: 🤖 Step 1/3: Market Analyst analyzing trends...\n\n"
            market_analysis = market_analyst_agent(career_goal, current_skills)
            yield "data: ✅ Market analysis complete!\n\n"
            time.sleep(0.3)
            
            # Step 2: Curriculum Design
            yield "data: 📚 Step 2/3: Curriculum Designer creating plan...\n\n"
            learning_plan = curriculum_designer_agent(career_goal, current_skills, learning_style, market_analysis)
            yield "data: ✅ Learning plan structured!\n\n"
            time.sleep(0.3)
            
            # Step 3: Final Strategy
            yield "data: 🎯 Step 3/3: Chief Strategist finalizing...\n\n"
            final_output = chief_strategist_agent(career_goal, learning_plan)
            html_output = markdown2.markdown(final_output, extras=['fenced-code-blocks', 'tables'])
            
            # Build result HTML
            result_html = f"""
            <div class="result-header">
                <div style="text-align: center; margin-bottom: 30px;">
                    <h2 style="color: #f59e0b; margin-bottom: 10px;">🚀 Your AI-Powered Learning Roadmap</h2>
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
            logger.error(f"Generation error: {e}")
            yield f"data: ERROR: An error occurred while generating your roadmap. Please try again.\n\n"
    
    return Response(
        generate_stream(career_goal, current_skills, learning_style),
        mimetype='text/event-stream'
    )

@app.route('/health')
def health():
    """Health check endpoint for Railway monitoring"""
    return jsonify({
        "status": "healthy",
        "service": "edu-recommender",
        "environment": APP_ENV,
        "model": MODEL_NAME,
        "mode": "demo" if DEMO_MODE else "live",
        "timestamp": datetime.now().isoformat()
    })

@app.route('/status')
def status():
    """Status endpoint for Railway health checks"""
    return jsonify({
        "status": "operational",
        "version": "1.0.0",
        "uptime": time.time() - app_start_time if 'app_start_time' in globals() else 0
    })

# Initialize app start time
app_start_time = time.time()

# ============================================
# RAILWAY STARTUP
# ============================================
if __name__ == '__main__':
    # Railway provides PORT environment variable
    port = int(os.environ.get("PORT", 5000))
    host = "0.0.0.0"  # Important for Railway
    
    print("\n" + "="*60)
    print("🚀 EDU-RECOMMENDER DEPLOYED ON RAILWAY")
    print("="*60)
    print(f"\n🌐 Server starting on: http://{host}:{port}")
    print(f"🤖 Model: {MODEL_NAME}")
    print(f"🔧 Mode: {'DEMO' if DEMO_MODE else 'LIVE'}")
    print(f"🏷️  Environment: {APP_ENV}")
    
    if DEMO_MODE:
        print("\n⚠️  Running in DEMO MODE")
        print("   To enable AI features, add GOOGLE_API_KEY to Railway variables")
    else:
        print(f"\n✅ AI System Ready!")
    
    print("\n📡 Health Check Endpoint:")
    print(f"   http://{host}:{port}/health")
    print("\n" + "="*60)
    
    # Production server (no debug/reloader)
    app.run(host=host, port=port, debug=False)
