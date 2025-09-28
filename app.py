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

        # Run classifications
        underweight, z_wfa = classify_weight_for_age(latest["Age (months)"], latest["Sex"], latest["Weight (kg)"])
        stunted, z_lfa = classify_length_for_age(latest["Age (months)"], latest["Sex"], latest["Height (cm)"])
        wasting_status, z_wfl = classify_weight_for_length(latest["Height (cm)"], latest["Sex"], latest["Weight (kg)"])

        # Display results
        st.write("### WHO-based Growth Classification")

        if underweight == "Underweight":
            st.markdown(f"**Weight:** ❗ **{underweight}** (Z = {z_wfa:.2f})")
        else:
            st.markdown(f"**Weight:** ✅ **Normal** (Z = {z_wfa:.2f})")

        if stunted == "Stunted":
            st.markdown(f"**Height:** ❗ **{stunted}** (Z = {z_lfa:.2f})")
        else:
            st.markdown(f"**Height:** ✅ **Normal** (Z = {z_lfa:.2f})")

        if wasting_status == "Wasted":
            st.markdown(f"**Weight vs Height:** ❗ **{wasting_status}** (Z = {z_wfl:.2f})")
        elif wasting_status == "Overweight":
            st.markdown(f"**Weight vs Height:** ⚠️ **{wasting_status}** (Z = {z_wfl:.2f})")
        else:
            st.markdown(f"**Weight vs Height:** ✅ **Normal** (Z = {z_wfl:.2f})")

