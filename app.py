# Simple SaaS Login Logic
st.sidebar.title("🔐 User Access")
user_email = st.sidebar.text_input("Enter Email to access your stats")

if not user_email:
    st.warning("Please enter your email in the sidebar to start tracking.")
    st.stop() # This stops the rest of the app from running until they type an email

# Now, update your Supabase save logic to include the email
data = {
    "user_id": user_email, # This links the data to the specific person
    "weight": w, 
    "body_fat": bf,
    # ... other metrics
}


import streamlit as st
import google.generativeai as genai
from supabase import create_client

# --- CREDENTIALS ---
GEMINI_KEY = "AIzaSyAJBpU17seAb-QnW8AmIiB5hs6IdLFLrpw"
SUPABASE_URL = "https://xxqrcppczwukedofueqt.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inh4cXJjcHBjend1a2Vkb2Z1ZXF0Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzE4OTcyNzYsImV4cCI6MjA4NzQ3MzI3Nn0.dsBf9SU2VYt-Ed545EaBA6tSkY2kN5tT9kRo-7PijBU"

# Setup
genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

st.title("🏋️‍♂️ AI Trainer with Memory")

# Inputs
w = st.number_input("Weight (kg)", value=70.0)
bf = st.number_input("Body Fat %", value=20.0)
smm = st.number_input("Skeletal Muscle (kg)", value=30.0)
v_fat = st.number_input("Visceral Fat", value=5)
notes = st.text_area("Notes")

if st.button("Analyze & Save Progress"):
    # 1. SAVE to Database
    data = {
        "weight": w, "body_fat": bf, "muscle_mass": smm, 
        "visceral_fat": v_fat, "notes": notes
    }
    supabase.table("metrics").insert(data).execute()
    
    # 2. FETCH Previous Entry for Comparison
    previous = supabase.table("metrics").select("*").order("created_at", desc=True).limit(2).execute()
    
    # 3. CONSTRUCT TREND LOGIC
    if len(previous.data) > 1:
        last_week = previous.data[1]
        diff_w = w - last_week['weight']
        trend = f"Last week I was {last_week['weight']}kg. I am now {w}kg (Change: {diff_w}kg)."
    else:
        trend = "This is my first entry."

    # 4. SEND TO AI
    prompt = f"Compare my progress: {trend}. Current stats: {data}. Provide a plan."
    response = model.generate_content(prompt)
    
    st.success("Stats Saved to Cloud!")
    st.write(response.text)
