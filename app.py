import math
from pathlib import Path

import pandas as pd
import pydeck as pdk
import streamlit as st

from src.data_loader import load_carpark_data

st.set_page_config(
    page_title="HK Car Park Finder",
    layout="wide",
    initial_sidebar_state="expanded",
)

DATA_PATH = Path("data/basic_info_all.json")

PRESET_DESTINATIONS = {
    "Central": {"lat": 22.2819, "lon": 114.1589},
    "Tsim Sha Tsui": {"lat": 22.2988, "lon": 114.1722},
    "CUHK": {"lat": 22.4196, "lon": 114.2068},
    "Mong Kok": {"lat": 22.3193, "lon": 114.1694},
    "Causeway Bay": {"lat": 22.2803, "lon": 114.1822},
    "Wan Chai": {"lat": 22.2770, "lon": 114.1750},
    "Manual input": {"lat": 22.3193, "lon": 114.1694},
}


def inject_custom_css():
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap');

        html, body, [class*="css"], .stApp {
            font-family: 'Poppins', sans-serif;
            background: linear-gradient(180deg, #f7fbff 0%, #eef6ff 100%);
            color: #16324f;
        }

        .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
            max-width: 1200px;
        }

        section[data-testid="stSidebar"] {
            background: #f4f9ff;
            border-right: 1px solid #dbeafe;
        }

        section[data-testid="stSidebar"] * {
            font-family: 'Poppins', sans-serif !important;
        }

        div[data-testid="stMetric"] {
            background: white;
            border: 1px solid #dbeafe;
            border-radius: 18px;
            padding: 0.8rem 1rem;
            box-shadow: 0 8px 24px rgba(59, 130, 246, 0.06);
        }

        .app-card {
            background: rgba(255, 255, 255, 0.88);
            border: 1px solid #dbeafe;
            border-radius: 22px;
            padding: 1.2rem 1.2rem;
            box-shadow: 0 12px 30px rgba(59, 130, 246, 0.08);
            backdrop-filter: blur(10px);
        }

        .hero-title {
            font-size: 2.2rem;
            font-weight: 700;
            color: #0f2f4f;
            margin-bottom: 0.35rem;
        }

        .hero-subtitle {
            color: #4b6b88;
            font-size: 1rem;
            margin-bottom: 0.2rem;
        }

        .section-title {
            font-size: 1.15rem;
            font-weight: 600;
            color: #16324f;
            margin-bottom: 0.8rem;
        }

        .best-card {
            background: linear-gradient(135deg, #dff1ff 0%, #edf7ff 100%);
            border: 1px solid #bfdbfe;
            border-radius: 18px;
            padding: 1rem 1rem;
            margin-bottom: 1rem;
        }

        .best-name {
            font-size: 1.1rem;
            font-weight: 700;
            color: #0f2f4f;
            margin-bottom: 0.4rem;
        }

        .best-meta {
            color: #31506d;
            font-size: 0.95rem;
            line-height: 1.7;
        }

        a {
            color: #2563eb !important;
            text-decoration: none;
        }

        a:hover {
            text-decoration: underline;
        }

        .stDataFrame {
            border-radius: 16px;
            overflow: hidden;
        }

        div[data-testid="stSelectbox"] > div,
        div[data-testid="stNumberInput"] input,
        div[data-testid="stTextInput"] input {
            border-radius: 12px !important;
        }

        .small-note {
            color: #5b7a96;
            font-size: 0.92rem;
            margin-top: 0.5rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


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


inject_custom_css()

try:
    df = get_data()
except Exception as e:
    st.error(f"Failed to load dataset: {e}")
    st.stop()

st.markdown('<div class="hero-title">HK Car Park Finder</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="hero-subtitle">Find nearby Hong Kong car parks with a cleaner, faster location search experience.</div>',
    unsafe_allow_html=True,
)

metric_col1, metric_col2, metric_col3 = st.columns(3)
with metric_col1:
    st.metric("Total Car Parks", f"{len(df)}")
with metric_col2:
    open_count = (
        df["opening_status"].fillna("").astype(str).str.upper().eq("OPEN").sum()
        if "opening_status" in df.columns
        else 0
    )
    st.metric("Currently Marked Open", f"{open_count}")
with metric_col3:
    district_count = df["district"].dropna().astype(str).nunique() if "district" in df.columns else 0
    st.metric("Districts Covered", f"{district_count}")

st.markdown("")

with st.sidebar:
    st.markdown("## Search settings")
    st.markdown("Choose a destination and refine the results.")

    selected_preset = st.selectbox(
        "Preset destination",
        list(PRESET_DESTINATIONS.keys()),
        index=0,
        help="Quickly jump to a common Hong Kong location.",
    )

    default_lat = PRESET_DESTINATIONS[selected_preset]["lat"]
    default_lon = PRESET_DESTINATIONS[selected_preset]["lon"]

    st.markdown("### Destination coordinates")
    user_lat = st.number_input(
        "Latitude",
        value=float(default_lat),
        format="%.6f",
        help="You can overwrite the preset coordinates manually.",
    )
    user_lon = st.number_input(
        "Longitude",
        value=float(default_lon),
        format="%.6f",
        help="You can overwrite the preset coordinates manually.",
    )

    st.markdown("### Filters")
    district_options = ["All districts"] + sorted(
        df["district"].dropna().astype(str).unique().tolist()
    )
    selected_district = st.selectbox("District", district_options)

    open_only = st.checkbox("Show only currently open car parks", value=False)

    min_height = st.slider(
        "Minimum vehicle height clearance (m)",
        min_value=0.0,
        max_value=5.0,
        value=0.0,
        step=0.1,
        help="Useful if your vehicle needs extra height clearance.",
    )

    top_n = st.slider(
        "Number of matches to display",
        min_value=5,
        max_value=30,
        value=10,
    )

    sort_by = st.selectbox(
        "Sort results by",
        ["Nearest distance", "Highest clearance"],
    )

    st.markdown(
        '<div class="small-note">Tip: start with a preset destination, then fine-tune the coordinates if needed.</div>',
        unsafe_allow_html=True,
    )

filtered = df.copy()

if selected_district != "All districts":
    filtered = filtered[filtered["district"] == selected_district]

if open_only and "opening_status" in filtered.columns:
    filtered = filtered[
        filtered["opening_status"].fillna("").astype(str).str.upper() == "OPEN"
    ]

filtered["height"] = pd.to_numeric(filtered["height"], errors="coerce").fillna(0)
filtered = filtered[filtered["height"] >= min_height]

filtered["distance_km"] = filtered.apply(
    lambda row: haversine_km(user_lat, user_lon, row["latitude"], row["longitude"]),
    axis=1,
)

if sort_by == "Nearest distance":
    filtered = filtered.sort_values(by=["distance_km", "height"], ascending=[True, False])
else:
    filtered = filtered.sort_values(by=["height", "distance_km"], ascending=[False, True])

results = filtered.head(top_n).copy()

left_col, right_col = st.columns([1.05, 1.35], gap="large")

with left_col:
    st.markdown('<div class="app-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Top matches</div>', unsafe_allow_html=True)

    if results.empty:
        st.warning("No car parks matched your current filters.")
    else:
        best = results.iloc[0]

        website_html = ""
        if "website" in best and pd.notna(best["website"]) and str(best["website"]).strip():
            website = str(best["website"]).strip()
            website_html = f'<br><strong>Website:</strong> <a href="{website}" target="_blank">Open link</a>'

        st.markdown(
            f"""
            <div class="best-card">
                <div class="best-name">{best['name']}</div>
                <div class="best-meta">
                    <strong>District:</strong> {best['district']}<br>
                    <strong>Address:</strong> {best['address']}<br>
                    <strong>Distance:</strong> {best['distance_km']:.2f} km<br>
                    <strong>Height clearance:</strong> {best['height']:.1f} m<br>
                    <strong>Status:</strong> {best['opening_status']}
                    {website_html}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        table_df = results[
            ["name", "district", "address", "height", "distance_km", "opening_status"]
        ].copy()

        table_df = table_df.rename(
            columns={
                "name": "Car Park",
                "district": "District",
                "address": "Address",
                "height": "Height Clearance (m)",
                "distance_km": "Distance (km)",
                "opening_status": "Opening Status",
            }
        )

        st.dataframe(table_df, use_container_width=True, hide_index=True)

    st.markdown("</div>", unsafe_allow_html=True)

with right_col:
    st.markdown('<div class="app-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Map view</div>', unsafe_allow_html=True)

    if results.empty:
        st.info("Map will appear once matching car parks are found.")
    else:
        map_df = results.copy()

        map_df["tooltip_text"] = map_df.apply(
            lambda row: (
                f"{row['name']}\n"
                f"District: {row['district']}\n"
                f"Address: {row['address']}\n"
                f"Height: {row['height']:.1f} m\n"
                f"Distance: {row['distance_km']:.2f} km\n"
                f"Status: {row['opening_status']}"
            ),
            axis=1,
        )

        parking_layer = pdk.Layer(
            "ScatterplotLayer",
            data=map_df,
            get_position="[longitude, latitude]",
            get_radius=95,
            get_fill_color="[59, 130, 246, 180]",
            pickable=True,
        )

        destination_df = pd.DataFrame(
            [{"latitude": user_lat, "longitude": user_lon, "label": "Destination"}]
        )

        destination_layer = pdk.Layer(
            "ScatterplotLayer",
            data=destination_df,
            get_position="[longitude, latitude]",
            get_radius=130,
            get_fill_color="[14, 165, 233, 230]",
            pickable=True,
        )

        text_layer = pdk.Layer(
            "TextLayer",
            data=destination_df,
            get_position="[longitude, latitude]",
            get_text="'Destination'",
            get_size=16,
            get_color="[15, 47, 79]",
            get_alignment_baseline="'bottom'",
        )

        view_state = pdk.ViewState(
            latitude=float(map_df["latitude"].mean()),
            longitude=float(map_df["longitude"].mean()),
            zoom=12,
        )

        st.pydeck_chart(
            pdk.Deck(
                layers=[parking_layer, destination_layer, text_layer],
                initial_view_state=view_state,
                tooltip={"text": "{tooltip_text}"},
            )
        )

    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("")

st.markdown('<div class="app-card">', unsafe_allow_html=True)
st.markdown('<div class="section-title">Selected search summary</div>', unsafe_allow_html=True)
summary_district = selected_district if selected_district != "All districts" else "All districts"
st.write(
    f"Showing up to **{top_n}** car parks near **{selected_preset}** "
    f"at coordinates **({user_lat:.4f}, {user_lon:.4f})**, "
    f"filtered by **{summary_district}** and **minimum height clearance of {min_height:.1f} m**."
)
st.markdown("</div>", unsafe_allow_html=True)