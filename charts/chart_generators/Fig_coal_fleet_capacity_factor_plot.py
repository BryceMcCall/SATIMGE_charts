# coal fleet capacity factor plot
# not complete yet


def calculate_coal_capacity_factor(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate capacity factor for the coal fleet.
    Expects:
      - 'Sector'
      - 'Subsector'
      - 'Indicator' (e.g., 'Capacity', 'Generation')
      - 'Year'
      - 'SATIMGE' (numeric value)
    """

    coal_subsectors = ["ECoal"]  # Adjust if your data has other coal names
    com = "Electricity"

    # Filter to coal subsector
    df_coal = df[(df["Sector"] == "Power") &
                  (df["Subsector"].isin(coal_subsectors))&
                  (df["Commodity Short Description"] == com) &
                  (df["Indicator"].isin(["Capacity", "FlowOut"]))
                  ].copy()

    # Pivot to get Capacity and Generation side-by-side
    df_pivot = df_coal.pivot_table(
        index=["Scenario", "Year", "Subsector"],
        columns="Indicator",
        values="SATIMGE",
        aggfunc="sum"
    ).reset_index()

    # Ensure both columns exist
    if "Capacity" not in df_pivot.columns or "Generation" not in df_pivot.columns:
        raise ValueError("Data must contain both 'Capacity' and 'Generation' indicators.")

    # Capacity factor calculation
    # Capacity in GW, Generation in TWh
    df_pivot["CapacityFactor_%"] = (
        df_pivot["Generation"] * 1000  # TWh -> GWh
        / (df_pivot["Capacity"] * 8760) * 100
    )

    return df_pivot[["Scenario", "Year", "Subsector", "CapacityFactor_%"]]
