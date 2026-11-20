
import streamlit as st

st.set_page_config(
    page_title="Global Allocation & Rotation V1",
    layout="wide"
)

st.title("Global Asset Allocation & Rotation V1")
st.caption("Private dashboard | Price-based rotation")

st.info(
    "Dashboard initialized. "
    "Secure scan-data connection is not configured yet."
)

st.subheader("System status")
st.write("Scanner: Global Allocation & Rotation V1")
st.write("Data connection: Pending")
st.write("Portfolio recommendations: Not available yet")

st.warning(
    "Do not use allocation signals until "
    "market data has been validated."
)
