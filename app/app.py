import os
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="Hotel Booking Dashboard",
                   page_icon="🏨", layout="wide")

MONTHS = ["January", "February", "March", "April", "May", "June", "July",
          "August", "September", "October", "November", "December"]


@st.cache_data
def load_data():
    path = os.path.join(os.path.dirname(__file__), "..",
                        "dataset", "cleaned_hotel_bookings.csv")
    return pd.read_csv(path, parse_dates=["arrival_date", "reservation_status_date"])


df = load_data()

# ---------------- Title ----------------
st.title("🏨 Hotel Booking Demand Dashboard")
st.caption("Devixo Solutions | AI/ML Internship Program | Task 01 | Data: Kaggle Hotel Booking Demand (cleaned)")

# ---------------- Sidebar filters ----------------
st.sidebar.header("Filters")
all_hotels = sorted(df["hotel"].unique())
all_years = sorted(df["arrival_year"].unique())
all_segments = sorted(df["market_segment"].unique())

hotels = st.sidebar.multiselect("Hotel", all_hotels, default=all_hotels)
years = st.sidebar.multiselect("Arrival year", all_years, default=all_years)
segments = st.sidebar.multiselect(
    "Market segment", all_segments, default=all_segments)

rate_min, rate_max = int(df["avg_daily_rate"].min()), int(
    df["avg_daily_rate"].max())
rate = st.sidebar.slider("Average daily rate", rate_min,
                         rate_max, (rate_min, rate_max))
status = st.sidebar.radio("Cancellation status", [
                          "All", "Cancelled", "Not Cancelled"])

f = df[
    df["hotel"].isin(hotels)
    & df["arrival_year"].isin(years)
    & df["market_segment"].isin(segments)
    & df["avg_daily_rate"].between(rate[0], rate[1])
]
if status != "All":
    f = f[f["cancellation_status"] == status]

if f.empty:
    st.warning(
        "No bookings match the selected filters. Please change the filters.")
    st.stop()

st.sidebar.markdown("---")
st.sidebar.download_button("Download filtered data (CSV)",
                           f.to_csv(index=False).encode("utf-8"),
                           "filtered_bookings.csv", "text/csv")

# ---------------- KPIs ----------------
c1, c2, c3, c4, c5, c6 = st.columns(6)
c1.metric("Total Bookings", f"{len(f):,}")
c2.metric("Total Columns", df.shape[1])
c3.metric("Cancellation Rate", f"{f['is_cancelled'].mean() * 100:.2f}%")
c4.metric("Avg Daily Rate", f"{f['avg_daily_rate'].mean():.2f}")
c5.metric("Avg Lead Time", f"{f['lead_time'].mean():.1f} days")
c6.metric("Avg Stay (nights)", f"{f['total_nights'].mean():.2f}")

tab1, tab2, tab3, tab4 = st.tabs(
    ["📋 Overview", "📊 Charts", "🔗 Correlation", "💡 Key Insights"])

# ---------------- Tab 1: Overview ----------------
with tab1:
    st.subheader("Dataset Overview")
    a, b, c = st.columns(3)
    a.metric("Records (after filters)", f"{len(f):,}")
    b.metric("Records (full cleaned data)", f"{len(df):,}")
    c.metric("Missing values", int(f.isnull().sum().sum()))
    st.markdown("**Sample records**")
    st.dataframe(f.head(100), use_container_width=True)
    st.markdown("**Summary statistics (numerical columns)**")
    num_cols = ["lead_time", "avg_daily_rate", "total_nights", "total_guests",
                "special_requests", "booking_changes"]
    st.dataframe(f[num_cols].describe().round(2), use_container_width=True)

