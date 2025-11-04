import streamlit as st
import pandas as pd
import numpy as np
import datetime

st.set_page_config(page_title="NourishNav Prototype", layout="wide")
st.title("NourishNav: Childhood Nutrition Tracker 🍎")

# --- TOWS STRATEGY INTEGRATION ---

# OW Strategy: Multi-profile Tracking
# Stores a list of children and the currently selected child's name
if "children_profiles" not in st.session_state:
    # Use a descriptive placeholder profile that cannot be used for data entry
    st.session_state.children_profiles = {"Select/Create Profile": pd.DataFrame(columns=["Date", "Age (months)", "Sex", "Weight (kg)", "Height (cm)", "Head Circ (cm)"])}
    st.session_state.current_child = "Select/Create Profile"

# --- Sidebar ---
st.sidebar.header("Active Child Profile")

# Dropdown to select existing child
child_names = list(st.session_state.children_profiles.keys())
selected_child = st.sidebar.selectbox("Profile", child_names, index=child_names.index(st.session_state.current_child))

# Update the session state with the selected child
st.session_state.current_child = selected_child

# Check if the current child is the placeholder
is_placeholder_profile = st.session_state.current_child == "Select/Create Profile"
if is_placeholder_profile:
    st.sidebar.warning("Go to Profile Manager to create a new profile.")

st.sidebar.markdown("---")
# Set "Profile Manager" as the default landing page
page = st.sidebar.radio("Go to", ["Profile Manager", "Growth Tracking", "Reports", "Help & FAQ"])

# Retrieve the growth data for the current child
if st.session_state.current_child not in st.session_state.children_profiles:
     # Fallback for safety
     st.session_state.current_child = child_names[0] if child_names else "Select/Create Profile"

current_growth_data = st.session_state.children_profiles[st.session_state.current_child]


# --- Load WHO datasets (Simulated - assuming files exist) ---
try:
    # NOTE: In a real environment, you'd ensure these files are available.
    # Placeholder for file loading, assuming files are available
    @st.cache_data
    def load_who_data():
        try:
            wfa_boys = pd.read_excel("wfa_boys_0-to-5-years_zscores.xlsx").rename(columns={0: "Age (months)"})
            wfa_girls = pd.read_excel("wfa_girls_0-to-5-years_zscores.xlsx").rename(columns={0: "Age (months)"})
            lhfa_boys = pd.read_excel("lhfa_boys_0-to-2-years_zscores.xlsx").rename(columns={0: "Age (months)"})
            lhfa_girls = pd.read_excel("lhfa_girls_0-to-2-years_zscores.xlsx").rename(columns={0: "Age (months)"})
            wfl_boys = pd.read_excel("wfl_boys_0-to-2-years_zscores.xlsx").rename(columns={0: "Length (cm)"})
            wfl_girls = pd.read_excel("wfl_girls_0-to-2-years_zscores.xlsx").rename(columns={0: "Length (cm)"})
            
            return wfa_boys, wfa_girls, lhfa_boys, lhfa_girls, wfl_boys, wfl_girls
        except FileNotFoundError:
            return None, None, None, None, None, None

    data_files = load_who_data()
    if all(df is None for df in data_files):
        st.error("Error: WHO growth standards files not found. The application will not function.")
        st.stop()
    else:
        wfa_boys, wfa_girls, lhfa_boys, lhfa_girls, wfl_boys, wfl_girls = data_files


except Exception as e:
    st.error(f"Error loading WHO data: {e}")
    st.stop()


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

# --- Profile Management Functions ---

def create_profile(name):
    name_stripped = name.strip()
    if not name_stripped:
        st.error("Profile name cannot be empty. Please enter a valid name.")
        return False
    elif name_stripped in st.session_state.children_profiles:
        st.error(f"Profile '{name_stripped}' already exists. Please choose a different name.")
        return False
    else:
        st.session_state.children_profiles[name_stripped] = pd.DataFrame(
            columns=["Date", "Age (months)", "Sex", "Weight (kg)", "Height (cm)", "Head Circ (cm)"]
        )
        st.session_state.current_child = name_stripped
        st.success(f"Profile for **{name_stripped}** created and set as active!")
        st.rerun()
        return True

def delete_profile(name):
    if name in st.session_state.children_profiles and name != "Select/Create Profile":
        del st.session_state.children_profiles[name]
        # Switch to the placeholder profile after deletion
        st.session_state.current_child = "Select/Create Profile"
        st.warning(f"Profile for **{name}** deleted.")
        st.rerun()

# --- Pages ---

