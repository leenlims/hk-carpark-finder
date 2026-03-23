import math
from pathlib import Path

import pandas as pd
import pydeck as pdk
import streamlit as st

from src.data_loader import load_carpark_data

st.set_page_config(page_title="HK Car Park Finder", layout="wide")

DATA_PATH = Path("data/basic_info_all.json")


def haversine_km(lat1, lon1, lat2, lon2):
    earth_radius_km = 6371.0

    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = (
        math.sin(dphi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return earth_radius_km * c


@st.cache_data
def get_data():
    return load_carpark_data(DATA_PATH)


st.title("HK Car Park Finder")
st.caption("Find nearby car parks in Hong Kong using open government data.")

try:
    df = get_data()
except Exception as e:
    st.error(f"Failed to load dataset: {e}")
    st.stop()

with st.sidebar:
    st.header("Filters")

    user_lat = st.number_input("Destination Latitude", value=22.3193, format="%.6f")
    user_lon = st.number_input("Destination Longitude", value=114.1694, format="%.6f")

    district_options = ["All"] + sorted(df["district"].dropna().astype(str).unique().tolist())
    selected_district = st.selectbox("District", district_options)

    open_only = st.checkbox("Open only", value=False)
    min_height = st.slider("Minimum height clearance (m)", min_value=0.0, max_value=4.0, value=0.0, step=0.1)
    top_n = st.slider("Number of results", min_value=5, max_value=30, value=10)

filtered = df.copy()

if selected_district != "All":
    filtered = filtered[filtered["district"] == selected_district]

if open_only:
    filtered = filtered[
        filtered["opening_status"].fillna("").astype(str).str.upper() == "OPEN"
    ]

filtered["height"] = pd.to_numeric(filtered["height"], errors="coerce").fillna(0)
filtered = filtered[filtered["height"] >= min_height]

filtered["distance_km"] = filtered.apply(
    lambda row: haversine_km(user_lat, user_lon, row["latitude"], row["longitude"]),
    axis=1,
)

filtered = filtered.sort_values(by=["distance_km", "height"], ascending=[True, False])
results = filtered.head(top_n).copy()

left_col, right_col = st.columns([1.1, 1.4])

with left_col:
    st.subheader("Top Matches")

    if results.empty:
        st.warning("No car parks matched your filters.")
    else:
        best = results.iloc[0]
        st.metric("Best Match", best["name"])
        st.write(f"**District:** {best['district']}")
        st.write(f"**Address:** {best['address']}")
        st.write(f"**Distance:** {best['distance_km']:.2f} km")
        st.write(f"**Height Limit:** {best['height']:.1f} m")

        st.dataframe(
            results[["name", "district", "height", "distance_km", "opening_status"]]
            .rename(
                columns={
                    "name": "Car Park",
                    "district": "District",
                    "height": "Height (m)",
                    "distance_km": "Distance (km)",
                    "opening_status": "Status",
                }
            ),
            use_container_width=True,
        )

with right_col:
    st.subheader("Map")

    if results.empty:
        st.info("Map will appear when results are available.")
    else:
        map_df = results.copy()
        map_df["tooltip_text"] = map_df.apply(
            lambda row: (
                f"{row['name']}\n"
                f"District: {row['district']}\n"
                f"Height: {row['height']} m\n"
                f"Distance: {row['distance_km']:.2f} km"
            ),
            axis=1,
        )

        parking_layer = pdk.Layer(
            "ScatterplotLayer",
            data=map_df,
            get_position="[longitude, latitude]",
            get_radius=90,
            get_fill_color="[0, 140, 255, 180]",
            pickable=True,
        )

        destination_df = pd.DataFrame(
            [{"latitude": user_lat, "longitude": user_lon}]
        )

        destination_layer = pdk.Layer(
            "ScatterplotLayer",
            data=destination_df,
            get_position="[longitude, latitude]",
            get_radius=130,
            get_fill_color="[255, 80, 80, 220]",
            pickable=True,
        )

        view_state = pdk.ViewState(
            latitude=float(map_df["latitude"].mean()),
            longitude=float(map_df["longitude"].mean()),
            zoom=12,
        )

        st.pydeck_chart(
            pdk.Deck(
                layers=[parking_layer, destination_layer],
                initial_view_state=view_state,
                tooltip={"text": "{tooltip_text}"},
            )
        )

st.markdown("---")
st.write(f"Loaded **{len(df)}** car park records.")