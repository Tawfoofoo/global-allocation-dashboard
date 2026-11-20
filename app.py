
import streamlit as st

st.set_page_config(
    page_title="Global Allocation & Rotation V1",
    page_icon="🌍",
    layout="wide"
)

st.title("🌍 Global Allocation & Rotation V1")
st.caption("Price-based Global Asset Allocation Dashboard")

st.info(
    "Dashboard V1 is running. "
    "Live scanner data connection is pending."
)

st.subheader("Market Regime")
st.metric("Current Status", "Pending verification")

st.subheader("Target Asset Allocation")
st.warning("Waiting for validated scanner data.")

st.subheader("Rotation Rankings")
st.info("Rotation data connection is not configured yet.")

st.subheader("Data Quality")
st.write("Scanner connection: Pending")
st.write("Critical ETF validation: Pending")
st.write("Rotation completeness: Pending")

st.divider()

st.caption(
    "This dashboard uses price-based rotation signals, "
    "not observed institutional fund flows. "
    "It is not investment advice."
)
