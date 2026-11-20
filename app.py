
import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import streamlit as st


st.set_page_config(
    page_title="Global Allocation & Rotation V1",
    page_icon="🌍",
    layout="wide",
)

DATA_DIR = Path(__file__).resolve().parent / "data"
ALLOCATION_FILE = DATA_DIR / "latest_allocation.json"
ROTATION_FILE = DATA_DIR / "latest_rotation.csv"

st.title("🌍 Global Allocation & Rotation V1")
st.caption("Price-based Global Asset Allocation Dashboard")


@st.cache_data(ttl=300)
def load_data():
    with ALLOCATION_FILE.open("r", encoding="utf-8") as f:
        allocation = json.load(f)

    rotation = pd.read_csv(ROTATION_FILE)

    return allocation, rotation


def show_percentage(value):
    try:
        return f"{float(value):.1f}%"
    except (TypeError, ValueError):
        return "N/A"


if not ALLOCATION_FILE.exists() or not ROTATION_FILE.exists():
    st.error("Scanner data files are missing.")

    st.write("Expected files:")
    st.code(
        "data/latest_allocation.json\n"
        "data/latest_rotation.csv"
    )

    st.warning(
        "Dashboard cannot display investment signals "
        "until validated scanner files are available."
    )
    st.stop()


try:
    allocation, rotation = load_data()
except (OSError, ValueError, json.JSONDecodeError, pd.errors.ParserError) as exc:
    st.error("Unable to load scanner data.")
    st.exception(exc)
    st.stop()


quality = allocation.get("data_quality", {})

critical_valid = quality.get("critical_prices_valid") is True
rotation_complete = quality.get("rotation_complete") is True

regime = allocation.get("regime", "UNKNOWN")
target = allocation.get("target")

asof = allocation.get("asof", "Unknown")
rotation_asof = allocation.get("rotation_asof", "Unknown")
lag = allocation.get("rotation_lag_sessions", "Unknown")

generated = allocation.get("generated_utc")

freshness_ok = False
age_hours = None

if generated:
    try:
        generated_dt = datetime.fromisoformat(
            str(generated).replace("Z", "+00:00")
        )

        if generated_dt.tzinfo is None:
            generated_dt = generated_dt.replace(
                tzinfo=timezone.utc
            )

        age_hours = (
            datetime.now(timezone.utc) - generated_dt
        ).total_seconds() / 3600

        freshness_ok = 0 <= age_hours <= 72

    except (ValueError, TypeError):
        pass


weights_valid = False

if isinstance(target, dict) and target:
    try:
        values = [float(v) for v in target.values()]
        weights_valid = (
            all(v >= 0 for v in values)
            and abs(sum(values) - 100) <= 0.01
        )
    except (TypeError, ValueError):
        pass


valid_regimes = {"Risk-on", "Neutral", "Risk-off"}

signal_valid = (
    critical_valid
    and rotation_complete
    and freshness_ok
    and weights_valid
    and regime in valid_regimes
    and not rotation.empty
    and allocation.get("signal_type") == "PRICE_BASED_ROTATION"
)


st.subheader("System Status")

if signal_valid:
    st.success("Validated scanner data loaded successfully.")
else:
    st.error(
        "Data is incomplete, outdated, or unverified. "
        "Do not use the allocation as a current signal."
    )


c1, c2, c3 = st.columns(3)

with c1:
    st.metric("Market Data Date", asof)

with c2:
    st.metric("Rotation Data Date", rotation_asof)

with c3:
    st.metric(
        "Data Freshness",
        f"{age_hours:.1f} hours"
        if age_hours is not None
        else "Unknown"
    )


st.divider()
st.subheader("Market Regime")

st.metric("Current Market Regime", regime)

if regime == "Risk-on":
    st.success("Risk-on environment detected.")
elif regime == "Risk-off":
    st.warning("Risk-off environment detected.")
elif regime == "Neutral":
    st.info("Neutral market environment.")
else:
    st.error("Market regime is unavailable.")


st.divider()
st.subheader("Target Asset Allocation")

if signal_valid:
    allocation_table = pd.DataFrame(
        [
            {"ETF": ticker, "Target Weight (%)": float(weight)}
            for ticker, weight in target.items()
        ]
    )

    left, right = st.columns([1, 1])

    with left:
        st.dataframe(
            allocation_table,
            hide_index=True,
            use_container_width=True,
        )

    with right:
        st.bar_chart(
            allocation_table.set_index("ETF")[
                "Target Weight (%)"
            ]
        )

    st.caption(
        "Target allocation is a model output, "
        "not an automatic trade instruction."
    )

else:
    st.warning(
        "Target allocation is hidden because "
        "the current data has not passed validation."
    )


st.divider()
st.subheader("Rotation Rankings")

st.caption(
    f"Rotation date: {rotation_asof} | "
    f"Lag: {lag} market session(s)"
)

if signal_valid:
    st.dataframe(
        rotation,
        hide_index=True,
        use_container_width=True,
    )

    csv_bytes = rotation.to_csv(index=False).encode("utf-8")

    st.download_button(
        "Download Rotation Rankings CSV",
        data=csv_bytes,
        file_name="global_rotation_rankings.csv",
        mime="text/csv",
    )
else:
    st.warning(
        "Rotation rankings are hidden until "
        "the scanner data is validated."
    )


st.divider()
st.subheader("Data Quality")

quality_table = pd.DataFrame(
    [
        {
            "Check": "Critical ETF Prices",
            "Status": "PASS" if critical_valid else "FAIL",
        },
        {
            "Check": "Rotation Completeness",
            "Status": "PASS" if rotation_complete else "FAIL",
        },
        {
            "Check": "Data Freshness (72h)",
            "Status": "PASS" if freshness_ok else "FAIL",
        },
        {
            "Check": "Allocation Weights",
            "Status": "PASS" if weights_valid else "FAIL",
        },
    ]
)

st.dataframe(
    quality_table,
    hide_index=True,
    use_container_width=True,
)

missing = quality.get("missing_latest_prices", [])
excluded = quality.get("excluded_from_rotation", {})

if missing:
    st.warning(
        "ETFs missing latest prices: "
        + ", ".join(map(str, missing))
    )

if excluded:
    st.write("Rotation exclusions:")
    st.json(excluded)

with st.expander("View Raw Scanner Data"):
    st.json(allocation)


st.divider()

st.caption(
    "This dashboard uses price-based rotation signals, "
    "not observed institutional fund flows. "
    "It does not measure actual fund inflows or outflows."
)

st.caption(
    "For research and portfolio monitoring only. "
    "Not investment advice."
)