# ---------------- Tab 2: Charts ----------------
with tab2:
    st.subheader("Interactive Charts")
    col1, col2 = st.columns(2)

    m = f.groupby(["arrival_month", "hotel"]
                  ).size().reset_index(name="bookings")
    fig = px.bar(m, x="arrival_month", y="bookings", color="hotel", barmode="group",
                 category_orders={"arrival_month": MONTHS},
                 title="Bookings by Arrival Month",
                 labels={"arrival_month": "Arrival Month", "bookings": "Number of Bookings"})
    col1.plotly_chart(fig, use_container_width=True)

    r = f.groupby(["arrival_month", "hotel"])[
        "avg_daily_rate"].mean().reset_index()
    r["month_num"] = r["arrival_month"].map(
        {m: i for i, m in enumerate(MONTHS)})
    r = r.sort_values("month_num")
    fig = px.line(r, x="arrival_month", y="avg_daily_rate", color="hotel", markers=True,
                  category_orders={"arrival_month": MONTHS},
                  title="Average Daily Rate by Month",
                  labels={"arrival_month": "Arrival Month", "avg_daily_rate": "Average Daily Rate"})
    col2.plotly_chart(fig, use_container_width=True)

    col3, col4 = st.columns(2)
    seg = (f.groupby("market_segment")[
           "is_cancelled"].mean() * 100).reset_index()
    seg.columns = ["market_segment", "cancellation_rate"]
    seg = seg.sort_values("cancellation_rate", ascending=False)
    fig = px.bar(seg, x="market_segment", y="cancellation_rate", text_auto=".1f",
                 title="Cancellation Rate (%) by Market Segment",
                 labels={"market_segment": "Market Segment", "cancellation_rate": "Cancellation Rate (%)"})
    col3.plotly_chart(fig, use_container_width=True)

    fig = px.histogram(f, x="lead_time", color="cancellation_status", nbins=50,
                       barmode="overlay", opacity=0.7,
                       title="Lead Time Distribution by Cancellation Status",
                       labels={"lead_time": "Lead Time (days)"})
    col4.plotly_chart(fig, use_container_width=True)

    col5, col6 = st.columns(2)
    samp = f.sample(min(5000, len(f)), random_state=42)
    fig = px.scatter(samp[samp["total_guests"] <= 6], x="total_guests", y="avg_daily_rate",
                     color="hotel", opacity=0.5,
                     title="Total Guests vs Average Daily Rate (sample)",
                     labels={"total_guests": "Total Guests", "avg_daily_rate": "Average Daily Rate"})
    col5.plotly_chart(fig, use_container_width=True)

    top = f["country"].value_counts().head(10).reset_index()
    top.columns = ["country", "bookings"]
    fig = px.bar(top, x="bookings", y="country", orientation="h",
                 title="Top 10 Guest Countries",
                 labels={"bookings": "Number of Bookings", "country": "Country"})
    fig.update_yaxes(autorange="reversed")
    col6.plotly_chart(fig, use_container_width=True)

    share = f["market_segment"].value_counts().reset_index()
    share.columns = ["market_segment", "bookings"]
    fig = px.pie(share, names="market_segment", values="bookings",
                 title="Share of Bookings by Market Segment")
    st.plotly_chart(fig, use_container_width=True)

# ---------------- Tab 3: Correlation ----------------
with tab3:
    st.subheader("Correlation Heatmap")
    corr_cols = ["is_cancelled", "lead_time", "total_nights", "total_guests", "avg_daily_rate",
                 "special_requests", "booking_changes", "previous_cancellations",
                 "is_repeated_guest", "parking_spaces", "days_in_waiting_list"]
    corr = f[corr_cols].corr().round(2)
    fig = px.imshow(corr, text_auto=True, color_continuous_scale="RdBu_r",
                    zmin=-1, zmax=1, aspect="auto",
                    title="Correlation Matrix of Numerical Variables")
    fig.update_layout(height=650)
    st.plotly_chart(fig, use_container_width=True)
    st.caption(
        "+1 = perfect positive, 0 = no linear relationship, -1 = perfect negative.")

# ---------------- Tab 4: Insights ----------------
with tab4:
    st.subheader("Key Insights (from the full cleaned dataset)")
    st.markdown("""
- About **27.69%** of bookings are cancelled; the City Hotel (30.21%) cancels more than the Resort Hotel (23.72%).
- **Online TA** makes up 59.21% of bookings and has the highest cancellation rate (35.55%) among main segments.
- Cancelled bookings were made earlier (**105.8 days** ahead) than completed bookings (**70.5 days**).
- Demand and prices peak in **August** (11,194 bookings, average rate 151.70) and are lowest in **January**.
- The strongest correlation is between **total guests and daily rate (0.41)**; all correlations with cancellation are weak.
- Median lead time (50 days) describes a typical booking better than the mean (80.31 days) because the data is right-skewed.
""")
