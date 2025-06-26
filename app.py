import streamlit as st
import pandas as pd
import plotly.express as px
from nsepy import get_history
from datetime import date, datetime, timedelta
import requests

st.title("📈 Nifty Options Analyzer")

# ✅ Safe default expiry value (7 days ahead of today)
safe_default_expiry = date.today() + timedelta(days=7)

# Sidebar Inputs
expiry = st.sidebar.date_input("Expiry Date", min_value=date.today(), value=safe_default_expiry)

# ✅ Nifty Spot Input & ATM Strike Calculation
spot_input = st.text_input("Nifty Spot (fetch manually)", "0")
try:
    spot_value = float(spot_input)
    strike = st.sidebar.number_input("Strike Price", value=round(spot_value / 50) * 50)
except:
    st.sidebar.error("❌ Invalid spot input.")
    strike = 0  # fallback

opt_type = st.sidebar.radio("Option Type", ["CE", "PE", "Straddle"])
start = st.sidebar.date_input("Start Date (Historical)", date.today())
end = st.sidebar.date_input("End Date (Historical)", date.today())

if start > end:
    st.sidebar.error("📅 Start date must be ≤ end date")

# 📊 Fetch Historical Data
if st.sidebar.button("Fetch Historical Data"):
    df_list = []
    try:
        if opt_type in ("CE", "PE"):
            df = get_history(
                symbol="NIFTY",
                index=True,
                option_type=opt_type,
                strike_price=strike,
                expiry_date=expiry,
                start=start,
                end=end
            )
            df_list.append(df[["Close"]].rename(columns={"Close": f"{opt_type} Price"}))
        else:
            for t in ("CE", "PE"):
                df = get_history(
                    symbol="NIFTY",
                    index=True,
                    option_type=t,
                    strike_price=strike,
                    expiry_date=expiry,
                    start=start,
                    end=end
                )
                df_list.append(df[["Close"]].rename(columns={"Close": f"{t} Price"}))

        hist = pd.concat(df_list, axis=1).reset_index()
        hist["Datetime"] = pd.to_datetime(hist["Date"])
        st.subheader("📜 Historical Option Data")
        st.dataframe(hist)

        # Plotting
        fig = px.line(hist, x="Datetime", y=hist.columns.drop("Date"), title="Historical Option Prices")
        st.plotly_chart(fig)

    except Exception as e:
        st.error(f"⚠️ Failed to fetch data: {e}")

# 🔴 Real-Time ATM Straddle Estimate
st.subheader("📡 Real-Time ATM Straddle (Latest)")
try:
    url = "https://www.nseindia.com/api/option-chain-indices?symbol=NIFTY"
    data = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}).json()
    spot = data["records"]["underlyingValue"]
    atm = round(spot / 50) * 50

    for item in data["records"]["data"]:
        if item["strikePrice"] == atm:
            ce = item.get("CE", {}).get("lastPrice", 0)
            pe = item.get("PE", {}).get("lastPrice", 0)
            st.line_chart(pd.DataFrame({
                "Time": [datetime.now().strftime("%H:%M:%S")],
                "Straddle": [ce + pe]
            }).set_index("Time"))
            st.write(f"📌 Spot: {spot}, ATM Strike: {atm}, CE: {ce}, PE: {pe}, Straddle: {ce + pe}")
            break
except Exception as e:
    st.warning("⚠️ Real-time data fetch failed (possibly blocked by NSE).")
