import streamlit as st
import google.generativeai as genai
from supabase import create_client
from PIL import Image
import pandas as pd

# 1. CREDENTIALS (Secure these in Streamlit Cloud Secrets later)
GEMINI_KEY = st.secrets["GEMINI_KEY"]
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

# Setup Clients
genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel('gemini-1.5-flash-latest')
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

st.set_page_config(page_title="AI Body Trainer Pro", layout="wide")

# 2. LOGIN SYSTEM
st.sidebar.title("🔐 User Access")
user_email = st.sidebar.text_input("Enter Email to access profile")

if not user_email:
    st.header("Welcome to your AI Trainer")
    st.info("Enter your email in the sidebar to load your metrics and history.")
    st.stop()

# 3. GUI: THE 13 METRIC INPUTS
st.title(f"📊 Dashboard for {user_email}")

with st.form("weekly_audit"):
    st.subheader("Weekly Body Composition Scan")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        w = st.number_input("Weight (kg)", 30.0, 250.0, 75.0)
        bmi = st.number_input("BMI", 10.0, 50.0, 22.0)
        bf = st.number_input("Body Fat %", 3.0, 50.0, 15.0)
        smm = st.number_input("Skeletal Muscle (kg)", 10.0, 100.0, 35.0)
        ffm = st.number_input("Fat Free Mass (kg)", 30.0, 200.0, 60.0)

    with col2:
        mm = st.number_input("Muscle Mass (kg)", 10.0, 100.0, 55.0)
        bone = st.number_input("Bone Mass (kg)", 1.0, 10.0, 3.0)
        prot = st.number_input("Protein %", 5.0, 30.0, 18.0)
        s_fat = st.number_input("Subcutaneous Fat %", 3.0, 50.0, 12.0)

    with col3:
        v_fat = st.number_input("Visceral Fat Level", 1, 20, 5)
        water = st.number_input("Body Water %", 30.0, 80.0, 55.0)
        bmr = st.number_input("BMR (kcal)", 500, 5000, 1700)
        m_age = st.number_input("Metabolic Age", 10, 100, 25)

    notes = st.text_area("Notes: Describe your energy levels, sleep, and training performance this week.")
    img_file = st.file_uploader("Upload Progress Photo", type=["jpg", "png", "jpeg"])
    
    submit = st.form_submit_button("Sync Data & Generate AI Plan")

# 4. DATA PROCESSING
if submit:
    # A. Map inputs to the exact Database Column Names
    new_data = {
        "user_email": user_email,
        "weight": w, "bmi": bmi, "body_fat": bf, "skeletal_muscle": smm, "ffm": ffm,
        "muscle_mass": mm, "bone_mass": bone, "protein": prot, "sub_fat": s_fat,
        "visc_fat": v_fat, "body_water": water, "bmr": bmr, "metabolic_age": m_age,
        "notes": notes
    }

    try:
        # B. Push to Supabase
        supabase.table("metrics").insert(new_data).execute()
        st.success("Week data saved successfully!")

        # C. Fetch previous data for the AI to compare
        history_response = supabase.table("metrics").select("*").eq("user_email", user_email).order("created_at", desc=True).limit(2).execute()
        history = history_response.data

        # D. AI Context Building
        trend_context = ""
        if len(history) > 1:
            prev = history[1]
            diff = w - prev['weight']
            trend_context = f"Last week weight: {prev['weight']}kg. Current: {w}kg. Change: {diff}kg."
        else:
            trend_context = "This is the first entry. Establish a baseline."

        # E. AI Coach Logic
        prompt = f"""
        You are a Master AI Sports Scientist.
        User Email: {user_email}
        Recent Trend: {trend_context}
        Current 13-Metric Scan: {new_data}
        
        Analyze the relationship between Skeletal Muscle, Body Water, and Visceral Fat.
        If Muscle is dropping while Weight drops, warn about catabolism.
        If Visceral Fat is high (>10), suggest specific dietary fiber and cardio tweaks.
        
        Provide:
        1. BIOLOGICAL AUDIT: What do the numbers say?
        2. NUTRITION PLAN: Specific macro/calorie adjustments.
        3. TRAINING TWEAK: What to change in the gym this week.
        """

        with st.spinner("Analyzing metabolic data..."):
            if img_file:
                image = Image.open(img_file)
                response = model.generate_content([prompt, image])
            else:
                response = model.generate_content(prompt)
            
            st.divider()
            st.subheader("📋 Your Personalized AI Protocol")
            st.write(response.text)

    except Exception as e:
        st.error(f"Error syncing with database: {e}")

# 5. VISUAL PROGRESS
if user_email:
    st.divider()
    st.subheader("📉 Your Journey Over Time")
    prog_resp = supabase.table("metrics").select("created_at", "weight", "muscle_mass", "body_fat").eq("user_email", user_email).order("created_at").execute()
    
    if prog_resp.data:
        df = pd.DataFrame(prog_resp.data)
        st.line_chart(df.set_index('created_at')[['weight', 'muscle_mass', 'body_fat']])
