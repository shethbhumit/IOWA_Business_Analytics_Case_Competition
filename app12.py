import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st

st.set_page_config(layout="wide")

#logo_path = '/Users/bhumitsheth/Documents/IOWA Case Study/File/ball-logo.jpeg'

col1, col2 = st.columns([1,9])
#with col1:
    #st.image(logo_path, width=100)  # Maybe some space if you want to adjust the position of the title
with col2:
    st.markdown("""
    <style>
    .title {
        display: flex;
        align-items: center;
        height: 100px;  # Adjust the height to match your logo's height
        margin: 0;
    }
    </style>
    <div class="title">
    <h1 style="margin:0;">Engagement Survey Analysis</h1>
    </div>
    """, unsafe_allow_html=True)

# Load datasets
engagement_survey_df = pd.read_csv('/Users/bhumitsheth/Documents/IOWA Case Study/File/2022 Engagement Survey.csv')
pulse_survey_df = pd.read_csv('/Users/bhumitsheth/Documents/IOWA Case Study/File/2023 Pulse Survey.csv')
ops_people_data_df = pd.read_csv('/Users/bhumitsheth/Documents/IOWA Case Study/File/Ops People Data.csv')
action_items_df = pd.read_csv('/Users/bhumitsheth/Documents/IOWA Case Study/File/Action Items.csv')


# Clean column names and convert 'Value' to numeric for Engagement Survey Data
def prepare_survey_data(df):
    df.columns = df.columns.str.strip()
    if 'Value' in df.columns:
        df['Value'] = pd.to_numeric(df['Value'], errors='coerce')
    if 'Plant' in df.columns:
        df['Plant'] = df['Plant'].apply(lambda x: f'Plant_{x}' if x.isdigit() else x)
    return df

# Apply data preparation to both surveys
engagement_survey_df = prepare_survey_data(engagement_survey_df)
pulse_survey_df = prepare_survey_data(pulse_survey_df)

# Selecting the survey type
survey_type = st.radio("Select Survey Type:", ("Engagement", "Pulse Survey"), key='survey_type')
selected_survey_df = engagement_survey_df if survey_type == "Engagement" else pulse_survey_df

# Ensure Ops People Data matches the formatting
ops_people_data_df.columns = ops_people_data_df.columns.str.strip()
ops_people_data_df['Plant'] = ops_people_data_df['Plant'].astype(str)

def get_top_questions_based_on_excess(survey_df, plant):
    # Ensure Plant 17 is treated like any other plant without special naming
    plant_id = "17" if plant == "Overall Company" else plant
    
    # Fetch questions for the selected plant
    plant_questions = survey_df[
        (survey_df['Plant'] == plant_id) & 
        (survey_df['Metric'] == 'Unfavourable') & 
        (survey_df['Question number'].astype(str) != '0')  # Ensure this condition is correctly applied
    ]
    
    # Fetch overall benchmark
    overall_benchmark = selected_survey_df[
        (selected_survey_df['Plant'] == 'Overall') & 
        (selected_survey_df['Metric'] == 'Unfavourable')
    ]
    
    # Merge plant-specific questions with the overall benchmark on 'Category' and 'Question number'
    comparison = pd.merge(plant_questions, overall_benchmark, on=['Category', 'Question number'], suffixes=('', '_benchmark'))
    
    # Calculate the difference (excess) over benchmark
    comparison['Excess'] = comparison['Value'] - comparison['Value_benchmark']
    
    # Filter questions where the score exceeds the benchmark
    exceeding_questions = comparison[comparison['Excess'] > 0]
    
    # Determine the top 3 categories based on total excess
    top_exceeding_questions = exceeding_questions.nlargest(5, 'Excess')

    # Select relevant columns for display
    final_display = top_exceeding_questions[['Category', 'Question', 'Value', 'Value_benchmark']]
    final_display.columns = ['Category', 'Specific Question', 'Unfavourable Score', 'Benchmark']
    
    return final_display



# Create plant_options dynamically from the data

plant_mapping = {f"Plant_{i}": f"Plant_{i}" for i in range(1, 17)}  # Including Plant 1 to Plant 17
plant_mapping["Overall Company"] = "Plant_17"  # If you still want to display "Overall Company" in the UI
plant_options = [f"Plant_{i}" for i in range(1, 17)] + ["Overall Company"]  # Updated to include all plant options and "Overall Company"



# Define the relation matrix as a dictionary
category_to_metrics = {
    'Sustainable Engagement': ['Staffing %'],
    'Flexibility/Wellbeing': ['Absenteeism %'],
    'Retention Driver': ['Turnover %', 'Turnover 1st Year %'],
    'Training & Development': ['Tenure <2 %'],
    'Career Advancement': ['Tenure >10 %'],
    'Vision & Direction': ['Efficiency %'],
    'Senior Leadership': ['Efficiency %', 'Spoilage %', 'HFI quality'],
    'Manager Effectiveness': ['Spoilage %', 'HFI quality'],
    'Safety': ['TRIR safety'],
    'Inclusion': ['Tenure <2 %', 'Tenure >10 %']
}

