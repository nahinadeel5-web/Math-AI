import os
import json
import base64
import io
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from google import genai
from google.genai import types
from PIL import Image

# Initialize Flask and unlock cross-origin sharing so your web page can talk to your AI cleanly
app = Flask(__name__)
CORS(app)

# 🔑 Safe API Key Retrieval Engine (looks at your old secrets file fallback automatically)
API_KEY = None
secrets_path = os.path.join(".streamlit", "secrets.toml")

if os.path.exists(secrets_path):
    with open(secrets_path, "r") as f:
        for line in f:
            if "API_KEY" in line:
                API_KEY = line.split("=")[-1].replace('"', '').replace("'", "").strip()

if not API_KEY:
    # Fallback to standard environment variables if secrets file is blank
    API_KEY = os.environ.get("API_KEY", "")

client = genai.Client(api_key=API_KEY)

# =========================================================================
# 📝 1. MULTI-SUBJECT AI TUTORS ROUTE
# =========================================================================
@app.route("/api/tutor", methods=["POST"])
def consult_tutor():
    data = request.json or {}
    subject = data.get("subject", "Mathematics")
    user_query = data.get("query", "")
    image_b64 = data.get("image", None) # Catches sketch drawings effortlessly
    
    system_prompts = {
        "Mathematics": "You are an expert Math Professor. Show every algebraic step clearly, list formulas, and highlight the final answer.",
        "Biology": "You are a Biology Professor. Explain life sciences, cell structures, anatomy, and ecosystems using clear formatting and clear bullet points.",
        "Chemistry": "You are a Chemistry Professor. Explain chemical reactions, periodic tables, atomic structures, and balancing equations cleanly.",
        "Physics": "You are a Physics Professor. Explain mechanics, forces, thermodynamics, and energy. List the core equations and physics laws clearly.",
        "History": "You are a History Professor. Explain global historical events, key dates, figures, causes, and effects using clear structured timelines.",
        "Geography": "You are a Geography Professor. Explain earth structures, climates, map concepts, demographics, and geology simply.",
        "English": "You are an English Literature & Grammar Professor. Help students analyze essays, understand grammar rules, poetic devices, and sentence structures.",
        "Computer Science": "You are an expert Coding & Computer Science Instructor. Explain algorithms, data structures, and provide clean, commented Python/Java/HTML code blocks."
    }

    try:
        payload = []
        if user_query:
            payload.append(user_query)
            
        if image_b64:
            if "," in image_b64:
                image_b64 = image_b64.split(",")[-1]
            img_bytes = base64.b64decode(image_b64)
            img_obj = Image.open(io.BytesIO(img_bytes))
            payload.append(img_obj)
            if not user_query:
                payload.append("Analyze this study diagram and explain it thoroughly.")

        if not payload:
            return jsonify({"error": "Empty query payload"}), 400

        response = client.models.generate_content(
            model='gemini-3.5-flash-lite',
            contents=payload,
            config=types.GenerateContentConfig(system_instruction=system_prompts.get(subject, ""))
        )
        return jsonify({"reply": response.text})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# =========================================================================
# 🎮 2. SMART QUIZ ARENA GENERATOR ROUTE
# =========================================================================
@app.route("/api/quiz", methods=["POST"])
def generate_quiz():
    data = request.json or {}
    subject = data.get("subject", "Mathematics")
    num_questions = data.get("num_questions", 3)
    difficulty = data.get("difficulty", "Beginner Level")
    source_material = data.get("source_material", "")

    try:
        base_prompt = f"Generate a multiple-choice quiz with exactly {num_questions} questions targeting {subject} at an {difficulty} proficiency level."
        if source_material:
            base_prompt += f"\n\nCRITICAL: Base questions strictly on this material:\n{source_material}"
        base_prompt += '\nOutput a valid JSON list of objects with "question", "options" (list of 4), and "correct" (string matching the right option) keys. Do not wrap in markdown backticks.'
        
        response = client.models.generate_content(
            model='gemini-3.5-flash-lite',
            contents=base_prompt,
            config=types.GenerateContentConfig(response_mime_type="application/json")
        )
        return jsonify(json.loads(response.text))
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 🏠 Core route rendering our web shell dashboard template sheet
@app.route("/")
def home():
    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True, port=5000)
