# recommendation_logic.py

def recommend_destinations(df, budget_level, trip_types):
    # Filter by budget
    df_filtered = df[df['budget_level'].str.lower() == budget_level.lower()]

    # Computes average score per selected trip type
    df_filtered['score'] = df_filtered[trip_types].sum(axis=1) / len(trip_types)

    # Sort descending
    df_sorted = df_filtered.sort_values(by='score', ascending=False).reset_index(drop=True)

    # Assign ranks based on score
    df_sorted['rank'] = df_sorted['score'].rank(method='min', ascending=False)

    # Include all rank <= 5
    df_top = df_sorted[df_sorted['rank'] <= 5]

    return df_top[['city', 'country', 'region', 'short_description', 'score']]

