import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# --------------------------------------------------
# Page & Theme
# --------------------------------------------------
st.set_page_config(
    page_title="Canadian Aircraft Dashboard",
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
MAJOR_MANUFACTURERS = ["Boeing", "Airbus", "Bombardier", "Embraer"]
MAJOR_AIRLINES      = ["Air Canada", "WestJet", "Skyservice", "Porter", "Air  Transat"]

# --------------------------------------------------
# Data Loading
# --------------------------------------------------
@st.cache_data
def load_data():
    xl_file = "Canadian Aircraft Registry Automated.xlsx"
    owners  = pd.read_excel(xl_file, sheet_name="carsownr")
    curr    = pd.read_excel(xl_file, sheet_name="carscurr")

    df = curr.merge(owners, left_on="Mark", right_on="Registration Mark", how="left")

    # ------------------------------------------------------------------
    # Recompute YEAR & AGE (pandas does NOT evaluate Excel formulas)
    manuf_dt = pd.to_datetime(df["Date of Manufacture/Assembly"], errors="coerce")
    df["Year of Manufacture/Assembly"] = manuf_dt.dt.year.astype("Int64")
    current_year = datetime.now().year
    df["Aircraft Age"] = current_year - df["Year of Manufacture/Assembly"]
    # ------------------------------------------------------------------

    # Numeric cleaning
    df["Number of Engines"] = pd.to_numeric(df["Number of Engines"], errors="coerce")

    date_col  = "Issue Date" if "Issue Date" in df.columns else "Modified Date"
    df["Reg Year"] = pd.to_datetime(df[date_col], errors="coerce").dt.year

    # Optional weight column
    wcol = next((c for c in df.columns if "weight" in c.lower()), None)
    if wcol:
        df[wcol] = pd.to_numeric(df[wcol], errors="coerce")

    # Keep Canadian provinces only
    df = df[df["Province (English)"].isin(CANADA_PROVINCES)]
    return df, wcol

df, WEIGHT_COL = load_data()

# --------------------------------------------------
# Sidebar
# --------------------------------------------------
st.sidebar.header("Filters")

# --- Major manufacturer check-boxes ---------------------------------------
st.sidebar.markdown("### Highlight Manufacturers")
sel_boeing     = st.sidebar.checkbox("Boeing")
sel_airbus     = st.sidebar.checkbox("Airbus")
sel_bombardier = st.sidebar.checkbox("Bombardier")
sel_embraer    = st.sidebar.checkbox("Embraer")

# --- Major airline check-boxes -------------------------------------------
st.sidebar.markdown("### Highlight Airlines")
sel_air_canada  = st.sidebar.checkbox("Air Canada")
sel_westjet     = st.sidebar.checkbox("WestJet")
sel_skyservice  = st.sidebar.checkbox("Skyservice")
sel_porter      = st.sidebar.checkbox("Porter")
sel_air_transat = st.sidebar.checkbox("Air Transat")

# Apply highlighted-checkbox logic
df_highlight = df.copy()
if sel_boeing or sel_airbus or sel_bombardier or sel_embraer:
    chosen_manu = []
    if sel_boeing:       chosen_manu.append("Boeing")
    if sel_airbus:       chosen_manu.append("Airbus")
    if sel_bombardier:   chosen_manu.append("Bombardier")
    if sel_embraer:      chosen_manu.append("Embraer")
    df_highlight = df_highlight[df_highlight["Common Name"].isin(chosen_manu)]

if sel_air_canada or sel_westjet or sel_skyservice or sel_porter or sel_air_transat:
    chosen_ops = []
    if sel_air_canada:   chosen_ops.append("Air Canada")
    if sel_westjet:      chosen_ops.append("WestJet")
    if sel_skyservice:   chosen_ops.append("Skyservice Business Aviation Inc.")
    if sel_porter:
        chosen_ops.append("Porter Airlines Inc.")
        chosen_ops.append("Porter Airlines (Canada) Limited")
    if sel_air_transat:  chosen_ops.append("Air Transat A T Inc.")
    df_highlight = df_highlight[df_highlight["Owner Name"].isin(chosen_ops)]

# Use df_highlight for all further filtering
df = df_highlight

# --- Standard multiselect filters ----------------------------------------
province   = st.sidebar.multiselect("Province", CANADA_PROVINCES)
category   = st.sidebar.multiselect("Aircraft Category",
                                    sorted(df["Aircraft Category"].dropna().unique()))
engine_cat = st.sidebar.multiselect("Engine Category",
                                    sorted(df["Engine Category"].dropna().unique()))

# Registered Purpose (Commercial / Private)
purpose_filter = st.sidebar.multiselect("Registered Purpose",
                                        ["Commercial", "Private"])

# ----- Engine-count range slider with min==max guard ----------------------
min_eng, max_eng = int(df["Number of Engines"].min()), int(df["Number of Engines"].max())
if min_eng == max_eng:          # only a single value available
    st.sidebar.number_input("Engine Count", value=min_eng, disabled=True)
    num_engines = (min_eng, max_eng)
else:
    num_engines = st.sidebar.slider("Engine Count", min_eng, max_eng,
                                    (min_eng, max_eng))

# ----- Year range slider (same guard) -------------------------------------
min_year = int(df["Year of Manufacture/Assembly"].min())
max_year = int(df["Year of Manufacture/Assembly"].max())
if min_year == max_year:
    st.sidebar.number_input("Year of Manufacture", value=min_year, disabled=True)
    year_range = (min_year, max_year)
else:
    year_range = st.sidebar.slider("Year of Manufacture", min_year, max_year,
                                   (min_year, max_year))

# ----- Age range slider ---------------------------------------------------
min_age = int(df["Aircraft Age"].min())
max_age = int(df["Aircraft Age"].max())
if min_age == max_age:
    st.sidebar.number_input("Aircraft Age (yrs)", value=min_age, disabled=True)
    age_range = (min_age, max_age)
else:
    age_range = st.sidebar.slider("Aircraft Age (yrs)", min_age, max_age,
                                  (min_age, max_age))

# ----- Weight range slider (if column exists) -----------------------------
if WEIGHT_COL:
    min_w, max_w = int(df[WEIGHT_COL].min()), int(df[WEIGHT_COL].max())
    if min_w == max_w:
        st.sidebar.number_input("Weight", value=min_w, disabled=True)
        weight_range = (min_w, max_w)
    else:
        weight_range = st.sidebar.slider("Weight Range (kg)", min_w, max_w,
                                         (min_w, max_w))
else:
    weight_range = None

# ----- Country filter -----------------------------------------------------
country_cols = [c for c in df.columns if "country" in c.lower() and "manufact" in c.lower()]
country_col  = country_cols[0] if country_cols else None
if country_col:
    country_sel = st.sidebar.multiselect("Country of Manufacture",
                                         sorted(df[country_col].dropna().unique()))
else:
    country_sel = []

search = st.sidebar.text_input("Search Common / Model / Reg")

# --------------------------------------------------
# Chart Toggles
# --------------------------------------------------
st.sidebar.markdown("---")
chart_top_manu       = st.sidebar.checkbox("Top 15 Manufacturers", True)
chart_top_model      = st.sidebar.checkbox("Top 15 Models", True)
chart_top_operator   = st.sidebar.checkbox("Top 15 Commercial Operators", True)
chart_cat_dist       = st.sidebar.checkbox("Aircraft Category Distribution", True)
chart_purpose_share  = st.sidebar.checkbox("Registered Purpose Share", True)
chart_age_hist       = st.sidebar.checkbox("Aircraft Age Histogram", True)
chart_prov_bar       = st.sidebar.checkbox("Aircraft by Province", True)
chart_reg_year       = st.sidebar.checkbox("Registrations per Year", True)
chart_purpose_trend  = st.sidebar.checkbox("Purpose Trend Over Time", True)

st.sidebar.markdown("---")
st.sidebar.markdown("**Created by Victor Pham**  \n_Last updated August 2025_")

# --------------------------------------------------
# Apply Filters
# --------------------------------------------------
flt = df.copy()
if province:
    flt = flt[flt["Province (English)"].isin(province)]
if category:
    flt = flt[flt["Aircraft Category"].isin(category)]
if engine_cat:
    flt = flt[flt["Engine Category"].isin(engine_cat)]
if purpose_filter:
    flt = flt[flt["Registered Purpose"].str.contains('|'.join(purpose_filter),
                                                     case=False, na=False)]
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
    mask = (
        flt["Common Name"].str.contains(search, case=False, na=False) |
        flt["Model Name"].str.contains(search, case=False, na=False) |
        flt["Mark"].str.contains(search, case=False, na=False)
    )
    flt = flt[mask]

flt = flt.replace("null", pd.NA)
total = len(flt)

# --------------------------------------------------
# Styling Helpers
# --------------------------------------------------
bar_lbl  = dict(texttemplate="%{y}", textposition="outside")
axis_fmt = dict(title_font=dict(size=14, family="Arial"),
                margin=dict(t=80, b=40))

# --------------------------------------------------
# Dashboard
# --------------------------------------------------
st.title("🛩️ Canadian Aircraft Registry Dashboard")

# 1. Top Manufacturers
if chart_top_manu and not flt.empty:
    st.subheader("Top 15 Aircraft Manufacturers")
    manu_df = flt["Common Name"].value_counts().head(15).reset_index()
    manu_df.columns = ["Manufacturer", "Count"]
    fig = px.bar(manu_df, x="Manufacturer", y="Count",
                 title="Top 15 Manufacturers")
    fig.update_traces(**bar_lbl)
    fig.update_layout(xaxis_title="Manufacturer", yaxis_title="Count", **axis_fmt)
    st.plotly_chart(fig, use_container_width=True)

# 2. Top Models
if chart_top_model and not flt.empty:
    st.subheader("Top 15 Aircraft Models")
    model_df = flt["Model Name"].value_counts().head(15).reset_index()
    model_df.columns = ["Model", "Count"]
    fig = px.bar(model_df, x="Model", y="Count", title="Top 15 Models")
    fig.update_traces(**bar_lbl)
    fig.update_layout(xaxis_title="Model", yaxis_title="Count", **axis_fmt)
    st.plotly_chart(fig, use_container_width=True)

# 3. Top Commercial Operators
if chart_top_operator and not flt.empty:
    st.subheader("Top 15 Commercial Operators")
    op_df = (
        flt[flt["Registered Purpose"].str.contains("Commercial", na=False)]
        ["Owner Name"]
        .value_counts()
        .head(15)
        .reset_index()
    )
    op_df.columns = ["Operator", "Count"]
    op_df["Operator"] = op_df["Operator"].apply(
        lambda x: x if len(x) <= 25 else x[:22] + "…"
    )
    fig = px.bar(op_df, x="Operator", y="Count",
                 title="Top 15 Airlines / Operators")
    fig.update_traces(**bar_lbl)
    fig.update_layout(xaxis_title="Operator", yaxis_title="Count", **axis_fmt)
    st.plotly_chart(fig, use_container_width=True)

# 4. Aircraft Category Distribution
if chart_cat_dist and not flt.empty:
    st.subheader("Aircraft Category Distribution")
    fig = px.pie(flt, names="Aircraft Category",
                 hole=0.45, title="Aircraft Category Share")
    fig.update_traces(hovertemplate="%{label}: %{value} (%{percent})")
    fig.add_annotation(text=f"{total}", x=0.5, y=0.5,
                       font_size=18, showarrow=False)
    st.plotly_chart(fig, use_container_width=True)

# 5. Registered Purpose Share
if chart_purpose_share and not flt.empty:
    st.subheader("Registered Purpose Share")
    fig = px.pie(flt, names="Registered Purpose",
                 hole=0.45, title="Commercial vs Private")
    fig.update_traces(hovertemplate="%{label}: %{value} (%{percent})")
    fig.add_annotation(text=f"{total}", x=0.5, y=0.5,
                       font_size=18, showarrow=False)
    st.plotly_chart(fig, use_container_width=True)

# 6. Aircraft Age Histogram
if chart_age_hist and not flt.empty:
    st.subheader("Aircraft Age Distribution")
    fig = px.histogram(flt.dropna(subset=["Aircraft Age"]),
                       x="Aircraft Age", nbins=30,
                       title="Aircraft Age Histogram")
    fig.update_layout(xaxis_title="Aircraft Age", yaxis_title="Count",
                      **axis_fmt)
    st.plotly_chart(fig, use_container_width=True)

# 7. Aircraft by Province
if chart_prov_bar and not flt.empty:
    st.subheader("Aircraft Count by Province")
    prov_df = flt["Province (English)"].value_counts().reset_index()
    prov_df.columns = ["Province", "Count"]
    fig = px.bar(prov_df, x="Province", y="Count",
                 title="Aircraft Count by Province")
    fig.update_traces(**bar_lbl)
    fig.update_layout(xaxis_title="Province", yaxis_title="Count", **axis_fmt)
    st.plotly_chart(fig, use_container_width=True)

# 8. Registrations per Year
if chart_reg_year and not flt.empty:
    st.subheader("Registrations per Year")
    reg_df = (
        flt.dropna(subset=["Reg Year"])
        .groupby("Reg Year")
        .size()
        .reset_index(name="Count")
    )
    fig = px.line(reg_df, x="Reg Year", y="Count",
                  markers=True, title="New Registrations by Year")
    fig.update_layout(xaxis_title="Year", yaxis_title="Count", **axis_fmt)
    st.plotly_chart(fig, use_container_width=True)

# 9. Purpose Trend Over Time
if chart_purpose_trend and not flt.empty:
    st.subheader("Purpose Trend Over Time")
    trend_df = (
        flt.dropna(subset=["Reg Year"])
        .groupby(["Reg Year", "Registered Purpose"])
        .size()
        .reset_index(name="Count")
    )
    fig = px.line(trend_df, x="Reg Year", y="Count",
                  color="Registered Purpose", markers=True,
                  title="Commercial vs Private Over Time")
    fig.update_layout(xaxis_title="Year", yaxis_title="Count", **axis_fmt)
    st.plotly_chart(fig, use_container_width=True)

# --------------------------------------------------
# Drill-Down Table
# --------------------------------------------------
with st.expander("View Filtered Dataset"):
    st.dataframe(flt)

# --------------------------------------------------
# Footer
# --------------------------------------------------
st.caption(f"Dataset size after filters: {total} rows • Rendered {datetime.now():%Y-%m-%d %H:%M:%S}")
