import streamlit as st
import pandas as pd
import numpy as np
import datetime

st.set_page_config(page_title="NourishNav Prototype", layout="wide")
st.title("🍎 NourishNav – Childhood Nutrition Tracker")

# --- Sidebar ---
page = st.sidebar.radio("Go to", ["Home", "Growth Tracking", "Feeding Log", "Milestones", "Reports"])

# --- Session State ---
if "growth_data" not in st.session_state:
    st.session_state.growth_data = pd.DataFrame(columns=["Date", "Age (months)", "Sex", "Weight (kg)", "Height (cm)", "Head Circ (cm)"])
if "feeding_log" not in st.session_state:
    st.session_state.feeding_log = pd.DataFrame(columns=["Date", "Feeding Type", "Food/Formula", "Amount"])
if "milestones" not in st.session_state:
    st.session_state.milestones = []

# --- Load WHO datasets ---
wfa_boys = pd.read_csv("wfa_boys_0-to-5-years_zscores.csv")
wfa_boys.rename(columns={wfa_boys.columns[0]: "Age (months)"}, inplace=True)

wfa_girls = pd.read_csv("wfa_girls_0-to-5-years_zscores.csv")
wfa_girls.rename(columns={wfa_girls.columns[0]: "Age (months)"}, inplace=True)

lfa_boys = pd.read_csv("lfa_boys_0-to-5-years_zscores.csv")
lfa_boys.rename(columns={lfa_boys.columns[0]: "Age (months)"}, inplace=True)

lfa_girls = pd.read_csv("lfa_girls_0-to-5-years_zscores.csv")
lfa_girls.rename(columns={lfa_girls.columns[0]: "Age (months)"}, inplace=True)

wfl_boys = pd.read_csv("wfl_boys_0-to-5-years_zscores.csv")
wfl_boys.rename(columns={wfl_boys.columns[0]: "Length (cm)"}, inplace=True)

wfl_girls = pd.read_csv("wfl_girls_0-to-5-years_zscores.csv")
wfl_girls.rename(columns={wfl_girls.columns[0]: "Length (cm)"}, inplace=True)



# --- Z-score function ---
def compute_zscore(x, L, M, S):
    if L != 0:
        return (((x / M) ** L) - 1) / (L * S)
    else:
        return np.log(x / M) / S


# --- Classification functions ---
def classify_weight_for_age(age, sex, weight):
    ref = wfa_boys if sex == "Boy" else wfa_girls
    ref_row = ref.iloc[(ref["Age (months)"] - age).abs().argsort()[:1]]
    z = compute_zscore(weight, ref_row["L"].values[0], ref_row["M"].values[0], ref_row["S"].values[0])
    return "Underweight" if z < -2 else "Normal", z

def classify_length_for_age(age, sex, height):
    ref = lfa_boys if sex == "Boy" else lfa_girls
    ref_row = ref.iloc[(ref["Age (months)"] - age).abs().argsort()[:1]]
    z = compute_zscore(height, ref_row["L"].values[0], ref_row["M"].values[0], ref_row["S"].values[0])
    return "Stunted" if z < -2 else "Normal", z

def classify_weight_for_length(length, sex, weight):
    ref = wfl_boys if sex == "Boy" else wfl_girls
    ref_row = ref.iloc[(ref["Length (cm)"] - length).abs().argsort()[:1]]
    z = compute_zscore(weight, ref_row["L"].values[0], ref_row["M"].values[0], ref_row["S"].values[0])
    if z < -2:
        return "Wasted", z
    elif z > 2:
        return "Overweight", z
    else:
        return "Normal", z


# --- Pages ---
if page == "Home":
    st.subheader("Welcome to NourishNav Prototype")
    st.markdown("""
    - 📈 Growth Tracking with WHO classifications  
    - 🍲 Feeding & Diet Logging  
    - 🧒 Milestone Tracking  
    - 📊 Reports with WHO-based nutrition status  
    """)

elif page == "Growth Tracking":
    st.subheader("Growth Tracking")
    date = st.date_input("Date", datetime.date.today())
    age = st.number_input("Age (months)", 0, 24, 0)
    sex = st.selectbox("Sex", ["Boy", "Girl"])
    weight = st.number_input("Weight (kg)", 0.0, 25.0, 3.0)
    height = st.number_input("Height (cm)", 40.0, 110.0, 50.0)
    head = st.number_input("Head Circumference (cm)", 0.0, 60.0, 35.0)

    if st.button("Add Record"):
        st.session_state.growth_data = pd.concat([
            st.session_state.growth_data,
            pd.DataFrame([[date, age, sex, weight, height, head]], columns=st.session_state.growth_data.columns)
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
    st.subheader("📊 Growth Classification Report")
    if st.session_state.growth_data.empty:
        st.warning("No growth data yet. Add some records first.")
    else:
        latest = st.session_state.growth_data.iloc[-1]
        st.write("### Latest Growth Record")
        st.json(latest.to_dict())

        # Run classifications
        underweight, z_wfa = classify_weight_for_age(latest["Age (months)"], latest["Sex"], latest["Weight (kg)"])
        stunted, z_lfa = classify_length_for_age(latest["Age (months)"], latest["Sex"], latest["Height (cm)"])
        wasting_status, z_wfl = classify_weight_for_length(latest["Height (cm)"], latest["Sex"], latest["Weight (kg)"])

        # Display results
        st.write("### WHO-based Growth Classification")
        if underweight == "Underweight":
            st.error(f"⚠️ {underweight} (Weight-for-Age Z = {z_wfa:.2f})")
        else:
            st.success(f"✅ Normal (Weight-for-Age Z = {z_wfa:.2f})")

        if stunted == "Stunted":
            st.error(f"⚠️ {stunted} (Length-for-Age Z = {z_lfa:.2f})")
        else:
            st.success(f"✅ Normal (Length-for-Age Z = {z_lfa:.2f})")

        if wasting_status == "Wasted":
            st.error(f"⚠️ {wasting_status} (Weight-for-Length Z = {z_wfl:.2f})")
        elif wasting_status == "Overweight":
            st.warning(f"⚠️ {wasting_status} (Weight-for-Length Z = {z_wfl:.2f})")
        else:
            st.success(f"✅ Normal (Weight-for-Length Z = {z_wfl:.2f})")


