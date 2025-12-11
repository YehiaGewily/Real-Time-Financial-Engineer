import os
from pyflink.table import EnvironmentSettings, TableEnvironment

def main():
    # 1. Setup Environment
    env_settings = EnvironmentSettings.in_streaming_mode()
    t_env = TableEnvironment.create(env_settings)

    # 2. Configuration & Threshold
    # If DEMO_MODE is TRUE, use a small threshold (0.1) to force alerts
    demo_mode = os.environ.get('DEMO_MODE', 'FALSE').upper() == 'TRUE'
    threshold = 0.1 if demo_mode else 50.0

    print(f"Starting Arbitrage Detector... DEMO_MODE={demo_mode}, THRESHOLD=${threshold}")

    # 3. Create Source Table (Kafka)
    # Note: 'ts' is unix milliseconds. We convert to TIMESTAMP_LTZ(3)
    t_env.execute_sql("""
        CREATE TABLE crypto_prices (
            symbol STRING,
            price DOUBLE,
            source STRING,
            ts BIGINT,
            ts_ltz AS TO_TIMESTAMP_LTZ(ts, 3),
            WATERMARK FOR ts_ltz AS ts_ltz - INTERVAL '5' SECOND
        ) WITH (
            'connector' = 'kafka',
            'topic' = 'crypto-prices',
            'properties.bootstrap.servers' = 'kafka:29092',
            'properties.group.id' = 'flink-processor',
            'scan.startup.mode' = 'latest-offset',
            'format' = 'json'
        )
    """)

    # 4. Define Logic
    # We create two views, one for Coinbase, one for Binance, aggregated by 10s window
    
    # Coinbase View
    coinbase_view = t_env.sql_query("""
        SELECT 
            window_start, 
            window_end, 
            AVG(price) as cb_price
        FROM TABLE(
            TUMBLE(TABLE crypto_prices, DESCRIPTOR(ts_ltz), INTERVAL '10' SECOND)
        )
        WHERE source = 'coinbase'
        GROUP BY window_start, window_end
    """)
    t_env.create_temporary_view("coinbase_window", coinbase_view)

    # Binance View
    binance_view = t_env.sql_query("""
        SELECT 
            window_start, 
            window_end, 
            AVG(price) as bn_price
        FROM TABLE(
            TUMBLE(TABLE crypto_prices, DESCRIPTOR(ts_ltz), INTERVAL '10' SECOND)
        )
        WHERE source = 'binance'
        GROUP BY window_start, window_end
    """)
    t_env.create_temporary_view("binance_window", binance_view)

    # 5. Join and Filter
    # 6. Create Sink Table (Kafka)
    t_env.execute_sql("""
        CREATE TABLE alerts_sink (
            symbol STRING,
            coinbase_price DOUBLE,
            binance_price DOUBLE,
            spread_diff DOUBLE,
            ts TIMESTAMP(3)
        ) WITH (
            'connector' = 'kafka',
            'topic' = 'arbitrage-alerts',
            'properties.bootstrap.servers' = 'kafka:29092',
            'format' = 'json'
        )
    """)

    # 7. Execute (Insert into Sink)
    print("Submitting Job to Kafka Sink...")
    
    # We select 'BTC' as symbol since our source data implies it, and map window_end to ts
    t_env.execute_sql(f"""
        INSERT INTO alerts_sink
        SELECT 
            'BTC',
            c.cb_price,
            b.bn_price,
            ABS(c.cb_price - b.bn_price),
            c.window_end
        FROM coinbase_window c
        JOIN binance_window b ON c.window_start = b.window_start
        WHERE ABS(c.cb_price - b.bn_price) > {threshold}
    """).wait()

if __name__ == '__main__':
    main()
