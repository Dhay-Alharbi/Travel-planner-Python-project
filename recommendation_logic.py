# recommendation_logic.py
import pandas as pd
def recommend_destinations(df: pd.DataFrame, budget_level: str, trip_types: list):
    # Filter by budget
    df_filtered = df[df['budget_level'].str.lower() == budget_level.lower()]
    if df_filtered.empty:
        df_filtered = df.copy()

    # Compute average score per selected trip type
    df_filtered['score'] = df_filtered[trip_types].sum(axis=1) / len(trip_types)

    # Sort descending
    df_sorted = df_filtered.sort_values(by='score', ascending=False).reset_index(drop=True)

    # Get the top 3 scores
    top_scores = df_sorted['score'].unique()[:3]

    # Include all rows whose score is in top_scores
    df_top = df_sorted[df_sorted['score'].isin(top_scores)]

    return df_top[['city', 'country', 'region', 'short_description', 'score']]
