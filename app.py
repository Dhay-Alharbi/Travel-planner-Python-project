# app.py
from data import load_cleaned_data
from recommendation_logic import recommend_destinations

def get_user_input():
    """
    Ask the user for budget level and trip types.
    """
    print("========================================")
    print("🌍 Welcome to the Travel Planning Assistant!")
    print("Let's help you set up your trip details.")
    print("========================================\n")

    # Budget options
    budget_levels = {
        1: ("Budget", 50, 150),
        2: ("Mid-range", 150, 350),
        3: ("Luxury", 350, 1000)
    }

    print("🔹 Select your Budget Level:")
    for num, (level, low, high) in budget_levels.items():
        high_display = f"{high}+" if high >= 1000 else str(high)
        print(f"{num}. {level} ({low} - {high_display})")

    while True:
        try:
            choice = int(input("\nEnter the number corresponding to your budget level: "))
            if choice not in budget_levels:
                raise ValueError("Invalid option")
            budget_level, budget_min, budget_max = budget_levels[choice]
            break
        except ValueError as e:
            print(f"❌ Error: {e}. Please choose a valid number (1-3).")

    # Trip type options
    valid_trip_types = ["culture", "adventure", "nature", "beaches", "cuisine", "wellness", "urban", "seclusion"]
    print("\n🔹 Available Trip Types:")
    for i, t in enumerate(valid_trip_types, start=1):
        print(f"{i}. {t}")
    print("\n👉 Choose one or more types by number. Example: 1, 3, 5\n")

    while True:
        try:
            user_input = input("Enter your choice(s): ")
            chosen_numbers = [int(num.strip()) for num in user_input.split(",")]
            invalid_nums = [n for n in chosen_numbers if n < 1 or n > len(valid_trip_types)]
            if invalid_nums:
                raise ValueError(f"Invalid option(s): {invalid_nums}")
            chosen_types = [valid_trip_types[n - 1] for n in chosen_numbers]
            break
        except ValueError as e:
            print(f"❌ Error: {e}")
            print("Please choose numbers only from the list above.\n")

    return budget_level, budget_min, budget_max, chosen_types


# ---- Main ----
if __name__ == "__main__":
    # Load data
    df = load_cleaned_data()

    # Get user input
    budget_level, budget_min, budget_max, trip_types = get_user_input()
    print("\n✅ Inputs saved successfully!")
    print(f"Budget Level: {budget_level} ({budget_min} - {budget_max})")
    print(f"Trip Types Selected: {trip_types}")

    # Get recommendations
    recommendations = recommend_destinations(df, budget_level, trip_types)

    # ---- Print recommendations ----
    print("\n🏖️ Top 3 Destination Recommendations for You:\n")
    for idx, row in recommendations.head(3).iterrows():
        print(f"Recommendation {idx+1}:")
        print(f"   City: {row['city']} , Country: {row['country']} , Region: {row['region']}")
        print(f"   Description: {row['short_description']}")
        print(f"   Average Score: {row['score']:.2f}\n")
