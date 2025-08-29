import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

data=pd.read_excel(r"C:\Users\jayat\OneDrive\Documents\smart meal planner\indb data.xlsx")
meal_df = pd.DataFrame(data)

# ---------------------------
# Helper Functions
# ---------------------------
def calculate_bmr(age, gender, weight, height):
    print("Using Harris-Benedict formula for BMR(Basal Metabolic Rate)")
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
    food_name=str(food_name).lower()

    # Non-veg items
    non_veg_keywords=["chicken", "mutton", "beef", "pork", "fish", "egg", "eggs",
    "seafood", "lamb", "turkey", "duck", "bacon", "ham",
    "prawns", "shrimp", "crab", "lobster", "oyster", "squid",
    "anchovy", "sardine", "salmon", "tuna", "meat", "veal",
    "goat", "steak", "pepperoni", "sausage", "kebab", "drumstick",
    "cutlet", "nuggets"]

    # Veg items
    veg_keywords=["paneer", "tofu", "dal", "lentil", "beans", "chole", "rajma",
    "peas", "spinach", "mushroom", "potato", "cauliflower", "cabbage",
    "carrot", "broccoli", "okra", "brinjal", "eggplant", "zucchini",
    "pumpkin", "gourd", "bottle gourd", "bitter gourd", "ridge gourd",
    "cucumber", "tomato", "onion", "capsicum", "bell pepper",
    "corn", "soy", "soya", "sambar", "idli", "dosa", "upma",
    "poha", "roti", "paratha", "khichdi", "sabzi", "curry",
    "rice", "pulao", "biryani (veg)", "kadhi", "curd", "yogurt",
    "butter", "milk", "cheese", "ghee"]

    # Check for Non-veg
    if any (word in food_name for word in non_veg_keywords):
        return "Non-Veg"
    # Check for dairy → vegetarian but not vegan
    elif any(word in food_name for word in veg_keywords):
        return "Veg"
    else:
        return "Vegan"

# Apply function to create new column
meal_df["diet_choice"] = meal_df["food_name"].apply(classify_diet)

# Save updated dataset
meal_df.to_excel(r"C:\Users\jayat\OneDrive\Documents\smart meal planner\indb_data.xlsx", index=False)

def recommend_meals(target_calories, diet_choice):
    # Filter meals by diet type
    filtered_meals = meal_df[meal_df["diet_choice"].str.lower() == diet_choice]
    
    # Ensure Calories column exists (use consistent naming)
    if "Calories" not in filtered_meals.columns:
        filtered_meals["Calories"] = (
            filtered_meals["protein_g"] * 4 +
            filtered_meals["carb_g"] * 4 +
            filtered_meals["fat_g"] * 9
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
    
    return pd.DataFrame(chosen), total
    




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
    df_filtered = meal_df[meal_df["diet_choice"] == diet_choice]
    submitted = st.form_submit_button("Generate Plan")

if submitted:
    bmr = calculate_bmr(age, gender, weight, height)
    calories = adjust_for_goal(bmr * get_activity_factor(activity), goal)
    macros = get_macros(calories, goal)

    # Unpack here
    plan_df, total = recommend_meals(calories, diet_choice)

    st.subheader("Your Daily Nutrition Targets")
    st.write(f"**Calories:** {int(calories)} kcal/day")
    st.write(f"**Protein:** {int(macros['protein'])} g |\n **Carbs:** {int(macros['carbs'])} g |\n **Fat:** {int(macros['fat'])} g")

    st.subheader("Recommended Meal Plan")
    st.dataframe(plan_df)
    st.write("**Total Calories from selected meals:**", int(total))

    
    protein_cals = int(macros['protein'])*4
    carb_cals = macros['carbs']*4
    fat_cals= macros['fat']*9

    st.subheader("Macro Distribution")
    fig, ax = plt.subplots() 

    ax.pie([protein_cals,carb_cals,fat_cals],
           labels=["Protein", "Carbs", "Fat"],
           autopct='%1.1f%%',
           textprops={'color': 'white'})
    ax.set_facecolor(None)
    plt.axis('equal')
    st.pyplot(fig,transparent=True)
    plt.show()
