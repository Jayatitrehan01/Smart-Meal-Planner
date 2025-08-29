import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# ---------------------------
# Load Data
# ---------------------------
url = "https://drive.google.com/uc?export=download&id=1e47Ho2VkOuErwUyVr1MN9vaRIIAvzGep"
data = pd.read_excel(url)
meal_df = pd.DataFrame(data)

# ---------------------------
# Helper Functions
# ---------------------------
def calculate_bmr(age, gender, weight, height):
    if gender == "Male":
        return 88.36 + (13.4 * weight) + (4.8 * height) - (5.7 * age)
    else:
        return 447.6 + (9.2 * weight) + (3.1 * height) - (4.3 * age)

def get_activity_factor(activity):
    factors = {
        "Sedentary": 1.2,
        "Lightly Active": 1.375,
        "Moderately Active": 1.55,
        "Very Active": 1.725
    }
    return factors.get(activity, 1.2)

def adjust_for_goal(calories, goal):
    if goal == "Weight Loss":
        return calories - 500
    elif goal == "Muscle Gain":
        return calories + 300
    else:
        return calories

def get_macros(calories, goal):
    if goal == "Weight Loss":
        ratios = (0.4, 0.3, 0.3)   # Protein, Carbs, Fat
    elif goal == "Muscle Gain":
        ratios = (0.3, 0.5, 0.2)
    else:
        ratios = (0.25, 0.5, 0.25)

    protein_cals, carb_cals, fat_cals = [calories * r for r in ratios]
    return {
        "protein": protein_cals / 4,
        "carbs": carb_cals / 4,
        "fat": fat_cals / 9
    }

def classify_diet(food_name):
    food_name = str(food_name).lower()

    non_veg_keywords = [
        "chicken","mutton","beef","pork","fish","egg","eggs",
        "seafood","lamb","turkey","duck","bacon","ham",
        "prawns","shrimp","crab","lobster","oyster","squid",
        "anchovy","sardine","salmon","tuna","meat","veal",
        "goat","steak","pepperoni","sausage","kebab","drumstick",
        "cutlet","nuggets"
    ]

    veg_keywords = [
        "paneer","tofu","dal","lentil","beans","chole","rajma",
        "peas","spinach","mushroom","potato","cauliflower","cabbage",
        "carrot","broccoli","okra","brinjal","eggplant","zucchini",
        "pumpkin","gourd","bottle gourd","bitter gourd","ridge gourd",
        "cucumber","tomato","onion","capsicum","bell pepper",
        "corn","soy","soya","sambar","idli","dosa","upma",
        "poha","roti","paratha","khichdi","sabzi","curry",
        "rice","pulao","biryani (veg)","kadhi","curd","yogurt",
        "butter","milk","cheese","ghee"
    ]

    if any(word in food_name for word in non_veg_keywords):
        return "Non-Veg"
    elif any(word in food_name for word in veg_keywords):
        return "Veg"
    else:
        return "Vegan"

# Apply classification
meal_df["diet_choice"] = meal_df["food_name"].apply(classify_diet)

# ---------------------------
# Meal Recommendation
# ---------------------------
def filter_meals_by_diet(diet_choice):
    """Return meals filtered by diet inclusion rules"""
    if diet_choice == "vegan":
        return meal_df[meal_df["diet_choice"].str.lower() == "vegan"]
    elif diet_choice == "veg":
        return meal_df[meal_df["diet_choice"].str.lower().isin(["veg", "vegan"])]
    elif diet_choice == "non-veg":
        return meal_df[meal_df["diet_choice"].str.lower().isin(["veg", "vegan", "non-veg"])]
    else:
        return meal_df.copy()

def recommend_meals(target_calories, diet_choice):
    # Filtering logic with inclusion rules
    if diet_choice == "vegan":
        filtered_meals = meal_df[meal_df["diet_choice"].str.lower() == "vegan"]
    elif diet_choice == "veg":
        filtered_meals = meal_df[meal_df["diet_choice"].str.lower().isin(["veg", "vegan"])]
    elif diet_choice == "non-veg":
        filtered_meals = meal_df[meal_df["diet_choice"].str.lower().isin(["veg", "vegan", "non-veg"])]
    else:
        filtered_meals = meal_df.copy()

    # ✅ Ensure Calories column exists
    if "Calories" not in filtered_meals.columns:
        filtered_meals = filtered_meals.copy()
        filtered_meals["Calories"] = (
            filtered_meals["protein_g"].fillna(0) * 4 +
            filtered_meals["carb_g"].fillna(0) * 4 +
            filtered_meals["fat_g"].fillna(0) * 9
        )

    # Sort meals by Calories
    sorted_meals = filtered_meals.sort_values(by="Calories")

    # Pick meals until we reach close to the target
    total = 0
    chosen = []

    for _, row in sorted_meals.iterrows():
        if total + row["Calories"] <= target_calories:
            chosen.append({
                "food_name": row["food_name"],
                "calories": row["Calories"],
                "protein": row.get("protein_g", 0),
                "carbs": row.get("carb_g", 0),
                "fat": row.get("fat_g", 0)
            })
            total += row["Calories"]

    return pd.DataFrame(chosen), total, filtered_meals


# ---------------------------
# Streamlit UI
# ---------------------------
st.title("🥗 Smart Meal Planner")
st.write("Get personalized meal suggestions based on your health goals!")

with st.form("user_input"):
    age = st.number_input("Age", 10, 80, 25)
    gender = st.radio("Gender", ["Male", "Female"])
    weight = st.number_input("Weight (kg)", 30, 150, 70)
    height = st.number_input("Height (cm)", 120, 220, 170)
    activity = st.selectbox("Activity Level", ["Sedentary", "Lightly Active", "Moderately Active", "Very Active"])
    goal = st.selectbox("Goal", ["Weight Loss", "Muscle Gain", "Maintenance"])
    diet_choice = st.selectbox("Diet Preference", ["veg", "non-veg", "vegan"])
    submitted = st.form_submit_button("Generate Plan")

if submitted:
    bmr = calculate_bmr(age, gender, weight, height)
    calories = adjust_for_goal(bmr * get_activity_factor(activity), goal)
    macros = get_macros(calories, goal)

    # Unpack results
    plan_df, total, filtered_meals = recommend_meals(calories, diet_choice)

    st.subheader("Your Daily Nutrition Targets")
    st.write(f"**Calories:** {int(calories)} kcal/day")
    st.write(f"**Protein:** {int(macros['protein'])} g | "
             f"**Carbs:** {int(macros['carbs'])} g | "
             f"**Fat:** {int(macros['fat'])} g")

    # Macro pie chart
    protein_cals = int(macros['protein']) * 4
    carb_cals = macros['carbs'] * 4
    fat_cals = macros['fat'] * 9

    st.subheader("Macro Distribution")
    fig, ax = plt.subplots()
    ax.pie([protein_cals, carb_cals, fat_cals],
           labels=["Protein", "Carbs", "Fat"],
           autopct='%1.1f%%',
           textprops={'color': 'white'})
    plt.axis('equal')
    st.pyplot(fig, transparent=True)

    # Meal plan
    st.subheader("Recommended Meal Options")
    st.dataframe(plan_df)
    
    # Diet breakdown
    st.subheader("Available Options Breakdown")
    breakdown = filtered_meals["diet_choice"].value_counts()
    st.table(breakdown)
    for diet, count in breakdown.items():
        st.write(f"**{diet}:** {count} options")