if page == "Profile Manager":
    st.header("Profile Manager: Create, Select, or Delete Profiles")
    st.markdown("---")
    
    col_create, col_spacer = st.columns([1, 2])
    
    with col_create:
        st.subheader("➕ Create New Profile")
        new_child_name = st.text_input("Child's Name", key="new_profile_input", placeholder="E.g., Baby Juan, Maria")
        if st.button("Create and Set Active"):
            create_profile(new_child_name)
    
    st.markdown("---")
    st.subheader("Active Profiles")
    
    valid_profiles = [name for name in st.session_state.children_profiles if name != "Select/Create Profile"]
    
    if not valid_profiles:
        st.info("No active profiles yet. Use the section above to create your first child's profile!")
    else:
        st.markdown(f"**Currently Active:** {st.session_state.current_child}")
        
        for name in valid_profiles:
            col_name, col_records, col_switch, col_delete = st.columns([2, 1, 1, 1])
            
            records_count = len(st.session_state.children_profiles[name])
            
            with col_name:
                st.write(f"**{name}**")
            with col_records:
                st.markdown(f"*{records_count} record{'s' if records_count != 1 else ''}*")
            with col_switch:
                if st.button("Set Active", key=f"switch_{name}"):
                    st.session_state.current_child = name
                    st.success(f"**{name}** is now the active profile.")
                    st.rerun()
            with col_delete:
                if st.button("Delete", key=f"delete_{name}"):
                    delete_profile(name)
    
    
elif page == "Growth Tracking":
    if is_placeholder_profile:
        st.warning("⚠️ Please select or create a child profile in the **Profile Manager** before tracking growth.")
        st.stop()
        
    st.header(f"📈 Growth Tracking for **{st.session_state.current_child}**")

    # If the child profile is new, use default. If data exists, use latest data for initial input guess
    if not current_growth_data.empty:
        latest_record = current_growth_data.iloc[-1]
        default_age = latest_record["Age (months)"]
        default_sex = latest_record["Sex"]
        default_weight = latest_record["Weight (kg)"]
        default_height = latest_record["Height (cm)"]
        default_head = latest_record["Head Circ (cm)"]
    else:
        default_age = 0
        default_sex = "Boy"
        default_weight = 3.0
        default_height = 50.0
        default_head = 35.0

    col1, col2, col3 = st.columns(3)
    with col1:
        date = st.date_input("Date of Measurement", datetime.date.today())
    with col2:
        age = st.number_input("Age (months)", 0, 24, int(default_age))
    with col3:
        sex = st.selectbox("Sex", ["Boy", "Girl"], index=["Boy", "Girl"].index(default_sex))

    col4, col5, col6 = st.columns(3)
    with col4:
        weight = st.number_input("Weight (kg)", 0.0, 25.0, default_weight, help="Weight for Age (WFA) is calculated using this.")
    with col5:
        height = st.number_input("Length/Height (cm)", 40.0, 110.0, default_height, help="Length/Height for Age (LFA) is calculated using this.")
    with col6:
        head = st.number_input("Head Circumference (cm)", 0.0, 60.0, default_head)

    if st.button("➕ Add Growth Record"):
        if (date, age) in zip(current_growth_data["Date"], current_growth_data["Age (months)"]):
            st.error("A record for this date/age already exists. Please choose a different date or age.")
        else:
            new_record = pd.DataFrame([[date, age, sex, weight, height, head]], columns=current_growth_data.columns)
            st.session_state.children_profiles[st.session_state.current_child] = pd.concat([
                current_growth_data,
                new_record
            ], ignore_index=True)
            st.session_state.children_profiles[st.session_state.current_child] = st.session_state.children_profiles[st.session_state.current_child].sort_values(by="Date").reset_index(drop=True)
            st.success("Growth record added successfully!")
            st.rerun() # Rerun to refresh the chart/data table

    st.markdown("---")
    st.write(f"### Data for {st.session_state.current_child}")
    st.dataframe(current_growth_data)

    # TW Strategy: Progress Charts for Retention
    if not current_growth_data.empty:
        st.write("### 📈 Growth Trends")
        chart_data = current_growth_data.set_index("Date")[["Weight (kg)", "Height (cm)"]]
        st.line_chart(chart_data)