def get_participation_rate(survey_df, plant):
    plant_data = survey_df[survey_df['Plant'] == plant]
    # Assuming the participation rate is the same for all rows of the same plant
    participation_rate = plant_data['Participation'].iloc[0] if not plant_data.empty else "N/A"
    return participation_rate



def visualize_operational_metrics(plant, categories):
    plant_id = plant.replace("Plant_", "")
    metrics_to_display = set()  # Use a set to avoid duplicating metrics across categories
    
    # Collect unique metrics for the selected categories
    for category in categories:
        metrics = category_to_metrics.get(category, [])
        metrics_to_display.update(metrics)
    
    # Visualization
    if metrics_to_display:
        st.header("Operational Metrics:")
        metrics_list = list(metrics_to_display)  # Convert to list to index metrics
        for i in range(0, len(metrics_list), 2):  # Step by 2 to process pairs of metrics
            cols = st.columns(2)  # Create two columns
            for j in range(2):  # Fill each column with up to one metric
                if i+j < len(metrics_list):  # Check if there's a metric to display
                    metric = metrics_list[i+j]
                    data = ops_people_data_df[ops_people_data_df['Plant'] == plant_id]
                    if not data.empty and metric in data.columns:
                        with cols[j]:
                            st.subheader(f"{metric} over Time")
                            st.line_chart(data.set_index('Period')[metric])

# Streamlit app interface starts here
#st.title('Engagement Survey Analysis - Top Questions with Highest Excess')

# Initialize session state variables if they don't exist
if 'show_action_items' not in st.session_state:
    st.session_state['show_action_items'] = False
if 'selected_category' not in st.session_state:
    st.session_state['selected_category'] = None
if 'selected_plant' not in st.session_state:
    st.session_state['selected_plant'] = None



# Create two columns for layout: left_col for selection and action items, right_col for metrics visualization
left_col, spacer, right_col = st.columns([2, 0.1, 2])

with left_col:
    # Plant selection dropdown
    selected_option = st.selectbox('Select a Plant:', plant_options)
    selected_plant = plant_mapping[selected_option]
    if selected_plant != st.session_state['selected_plant']:
        st.session_state['selected_plant'] = selected_plant
        st.session_state['show_action_items'] = False

    # Display top 3 questions
    top_questions = get_top_questions_based_on_excess(selected_survey_df, selected_plant)
    participation_rate = get_participation_rate(selected_survey_df, selected_plant)
    if not top_questions.empty:
        st.header(f"Top 3 Questions Exceeding Benchmark for {selected_option} with participation count of {participation_rate}:")
        st.table(top_questions)

        # Define top_categories right after retrieving top_questions
        top_categories = top_questions['Category'].unique()

        # Toggle button for showing action items
        if 'show_action_items' not in st.session_state:
            st.session_state['show_action_items'] = False
        if st.button('Show Action Items'):
            st.session_state['show_action_items'] = not st.session_state['show_action_items']

        # Display action items based on the selected category
        if st.session_state['show_action_items']:
            for category in top_categories:
                if st.button(category, key=f"action_{category}"):  # Ensuring unique keys for buttons
                    st.session_state['selected_category'] = category

            if 'selected_category' in st.session_state and st.session_state['selected_category']:
                category = st.session_state['selected_category']
                st.write(f"Action Items for {category}:")
                category_action_items = action_items_df[action_items_df['Category '] == category]
                for _, row in category_action_items.iterrows():
                    with st.expander(row['Action Head']):
                        st.write(row['Action Item'])
    else:
        st.write(f"No questions exceed the 'Unfavourable' benchmark for {selected_option}.")

with right_col:
    # Check moved inside to avoid referencing before assignment
    if not top_questions.empty:
        # Visualization of operational metrics for the selected plant and its categories
        visualize_operational_metrics(selected_plant, top_categories)


st.markdown("""
<footer style='text-align: center; color: gray; padding: 10px; position: relative; bottom: 0; width: 100%;'>
    <div style='display: flex; justify-content: center; align-items: center; height: 4px; width: 60%; margin: auto;'>
        <div style='width: 33.33%; height: 100%; background-color: #8C1D40;'></div>
        <div style='width: 33.33%; height: 100%; background-color: #FFC627;'></div>
        <div style='width: 33.33%; height: 100%; background-color: #FFFFFF;'></div>
    </div>
    <hr style='margin:auto; width: 60%'>
    <span style='color: #FFFFFF;'>Team 10 - </span>
    <span style='color: #FFFFFF;'>Bhumit Sheth,</span>
    <span style='color: #FFFFFF;'>Kanhao Lin,</span>
    <span style='color: #FFFFFF;'>Sami Saud</span>
</footer>
""", unsafe_allow_html=True)
