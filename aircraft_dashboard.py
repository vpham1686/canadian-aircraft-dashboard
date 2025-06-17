import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# --------------------------------------------------
# Page & Theme
# --------------------------------------------------
st.set_page_config(
    page_title="🌎 Canadian Aircraft Dashboard",
    layout="wide",
    initial_sidebar_state="expanded",
    page_icon="✈️",
)

# --------------------------------------------------
# Constants & Helpers
# --------------------------------------------------
CANADA_PROVINCES = [
    "British Columbia", "Alberta", "Saskatchewan", "Manitoba", "Ontario", "Quebec",
    "New Brunswick", "Nova Scotia", "Prince Edward Island", "Newfoundland and Labrador",
    "Yukon", "Northwest Territories", "Nunavut",
]

# --------------------------------------------------
# Data Loading
# --------------------------------------------------
@st.cache_data
def load_data():
    xl_file = "Canadian Aircraft Registry.xlsx"
    owners = pd.read_excel(xl_file, sheet_name="carsownr")
    curr = pd.read_excel(xl_file, sheet_name="carscurr")

    df = curr.merge(owners, left_on="Mark", right_on="Registration Mark", how="left")
    df["Number of Engines"] = pd.to_numeric(df["Number of Engines"], errors="coerce")
    df["Aircraft Age"] = pd.to_numeric(df["Aircraft Age"], errors="coerce")
    df["Year of Manufacture/Assembly"] = pd.to_numeric(df["Year of Manufacture/Assembly"], errors="coerce")

    date_col = "Issue Date" if "Issue Date" in df.columns else "Modified Date"
    df["Reg Year"] = pd.to_datetime(df[date_col], errors="coerce").dt.year

    wcol = next((c for c in df.columns if "weight" in c.lower()), None)
    if wcol:
        df[wcol] = pd.to_numeric(df[wcol], errors="coerce")

    df = df[df["Province (English)"].isin(CANADA_PROVINCES)]
    return df, wcol

df, WEIGHT_COL = load_data()

# --------------------------------------------------
# Sidebar Filters
# --------------------------------------------------
st.sidebar.header("Filters")

province = st.sidebar.multiselect("Province", CANADA_PROVINCES)
category = st.sidebar.multiselect("Aircraft Category", sorted(df["Aircraft Category"].dropna().unique()))
owner_type = st.sidebar.multiselect("Owner Type", sorted(df["Type of Owner"].dropna().unique()))
engine_cat = st.sidebar.multiselect("Engine Category", sorted(df["Engine Category"].dropna().unique()))

min_eng, max_eng = int(df["Number of Engines"].min()), int(df["Number of Engines"].max())
col1, col2 = st.sidebar.columns(2)
min_eng_input = col1.number_input("Min Engines", min_value=min_eng, max_value=max_eng, value=min_eng)
max_eng_input = col2.number_input("Max Engines", min_value=min_eng, max_value=max_eng, value=max_eng)
num_engines = (min_eng_input, max_eng_input)

min_year, max_year = int(df["Year of Manufacture/Assembly"].min()), int(df["Year of Manufacture/Assembly"].max())
col1, col2 = st.sidebar.columns(2)
min_year_input = col1.number_input("Min Year", min_value=min_year, max_value=max_year, value=min_year)
max_year_input = col2.number_input("Max Year", min_value=min_year, max_value=max_year, value=max_year)
year_range = (min_year_input, max_year_input)

min_age, max_age = int(df["Aircraft Age"].min()), int(df["Aircraft Age"].max())
col1, col2 = st.sidebar.columns(2)
min_age_input = col1.number_input("Min Age", min_value=min_age, max_value=max_age, value=min_age)
max_age_input = col2.number_input("Max Age", min_value=min_age, max_value=max_age, value=max_age)
age_range = (min_age_input, max_age_input)

if WEIGHT_COL:
    min_w, max_w = int(df[WEIGHT_COL].min()), int(df[WEIGHT_COL].max())
    col1, col2 = st.sidebar.columns(2)
    min_w_input = col1.number_input("Min Weight", min_value=min_w, max_value=max_w, value=min_w)
    max_w_input = col2.number_input("Max Weight", min_value=min_w, max_value=max_w, value=max_w)
    weight_range = (min_w_input, max_w_input)
else:
    weight_range = None

country_cols = [c for c in df.columns if "country" in c.lower() and "manufact" in c.lower()]
country_col = country_cols[0] if country_cols else None
if country_col:
    country_sel = st.sidebar.multiselect("Country of Manufacture", sorted(df[country_col].dropna().unique()))
else:
    country_sel = []

search = st.sidebar.text_input("Search Common Name / Model")

# Chart visibility checkboxes
st.sidebar.markdown("---")
st.sidebar.subheader("Select charts to display")
chart_top_manu = st.sidebar.checkbox("Top 10 Manufacturers", value=True)
chart_top_model = st.sidebar.checkbox("Top 10 Models", value=True)
chart_cat_dist = st.sidebar.checkbox("Aircraft Category Distribution", value=True)
chart_owner_type = st.sidebar.checkbox("Ownership Type Share", value=True)
chart_age_hist = st.sidebar.checkbox("Aircraft Age Distribution", value=True)
chart_prov_bar = st.sidebar.checkbox("Aircraft Count by Province", value=True)
chart_reg_year = st.sidebar.checkbox("Registrations per Year", value=True)
chart_owner_trend = st.sidebar.checkbox("Ownership Trend Over Time", value=True)

st.sidebar.markdown("---")
st.sidebar.markdown("**Created by Victor Pham**  \n_Last updated June 2025_")

