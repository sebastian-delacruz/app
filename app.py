import streamlit as st
import pandas as pd
import numpy as np
import datetime

st.set_page_config(page_title="NourishNav Prototype", layout="wide")
st.title("NourishNav: Childhood Nutrition Tracker 🍎")

# --- Sidebar ---
page = st.sidebar.radio("Go to", ["Growth Tracking", "Reports"])

# --- Session State ---
if "growth_data" not in st.session_state:
    st.session_state.growth_data = pd.DataFrame(
        columns=["Date", "Age (months)", "Sex", "Weight (kg)", "Height (cm)", "Head Circ (cm)"]
    )

# --- Load WHO datasets ---
wfa_boys = pd.read_excel("wfa_boys_0-to-5-years_zscores.xlsx")
wfa_girls = pd.read_excel("wfa_girls_0-to-5-years_zscores.xlsx")
lhfa_boys = pd.read_excel("lhfa_boys_0-to-2-years_zscores.xlsx")
lhfa_girls = pd.read_excel("lhfa_girls_0-to-2-years_zscores.xlsx")
wfl_boys = pd.read_excel("wfl_boys_0-to-2-years_zscores.xlsx")
wfl_girls = pd.read_excel("wfl_girls_0-to-2-years_zscores.xlsx")

# Rename first column
wfa_boys.rename(columns={wfa_boys.columns[0]: "Age (months)"}, inplace=True)
wfa_girls.rename(columns={wfa_girls.columns[0]: "Age (months)"}, inplace=True)
lhfa_boys.rename(columns={lhfa_boys.columns[0]: "Age (months)"}, inplace=True)
lhfa_girls.rename(columns={lhfa_girls.columns[0]: "Age (months)"}, inplace=True)
wfl_boys.rename(columns={wfl_boys.columns[0]: "Length (cm)"}, inplace=True)
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
    ref = lhfa_boys if sex == "Boy" else lhfa_girls
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
if page == "Growth Tracking":
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

elif page == "Reports":
    st.subheader("📊 Growth Classification Report")

    if st.session_state.growth_data.empty:
        st.warning("No growth data yet. Add some records first.")
    else:
        latest = st.session_state.growth_data.iloc[-1]

        # --- Run classifications ---
        underweight, z_wfa = classify_weight_for_age(
            latest["Age (months)"], latest["Sex"], latest["Weight (kg)"]
        )
        stunted, z_lfa = classify_length_for_age(
            latest["Age (months)"], latest["Sex"], latest["Height (cm)"]
        )
        wasting_status, z_wfl = classify_weight_for_length(
            latest["Height (cm)"], latest["Sex"], latest["Weight (kg)"]
        )

        # --- Display results ---
        st.write("### WHO-based Growth Classification")
        st.markdown(f"**Weight:** {'❗ Underweight' if underweight=='Underweight' else '✅ Normal'} (Z = {z_wfa:.2f})")
        st.markdown(f"**Height:** {'❗ Stunted' if stunted=='Stunted' else '✅ Normal'} (Z = {z_lfa:.2f})")
        if wasting_status == "Wasted":
            st.markdown(f"**Weight vs Height:** ❗ Wasted (Z = {z_wfl:.2f})")
        elif wasting_status == "Overweight":
            st.markdown(f"**Weight vs Height:** ⚠️ Overweight (Z = {z_wfl:.2f})")
        else:
            st.markdown(f"**Weight vs Height:** ✅ Normal (Z = {z_wfl:.2f})")

        # --- Caretaker Recommendations (now variables are defined) ---
        st.write("### Caretaker Recommendations")

        # Underweight
        if underweight == "Underweight":
            if z_wfa < -3:
                st.error("**Severe Underweight (WFA Z < -3):** Seek immediate medical care, frequent feeding with calorie-dense fortified foods.")
            else:
                st.warning("**Moderate Underweight (WFA -3 < Z < -2):** Ensure frequent calorie-dense meals, monitor closely.")

        # Stunting
        if stunted == "Stunted":
            if z_lfa < -3:
                st.error("**Severe Stunting (LFA Z < -3):** Very short for age. Prioritize high-quality nutrition and seek professional assessment.")
            else:
                st.warning("**Moderate Stunting (LFA -3 < Z < -2):** Improve dietary diversity and stimulation.")

        # Wasting / Overweight
        if wasting_status == "Wasted":
            if z_wfl < -3:
                st.error("**Severe Wasting (WFL Z < -3):** Urgent medical care required.")
            else:
                st.warning("**Moderate Wasting (WFL -3 < Z < -2):** Provide energy-dense foods, therapeutic feeding as advised.")
        elif wasting_status == "Overweight":
            if z_wfl > 3:
                st.error("**Obese (WFL Z > +3):** Avoid sugary drinks & fried foods. Encourage healthy diet and activity.")
            else:
                st.warning("**Overweight (WFL +2 < Z < +3):** Limit snacks, promote active play.")

        # Normal
        if underweight == "Normal" and stunted == "Normal" and wasting_status == "Normal":
            st.success("**Normal Growth:** Continue breastfeeding, diverse diet, safe feeding, active play, and regular health checkups.")

        # --- General Recommendations ---
        st.write("### General Recommendations for Caretakers")
        st.markdown("""
        - **Feeding:** Exclusive breastfeeding for 6 months, then diverse complementary foods.
        - **Nutrition:** Mix grains, fruits, vegetables, proteins. Limit sugary/processed foods.
        - **Health:** Monthly growth monitoring, routine immunizations, check-ups.
        - **Activity:** Daily play and responsive caregiving.
        - **Hygiene:** Wash hands before feeding, provide safe drinking water.
        """)



