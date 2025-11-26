import streamlit as st
import plotly.graph_objects as go
import numpy as np
import QuantLib as ql

st.title("Barrier Option Pricing & Greeks (QuantLib)")

# --- Sidebar Inputs ---
st.sidebar.header("Parameters")
spot = st.sidebar.number_input("Spot Price", value=100.0)
strike = st.sidebar.number_input("Strike", value=100.0)
barrier = st.sidebar.number_input("Barrier Level", value=120.0)
risk_free = st.sidebar.number_input("Risk-Free Rate", value=0.01)
vol = st.sidebar.number_input("Volatility", value=0.20)
dividend = st.sidebar.number_input("Dividend Yield", value=0.00)
option_type = st.sidebar.selectbox("Option Type", ["Call", "Put"])
barrier_type_str = st.sidebar.selectbox("Barrier Type", ["Up-Out", "Up-In", "Down-Out", "Down-In"], index=2)

maturity = st.sidebar.date_input("Maturity Date")

# --- QuantLib Setup ---
today = ql.Date.todaysDate()
ql.Settings.instance().evaluationDate = today
ql_maturity = ql.Date(maturity.day, maturity.month, maturity.year)

# Market data
spot_handle = ql.QuoteHandle(ql.SimpleQuote(spot))
r_handle = ql.YieldTermStructureHandle(ql.FlatForward(today, risk_free, ql.Actual365Fixed()))
d_handle = ql.YieldTermStructureHandle(ql.FlatForward(today, dividend, ql.Actual365Fixed()))
vol_handle = ql.BlackVolTermStructureHandle(ql.BlackConstantVol(today, ql.NullCalendar(), vol, ql.Actual365Fixed()))
process = ql.BlackScholesMertonProcess(spot_handle, d_handle, r_handle, vol_handle)

# Map barrier type
barrier_map = {
    "Up-Out": ql.Barrier.UpOut,
    "Up-In": ql.Barrier.UpIn,
    "Down-Out": ql.Barrier.DownOut,
    "Down-In": ql.Barrier.DownIn,
}
bar_type = barrier_map[barrier_type_str]
ql_option_type = ql.Option.Call if option_type == "Call" else ql.Option.Put

# --- Construct Barrier Option ---
payoff = ql.PlainVanillaPayoff(ql_option_type, strike)
exercise = ql.EuropeanExercise(ql_maturity)
option = ql.BarrierOption(bar_type, barrier, 0.0, payoff, exercise)
option.setPricingEngine(ql.AnalyticBarrierEngine(process))

price = option.NPV()
delta = option.delta() if price != 0 else 0.0
gamma = option.gamma() if price != 0 else 0.0
vega = option.vega() if price != 0 else 0.0
theta = option.theta() if price != 0 else 0.0
rho = option.rho() if price != 0 else 0.0

# --- Display Results ---
st.subheader("QuantLib Pricing")
st.write(f"**Price:** {price:.4f}")
st.write(f"**Delta:** {delta:.4f}")
st.write(f"**Gamma:** {gamma:.6f}")
st.write(f"**Vega:** {vega:.4f}")
st.write(f"**Theta:** {theta:.4f}")
st.write(f"**Rho:** {rho:.4f}")

# --- Payoff Plot ---
S = np.linspace(0.5 * spot, 1.5 * spot, 200)
payoff_vals = []

for s in S:
    knocked_out = False
    if "Up-Out" in barrier_type_str and s >= barrier:
        knocked_out = True
    if "Down-Out" in barrier_type_str and s <= barrier:
        knocked_out = True

    if knocked_out:
        payoff_vals.append(0)
    else:
        if option_type == "Call":
            payoff_vals.append(max(s - strike, 0))
        else:
            payoff_vals.append(max(strike - s, 0))

fig = go.Figure()
fig.add_trace(go.Scatter(x=S, y=payoff_vals, mode="lines", name="Payoff"))
fig.update_layout(title="Barrier Option Payoff", xaxis_title="Underlying Price S", yaxis_title="Payoff")

st.plotly_chart(fig)