# --------------------------------------------------
# Filter Application
# --------------------------------------------------
flt = df.copy()
if province:
    flt = flt[flt["Province (English)"].isin(province)]
if category:
    flt = flt[flt["Aircraft Category"].isin(category)]
if owner_type:
    flt = flt[flt["Type of Owner"].isin(owner_type)]
if engine_cat:
    flt = flt[flt["Engine Category"].isin(engine_cat)]
if country_sel and country_col:
    flt = flt[flt[country_col].isin(country_sel)]

flt = flt[
    flt["Number of Engines"].between(*num_engines) &
    flt["Year of Manufacture/Assembly"].between(*year_range) &
    flt["Aircraft Age"].between(*age_range)
]
if WEIGHT_COL and weight_range:
    flt = flt[flt[WEIGHT_COL].between(*weight_range)]

if search:
    mask = flt["Common Name"].str.contains(search, case=False, na=False) | flt["Model Name"].str.contains(search, case=False, na=False)
    flt = flt[mask]

flt = flt.replace("null", pd.NA)
total = len(flt)

# --------------------------------------------------
# Styling Helpers
# --------------------------------------------------
bar_lbl = dict(texttemplate="%{y}", textposition="outside")
axis_fmt = dict(title_font=dict(size=14, family="Arial"))

# --------------------------------------------------
# Charts
# --------------------------------------------------
st.title("🌎 Canadian Aircraft Registry Dashboard")

if chart_top_manu and not flt.empty:
    st.subheader("Top 10 Aircraft Manufacturers")
    manu_df = flt["Manufacturer's Name"].value_counts().head(10).reset_index()
    manu_df.columns = ["Manufacturer", "Count"]
    fig_manu = px.bar(manu_df, x="Manufacturer", y="Count", title="Top 10 Manufacturers")
    fig_manu.update_traces(**bar_lbl)
    fig_manu.update_layout(xaxis_title="Manufacturer", yaxis_title="Count", **axis_fmt)
    st.plotly_chart(fig_manu, use_container_width=True)

if chart_top_model and not flt.empty:
    st.subheader("Top 10 Aircraft Models")
    model_df = flt["Model Name"].value_counts().head(10).reset_index()
    model_df.columns = ["Model", "Count"]
    fig_model = px.bar(model_df, x="Model", y="Count", title="Top 10 Models")
    fig_model.update_traces(**bar_lbl)
    fig_model.update_layout(xaxis_title="Model", yaxis_title="Count", **axis_fmt)
    st.plotly_chart(fig_model, use_container_width=True)

if chart_cat_dist and not flt.empty:
    st.subheader("Aircraft Category Distribution")
    fig_cat = px.pie(flt, names="Aircraft Category", title="Aircraft Category Share", hole=.45)
    fig_cat.update_traces(hovertemplate="%{label}: %{value} (%{percent})")
    fig_cat.add_annotation(text=f"{total}", x=0.5, y=0.5, font_size=18, showarrow=False)
    st.plotly_chart(fig_cat, use_container_width=True)

if chart_owner_type and not flt.empty:
    st.subheader("Ownership Type Share")
    fig_owner = px.pie(flt, names="Type of Owner", title="Entity vs Individual", hole=.45)
    fig_owner.update_traces(hovertemplate="%{label}: %{value} (%{percent})")
    fig_owner.add_annotation(text=f"{total}", x=0.5, y=0.5, font_size=18, showarrow=False)
    st.plotly_chart(fig_owner, use_container_width=True)

if chart_age_hist and not flt.empty:
    st.subheader("Aircraft Age Distribution")
    fig_age = px.histogram(flt.dropna(subset=["Aircraft Age"]), x="Aircraft Age", nbins=30, title="Aircraft Age Histogram")
    fig_age.update_layout(xaxis_title="Aircraft Age", yaxis_title="Count", **axis_fmt)
    st.plotly_chart(fig_age, use_container_width=True)

if chart_prov_bar and not flt.empty:
    st.subheader("Aircraft Count by Province")
    prov_df = flt["Province (English)"].value_counts().reset_index()
    prov_df.columns = ["Province", "Count"]
    fig_prov = px.bar(prov_df, x="Province", y="Count", title="Aircraft Count by Province")
    fig_prov.update_traces(**bar_lbl)
    fig_prov.update_layout(xaxis_title="Province", yaxis_title="Count", **axis_fmt)
    st.plotly_chart(fig_prov, use_container_width=True)

if chart_reg_year:
    st.subheader("Registrations per Year")
    reg_df = flt.dropna(subset=["Reg Year"]).groupby("Reg Year").size().reset_index(name="Count")
    if not reg_df.empty:
        fig_reg = px.line(reg_df, x="Reg Year", y="Count", markers=True, title="New Registrations by Year")
        fig_reg.update_layout(xaxis_title="Year", yaxis_title="Count", **axis_fmt)
        st.plotly_chart(fig_reg, use_container_width=True)

if chart_owner_trend:
    st.subheader("Ownership Trend Over Time")
    trend_df = flt.dropna(subset=["Reg Year"]).groupby(["Reg Year", "Type of Owner"]).size().reset_index(name="Count")
    if not trend_df.empty:
        fig_trend = px.line(trend_df, x="Reg Year", y="Count", color="Type of Owner", markers=True, title="Entity vs Individual Over Time")
        fig_trend.update_layout(xaxis_title="Year", yaxis_title="Count", **axis_fmt)
        st.plotly_chart(fig_trend, use_container_width=True)

# --------------------------------------------------
# Drill-Down Data Expander
# --------------------------------------------------
with st.expander("View Filtered Dataset"):
    st.dataframe(flt)

# --------------------------------------------------
# End