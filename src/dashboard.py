import streamlit as st
import json
import pandas as pd
from kafka import KafkaConsumer

# 1. Page Config
st.set_page_config(layout="wide", page_title="Real-Time Arbitrage Dashboard")

# 2. Sidebar
st.sidebar.title("Project Info")
st.sidebar.markdown("""
This project uses **Apache Flink** for real-time processing and **Kafka** for streaming.
It detects price discrepancies between Coinbase and Binance.
""")
spread_filter = st.sidebar.slider("Filter Spread ($)", min_value=0, max_value=100, value=0)

# 3. Main Layout Setup
st.title("Real-Time Arbitrage Dashboard")

# Placeholders for dynamic content
metrics_placeholder = st.empty()
chart_placeholder = st.empty()
st.subheader("Recent Alerts")
table_placeholder = st.empty()

# Footer / Architecture Info
with st.expander("System Architecture"):
    st.write("Python Producer -> Kafka (crypto-prices) -> Flink Windowing (processor.py) -> Kafka (arbitrage-alerts) -> Streamlit Dashboard")

# 4. State Management
if 'alerts' not in st.session_state:
    st.session_state['alerts'] = []

# 5. Consumer Initialization
# Note: Keep existing logic exactly as requested
try:
    consumer = KafkaConsumer(
        'arbitrage-alerts',
        bootstrap_servers=['kafka:29092'],
        auto_offset_reset='latest',
        value_deserializer=lambda x: json.loads(x.decode('utf-8'))
    )
except Exception as e:
    st.error(f"Waiting for Kafka Connection... Error: {e}")
    st.stop()

# 6. Infinite Loop
# Note: Streamlit will re-run the script on interaction (like slider change), 
# causing a reconnect. For a production app, caching the consumer is recommended,
# but we follow the request to keep logic simple here.
for message in consumer:
    alert = message.value
    
    # Update State
    st.session_state['alerts'].append(alert)
    # Keep last 100 in memory for chart
    if len(st.session_state['alerts']) > 100:
        st.session_state['alerts'].pop(0)
    
    # Prepare Data
    df = pd.DataFrame(st.session_state['alerts'])
    
    if not df.empty:
        # Get latest Alert for Metrics
        latest_alert = df.iloc[-1]
        cb_price = latest_alert.get('coinbase_price', 0.0)
        bn_price = latest_alert.get('binance_price', 0.0)
        spread = latest_alert.get('spread_diff', 0.0)
        
        # --- Top Row: Metrics ---
        with metrics_placeholder.container():
            col1, col2, col3 = st.columns(3)
            col1.metric("Coinbase Price", f"${cb_price:,.2f}")
            col2.metric("Binance Price", f"${bn_price:,.2f}")
            col3.metric("Arbitrage Spread", f"${spread:,.2f}", delta_color="normal" if spread <= 0 else "inverse") 
            # Note: "inverse" makes positive green in delta, but for just value color usually involves delta. 
            # Streamlit metric delta doesn't directly color the value unless delta is used. 
            # We'll just stick to standard metric display or use a delta if we had previous values.
            # Let's try to mimic "color green if > $0" by using delta context or just standard.
            # Actually, without a 'delta' param, it's just black/white. 
            # Let's pass the spread itself as delta to make it green/red? 
            # If spread > 0, delta=spread -> Green.
            
            # Using custom styling or just simple metric. Let's use simple metric with delta for the "Green" effect.
            col3.metric("Arbitrage Spread", f"${spread:,.2f}", f"{spread:,.2f}" if spread > 0 else None)

        # --- Middle Row: Chart ---
        with chart_placeholder.container():
            st.write("### Spread Over Time")
            st.line_chart(df[['spread_diff']])

        # --- Bottom Row: Table ---
        with table_placeholder.container():
            # Filter based on slider
            filtered_df = df[df['spread_diff'] >= spread_filter]
            
            # Show last 20 of the filtered list
            display_df = filtered_df.tail(20)[['symbol', 'spread_diff', 'ts', 'coinbase_price', 'binance_price']]
            st.dataframe(display_df, use_container_width=True)
