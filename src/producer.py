import json
import time
import threading
import websocket
from kafka import KafkaProducer
from kafka.errors import KafkaError

# Configuration
KAFKA_BROKER = 'kafka:29092'
KAFKA_TOPIC = 'crypto-prices'
COINBASE_WS_URL = 'wss://ws-feed.exchange.coinbase.com'
BINANCE_WS_URL = 'wss://stream.binance.com:9443/ws/btcusdt@trade'

# Initialize Kafka Producer
def get_producer():
    while True:
        try:
            producer = KafkaProducer(
                bootstrap_servers=[KAFKA_BROKER],
                value_serializer=lambda x: json.dumps(x).encode('utf-8')
            )
            print("Connected to Kafka")
            return producer
        except KafkaError as e:
            print(f"Waiting for Kafka... {e}")
            time.sleep(5)

# Shared producer instance (thread-safe for sending)
producer = get_producer()

def normalize_and_send(symbol, price, source):
    """
    Normalize data to JSON and send to Kafka.
    Format: {"symbol": "BTC", "price": <float>, "source": "source", "timestamp": <unix_ms>}
    """
    try:
        payload = {
            "symbol": symbol,
            "price": float(price),
            "source": source,
            "ts": int(time.time() * 1000)
        }
        producer.send(KAFKA_TOPIC, value=payload)
        # print(f"Sent: {payload}") # Debug logging
    except Exception as e:
        print(f"Error sending to Kafka: {e}")

def stream_coinbase():
    """
    Connects to Coinbase WebSocket and streams BTC-USD prices.
    """
    def on_open(ws):
        print("Connected to Coinbase")
        subscribe_message = {
            "type": "subscribe",
            "product_ids": ["BTC-USD"],
            "channels": ["ticker"]
        }
        ws.send(json.dumps(subscribe_message))

    def on_message(ws, message):
        data = json.loads(message)
        if data.get('type') == 'ticker' and 'price' in data:
            normalize_and_send("BTC", data['price'], "coinbase")

    def on_error(ws, error):
        print(f"Coinbase Error: {error}")

    def on_close(ws, close_status_code, close_msg):
        print("Coinbase Connection Closed")

    while True:
        try:
            print("Connecting to Coinbase...")
            ws = websocket.WebSocketApp(
                COINBASE_WS_URL,
                on_open=on_open,
                on_message=on_message,
                on_error=on_error,
                on_close=on_close
            )
            ws.run_forever()
        except Exception as e:
            print(f"Coinbase Exception: {e}")
        time.sleep(5)

def stream_binance():
    """
    Connects to Binance WebSocket and streams BTCUSDT prices.
    """
    def on_message(ws, message):
        data = json.loads(message)
        # Binance trade object has 'p' for price
        if 'p' in data:
            normalize_and_send("BTC", data['p'], "binance")

    def on_error(ws, error):
        print(f"Binance Error: {error}")

    def on_close(ws, close_status_code, close_msg):
        print("Binance Connection Closed")

    def on_open(ws):
        print("Connected to Binance")

    while True:
        try:
            print("Connecting to Binance...")
            ws = websocket.WebSocketApp(
                BINANCE_WS_URL,
                on_open=on_open,
                on_message=on_message,
                on_error=on_error,
                on_close=on_close
            )
            ws.run_forever()
        except Exception as e:
            print(f"Binance Exception: {e}")
        time.sleep(5)

if __name__ == "__main__":
    # Create threads
    t1 = threading.Thread(target=stream_coinbase, daemon=True)
    t2 = threading.Thread(target=stream_binance, daemon=True)

    # Start threads
    t1.start()
    t2.start()

    # Keep main thread alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Exiting...")