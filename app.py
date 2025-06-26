import streamlit as st
import pandas as pd
import plotly.express as px
from nsepy import get_history
from datetime import date, datetime
import requests

st.title("📈 Nifty Options Analyzer")

# Sidebar Inputs
expiry = st.sidebar.date_input("Expiry Date", min_value=date.today(), value=date.today().replace(day=1))
strike = st.sidebar.number_input("Strike Price", value=round(float(st.text_input("Nifty Spot (fetch manually)", "0"))/50)*50)
opt_type = st.sidebar.radio("Option Type", ["CE", "PE", "Straddle"])
start = st.sidebar.date_input("Start Date (历史)", date.today())
end = st.sidebar.date_input("End Date (历史)", date.today())

if start > end: st.sidebar.error("📅 Start date must be ≤ end date")

# FX History
if st.sidebar.button("Fetch Historical Data"):
    df_list = []
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
            df_list.append(df[["Close"]].rename(columns={ "Close": f"{t} Price" }))
    hist = pd.concat(df_list, axis=1).reset_index()
    hist["Datetime"] = pd.to_datetime(hist["Date"])
    st.subheader("Historical Data")
    st.dataframe(hist)

    # Plot
    fig = px.line(hist, x="Datetime", y=hist.columns.drop("Date"), title="Historical Option Prices")
    st.plotly_chart(fig)

# Real-Time (Sample)
st.subheader("Real-Time ATM Straddle (Latest)")
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
            st.write(f"📌 Spot: {spot}, ATM Strike: {atm}, CE: {ce}, PE: {pe}, Straddle: {ce+pe}")
            break
except Exception:
    st.write("⚠️ Unable to fetch live data right now.")
