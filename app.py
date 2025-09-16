import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import datetime

st.set_page_config(page_title="NourishNav Prototype", layout="wide")

st.title("🍎 NourishNav – Childhood Nutrition Tracker")

# --- Sidebar for navigation ---
page = st.sidebar.radio("Go to", ["Home", "Growth Tracking", "Feeding Log", "Milestones", "Reports"])

# --- Session storage ---
if "growth_data" not in st.session_state:
    st.session_state.growth_data = pd.DataFrame(columns=["Date", "Weight (kg)", "Height (cm)", "Head Circ (cm)"])

if "feeding_log" not in st.session_state:
    st.session_state.feeding_log = pd.DataFrame(columns=["Date", "Feeding Type", "Food/Formula", "Amount"])

if "milestones" not in st.session_state:
    st.session_state.milestones = []

# --- Pages ---
if page == "Home":
    st.subheader("Welcome to NourishNav Prototype")
    st.write("This prototype demonstrates the core features of NourishNav:")
    st.markdown("""
    - 📈 **Growth Tracking** (weight, height, head circumference with charts)  
    - 🍲 **Feeding & Diet Logging** (breastfeeding, formula, solids)  
    - 🧒 **Milestone Tracking** (motor, speech, social development)  
    - 📊 **Reports & Recommendations**  
    """)

elif page == "Growth Tracking":
    st.subheader("Growth Tracking")
    date = st.date_input("Date", datetime.date.today())
    weight = st.number_input("Weight (kg)", 0.0, 50.0, 8.0)
    height = st.number_input("Height (cm)", 0.0, 120.0, 70.0)
    head = st.number_input("Head Circumference (cm)", 0.0, 60.0, 45.0)

    if st.button("Add Record"):
        st.session_state.growth_data = pd.concat([
            st.session_state.growth_data,
            pd.DataFrame([[date, weight, height, head]], columns=st.session_state.growth_data.columns)
        ], ignore_index=True)

    st.write("### Growth Data")
    st.dataframe(st.session_state.growth_data)

    if not st.session_state.growth_data.empty:
        st.line_chart(st.session_state.growth_data.set_index("Date")[["Weight (kg)", "Height (cm)"]])

elif page == "Feeding Log":
    st.subheader("Feeding & Diet Log")
    date = st.date_input("Date", datetime.date.today())
    ftype = st.selectbox("Feeding Type", ["Breastfeeding", "Formula", "Solid Food"])
    food = st.text_input("Food / Formula")
    amount = st.text_input("Amount (ml / g)")

    if st.button("Log Feeding"):
        st.session_state.feeding_log = pd.concat([
            st.session_state.feeding_log,
            pd.DataFrame([[date, ftype, food, amount]], columns=st.session_state.feeding_log.columns)
        ], ignore_index=True)

    st.write("### Feeding Records")
    st.dataframe(st.session_state.feeding_log)

elif page == "Milestones":
    st.subheader("Milestone Tracking")
    milestone = st.text_input("Enter new milestone (e.g., First words, Crawling)")
    if st.button("Add Milestone"):
        st.session_state.milestones.append((datetime.date.today(), milestone))

    st.write("### Milestone Records")
    for date, m in st.session_state.milestones:
        st.write(f"✅ {date}: {m}")

elif page == "Reports":
    st.subheader("📊 Progress Reports & Recommendations")
    if st.session_state.growth_data.empty:
        st.warning("No growth data yet. Add some records first.")
    else:
        latest = st.session_state.growth_data.iloc[-1]
        st.write("### Latest Growth Record")
        st.json(latest.to_dict())

        # Simple recommendations (placeholder for WHO growth reference)
        if latest["Weight (kg)"] < 8:
            st.error("⚠️ Weight is below typical range. Consider consulting a pediatrician.")
        else:
            st.success("✅ Growth appears within a healthy range.")

        st.write("More advanced analysis could compare against WHO Child Growth Standards.")