elif page == "Reports":
    if is_placeholder_profile:
        st.warning("⚠️ Please select or create a child profile in the **Profile Manager** before generating reports.")
        st.stop()
        
    st.header(f"📊 Growth Classification Report for **{st.session_state.current_child}**")

    if current_growth_data.empty:
        st.warning("No growth data yet. Add some records first to generate a report.")
    else:
        latest = current_growth_data.iloc[-1]
        st.info(f"Report based on latest record from **{latest['Date'].strftime('%B %d, %Y')}** (Age: {latest['Age (months)']} months)")

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
        st.markdown("---")
        st.write("### WHO-based Growth Classification")

        # Use an f-string for clearer display of classification and Z-score (TS Strategy: Credibility and Clarity)
        st.markdown(f"""
        - **Weight for Age (WFA):** {'❗ **Underweight**' if underweight=='Underweight' else '✅ Normal'} (Z = {z_wfa:.2f})
        - **Length/Height for Age (LFA/HFA):** {'❗ **Stunted**' if stunted=='Stunted' else '✅ Normal'} (Z = {z_lfa:.2f})
        - **Weight for Length/Height (WFL/H):** {
            '❗ **Wasted**' if wasting_status == 'Wasted' else
            ('⚠️ **Overweight**' if wasting_status == 'Overweight' else '✅ Normal')
        } (Z = {z_wfl:.2f})
        """)
        st.markdown("---")

        # --- Caretaker Recommendations ---
        st.write("### Caretaker Recommendations")

        # TW Strategy: Retention/Reminders (Added Z-score threshold for tailored advice)
        if underweight == "Underweight":
            if z_wfa < -3:
                st.error("**Severe Underweight (WFA Z < -3):** Seek immediate medical care, frequent feeding with calorie-dense fortified foods. **Action Reminder:** Schedule a medical check-up this week.")
            else:
                st.warning("**Moderate Underweight (WFA -3 < Z < -2):** Ensure frequent calorie-dense meals, monitor closely. **Action Reminder:** Track weight again in 2 weeks.")
        # Stunting
        if stunted == "Stunted":
            if z_lfa < -3:
                st.error("**Severe Stunting (LFA Z < -3):** Very short for age. Prioritize high-quality nutrition and seek professional assessment. **Action Reminder:** Consult a Pediatrician/Nutritionist immediately.")
            else:
                st.warning("**Moderate Stunting (LFA -3 < Z < -2):** Improve dietary diversity and stimulation. **Action Reminder:** Review your child's meal plan for protein and micronutrients.")
        # Wasting / Overweight
        if wasting_status == "Wasted":
            if z_wfl < -3:
                st.error("**Severe Wasting (WFL Z < -3):** Urgent medical care required. **Action Reminder:** Seek emergency help now.")
            else:
                st.warning("**Moderate Wasting (WFL -3 < Z < -2):** Provide energy-dense foods, therapeutic feeding as advised. **Action Reminder:** Check if therapeutic food is available from a local health center.")
        elif wasting_status == "Overweight":
            if z_wfl > 3:
                st.error("**Obese (WFL Z > +3):** Avoid sugary drinks & fried foods. Encourage healthy diet and activity. **Action Reminder:** Create a daily activity schedule and track sugary food intake.")
            else:
                st.warning("**Overweight (WFL +2 < Z < +3):** Limit snacks, promote active play. **Action Reminder:** Replace one daily snack with a fruit or vegetable.")
        # Normal
        if underweight == "Normal" and stunted == "Normal" and wasting_status == "Normal":
            st.success("**Normal Growth:** Continue breastfeeding, diverse diet, safe feeding, active play, and regular health checkups. **Action Reminder:** Keep up the great work and schedule your next monitoring session!")

        st.markdown("---")
        # OS Strategy: General Recommendations (Can be expanded with localized meal plans)
        st.write("### General Recommendations for Caretakers")
        st.markdown("""
        - **Feeding:** Exclusive breastfeeding for 6 months, then diverse complementary foods.
        - **Nutrition:** Mix grains, fruits, vegetables, proteins. Limit sugary/processed foods.
        - **Health:** **Monthly growth monitoring**, routine immunizations, check-ups.
        - **Activity:** Daily play and responsive caregiving.
        - **Hygiene:** Wash hands before feeding, provide safe drinking water.
        """)

elif page == "Help & FAQ":
    # OW Strategy: Comprehensive Help Center/FAQ section for improved accessibility and usability.
    st.header("Help Center & Frequently Asked Questions")

    st.markdown("---")
    st.subheader("What is NourishNav?")
    st.markdown("""
    NourishNav is a childhood nutrition tracker that uses **WHO Growth Standards** to classify your child's growth status, providing immediate, actionable recommendations.
    """)

    st.subheader("How is the Classification Calculated?")
    with st.expander("Expand to learn more about Z-Scores"):
        st.markdown("""
        The app uses the World Health Organization (WHO) standards to calculate Z-scores (standard deviations from the median).
        - **Weight-for-Age (WFA):** Indicates Underweight. Z-score below -2 is 'Underweight'.
        - **Length/Height-for-Age (LFA/HFA):** Indicates Stunting. Z-score below -2 is 'Stunted'.
        - **Weight-for-Length/Height (WFL/H):** Indicates Wasting or Overweight. Z-score below -2 is 'Wasted', and Z-score above +2 is 'Overweight'.
        This method is the global standard for assessing child growth.
        """)

    st.subheader("Multi-Profile Tracking")
    st.markdown("""
    You can track multiple children or manage profiles for different families (useful for health workers). Use the **Profile Manager** page to create, switch, and delete profiles.
    """)

    st.subheader("Data Privacy")
    with st.expander("Expand to learn about our Privacy Policy"):
        st.markdown("""
        **Your Data Security is our Priority.** All data you input is stored locally within this application's session and is not transmitted externally. We adhere to clear protocols to ensure your information remains private and secure.
        """)
    st.markdown("---")
    st.warning("⚠️ **Reminder:** This is a prototype and not a substitute for professional medical advice. Always consult a healthcare professional for diagnosis and treatment.")


