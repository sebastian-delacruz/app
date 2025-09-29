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
st.write("### Caretaker Recommendations")

# --- Underweight (Weight-for-Age) ---
if underweight == "Underweight":
    if z_wfa < -3:
        st.error("**Severe Underweight (WFA Z < -3):** Child is severely underweight. Seek immediate medical care. Provide frequent feeding with calorie-dense and fortified foods under medical guidance.")
    else:
        st.warning("**Moderate Underweight (WFA -3 < Z < -2):** Child is moderately underweight. Ensure frequent meals, introduce calorie-dense foods (e.g., full-fat dairy, eggs, fortified meals), and monitor closely.")

# --- Stunted (Length-for-Age) ---
if stunted == "Stunted":
    if z_lfa < -3:
        st.error("**Severe Stunting (LFA Z < -3):** Height-for-age is severely low. Prioritize high-quality nutrition and seek professional assessment. Provide animal-source foods daily and continue responsive caregiving.")
    else:
        st.warning("**Moderate Stunting (LFA -3 < Z < -2):** Child is shorter than expected. Improve dietary diversity, ensure regular feeding, and promote early stimulation and play.")

# --- Wasted / Overweight (Weight-for-Length) ---
if wasting_status == "Wasted":
    if z_wfl < -3:
        st.error("**Severe Wasting (WFL Z < -3):** Severe acute malnutrition. Seek urgent medical treatment immediately (possible hospitalization).")
    else:
        st.warning("**Moderate Wasting (WFL -3 < Z < -2):** Thin for height. Provide energy-dense meals, therapeutic or supplementary foods as advised, and monitor for infections.")

elif wasting_status == "Overweight":
    if z_wfl > 3:
        st.error("**Obese (WFL Z > +3):** High risk of complications. Strictly avoid sugary drinks and fried foods. Encourage vegetables, fruits, whole grains, and daily physical activity.")
    else:
        st.warning("**Overweight (WFL +2 < Z < +3):** At risk of obesity. Limit processed snacks and encourage active play and family-wide healthy eating.")

# --- Normal (all three are normal) ---
if underweight == "Normal" and stunted == "Normal" and wasting_status == "Normal":
    st.success("**Normal Growth:** Continue exclusive breastfeeding (0–6 months), then diverse complementary feeding. Encourage physical activity, avoid added sugars, and maintain regular health check-ups.")

st.write("### General Recommendations for Caretakers")

st.markdown("""
-  **Feeding Practices**
  - Exclusive breastfeeding for the first 6 months.
  - At 6 months, introduce diverse and age-appropriate complementary foods while continuing breastfeeding up to 2 years or beyond.

-  **Nutrition**
  - Ensure dietary diversity: grains, fruits, vegetables, legumes, animal-source foods.
  - Limit sugary drinks, ultra-processed foods, and added salt.

-  **Health Monitoring**
  - Regular growth monitoring (weight & height every month up to 2 years).
  - Keep up with immunizations and regular pediatric check-ups.

-  **Care & Activity**
  - Encourage daily active play and interaction.
  - Ensure safe, responsive caregiving and adequate sleep.

-  **Hygiene & Safety**
  - Practice handwashing with soap before feeding.
  - Provide safe drinking water and clean food preparation areas.
""")


