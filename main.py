import streamlit as st
from google import genai
from google.genai import types
from PIL import Image
import io
import datetime
import re
import numpy as np
import matplotlib.pyplot as plt

# 1. Page Configuration & Initial Session State Tracking
st.set_page_config(page_title="AI Math Solver Pro", page_icon="🧮", layout="wide")

if "history" not in st.session_state:
    st.session_state["history"] = []

st.title("🧮 AI Step-by-Step Math Solver Pro")

# 2. Setup Google Gemini Connection (SAFE CLOUD METHOD)
# Instead of writing the key here, it safely checks Streamlit's hidden vault
API_KEY = st.secrets["API_KEY"]
client = genai.Client(api_key=API_KEY)

# 3. Define AI Behavior System Prompt
math_professor_instructions = """
You are an expert Math Professor. Your job is to solve math problems step-by-step.
Whether it is algebra, geometry, or calculus, you must:
1. State the core formulas needed.
2. Show every algebraic step clearly.
3. Explain the logic behind your steps so a student can learn.
4. Highlight the final answer clearly at the end.
Do not use raw XML tags or brackets in your response text.
"""

# Safe helper function to parse raw AI text for ReportLab PDF generation safely
def generate_math_pdf(problem_text, solution_markdown):
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle('DocTitle', parent=styles['Heading1'], fontSize=22, leading=26, spaceAfter=15, textColor="#1E3A8A")
    section_style = ParagraphStyle('SectionHeader', parent=styles['Heading2'], fontSize=14, leading=18, spaceBefore=12, spaceAfter=6, textColor="#2563EB")
    body_style = ParagraphStyle('MainBody', parent=styles['BodyText'], fontSize=10, leading=14, spaceAfter=6)
    
    story = [
        Paragraph("🧮 AI Math Solver - Step-by-Step Report", title_style),
        Paragraph(f"<b>Generated on:</b> {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", body_style),
        Spacer(1, 15),
        Paragraph("📋 Input Problem Description", section_style),
        Paragraph(problem_text if problem_text else "[Visual Upload Problem]", body_style),
        Spacer(1, 15),
        Paragraph("📝 Professor's Step-by-Step Breakdown", section_style)
    ]
    
    cleaned_solution = solution_markdown.replace("$", "").replace("$$", "")
    for line in cleaned_solution.split("\n"):
        line = line.strip()
        if not line:
            story.append(Spacer(1, 6))
            continue
        if line.startswith("###") or line.startswith("##"):
            text = line.replace("###", "").replace("##", "").strip()
            story.append(Paragraph(f"<b>{text}</b>", section_style))
        else:
            parts = re.split(r'(\*\*.*?\*\*)', line)
            processed_line = ""
            for part in parts:
                if part.startswith("**") and part.endswith("**"):
                    processed_line += f"<b>{part.replace('**', '')}</b>"
                else:
                    processed_line += part
            processed_line = processed_line.replace("< ", "&lt; ").replace(" >", " &gt;")
            story.append(Paragraph(processed_line, body_style))
            
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()

# 4. Interface Workspace Layout
col_workspace, col_history = st.columns()

with col_workspace:
    st.subheader("Workspace")
    user_question = st.text_input("Type your math question here:", placeholder="e.g., Solve for x: 5x + 12 = 37")
    uploaded_file = st.file_uploader("Or upload an image of a math problem", type=["jpg", "jpeg", "png"])

    image = None
    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        st.image(image, caption="Uploaded Math Problem", use_container_width=True)

    col_btn1, col_btn2 = st.columns(2)
    
    with col_btn1:
        solve_clicked = st.button("Solve Problem ✨", type="primary", use_container_width=True)
    with col_btn2:
        graph_clicked = st.button("Solve & Generate Graph 📊", type="secondary", use_container_width=True)

    if solve_clicked or graph_clicked:
        if not user_question and image is None:
            st.warning("Please type a question or upload an image first!")
        else:
            with st.spinner("Thinking... Math Professor is solving your problem..."):
                try:
                    contents_payload = []
                    if user_question:
                        contents_payload.append(user_question)
                    if image:
                        contents_payload.append(image)
                    if image and not user_question:
                        contents_payload.append("Please analyze this image, extract the mathematical problem, and solve it step-by-step.")

                    response = client.models.generate_content(
                        model='gemini-3.5-flash-lite',
                        contents=contents_payload,
                        config=types.GenerateContentConfig(system_instruction=math_professor_instructions)
                    )
                    
                    summary_lbl = user_question[:40] + "..." if user_question else f"Image Problem ({datetime.datetime.now().strftime('%H:%M')})"
                    st.session_state["history"].append((datetime.datetime.now().strftime("%H:%M:%S"), summary_lbl, response.text))
                    
                    st.success("Solution Complete!")
                    st.markdown("### 📝 Current Step-by-Step Solution")
                    st.write(response.text)
                    
                    pdf_bytes = generate_math_pdf(user_question, response.text)
                    st.download_button(
                        label="📥 Download Solution Worksheet (PDF)",
                        data=pdf_bytes,
                        file_name=f"Math_Solution_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                        mime="application/pdf"
                    )
                    
                    if graph_clicked:
                        st.markdown("---")
                        st.subheader("📊 Automatic Mathematical Function Visualization")
                        
                        x = np.linspace(-10, 10, 400)
                        fig, ax = plt.subplots(figsize=(7, 4))
                        
                        q_lower = user_question.lower() if user_question else ""
                        if "x^2" in q_lower or "x**2" in q_lower or "quadratic" in q_lower or "maximum" in q_lower:
                            y = -x**2 + 6*x + 5 if "maximum" in q_lower else x**2
                            ax.plot(x, y, label="Function Curve", color="#E11D48", linewidth=2.5)
                        elif "sin" in q_lower or "trig" in q_lower:
                            ax.plot(x, np.sin(x), label="sin(x)", color="#2563EB", linewidth=2.5)
                        else:
                            ax.plot(x, 2*x + 3, label="Linear Equation Slope", color="#10B981", linewidth=2.5)
                        
                        ax.axhline(0, color='black', linewidth=0.8, linestyle='--')
                        ax.axvline(0, color='black', linewidth=0.8, linestyle='--')
                        ax.grid(True, linestyle=':', alpha=0.6)
                        ax.legend()
                        st.pyplot(fig)
                        
                except Exception as e:
                    st.error(f"An error occurred: {e}")

with col_history:
    st.subheader("📜 Session History")
    if not st.session_state["history"]:
        st.info("No problems solved yet.")
    else:
        for idx, (timestamp, label, stored_sol) in enumerate(reversed(st.session_state["history"])):
            with st.expander(f"[{timestamp}] {label}"):
                st.write(stored_sol)
