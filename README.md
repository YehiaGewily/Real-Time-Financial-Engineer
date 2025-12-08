# Real-Time Crypto Arbitrage Detector

A real-time data engineering project detecting Bitcoin price discrepancies between Coinbase and Binance using Apache Flink and Kafka.

## Quick Start

### 1. Prerequisites
- Docker & Docker Compose installed.

### 2. Setup Project Structure
Ensure your workspace directory looks like this:
```
.
├── docker-compose.yml
├── Dockerfile
├── jars/
│   └── flink-sql-connector-kafka-3.0.0-1.18.jar  <-- You need to download this
└── src/
    ├── producer.py
    └── processor.py
```

### 3. Download Dependencies
You **must** place the manually downloaded Flink Kafka Connector (`flink-sql-connector-kafka-3.1.0-1.18.jar`) in the `jars/` folder before running.

*Note: Since you have manually downloaded version 3.1.0, ensure it is present in `jars/`.*

### 4. Run the System
Build the custom images and start the services:

```bash
docker-compose up --build -d
```

### 5. Verify Output
Data flows as follows: `WebSockets -> producer -> Kafka -> Flink (processor) -> TaskManager Stdout`.

To view the arbitrage alerts (or "NORMAL" status), you need to view the logs of the Flink TaskManager container.

```bash
# View logs and follow (-f)
docker logs -f taskmanager
```

*Note: It may take 30-60 seconds for the containers to fully initialize and the first 10-second window to close.*

### 6. Control Parameters
- **DEMO_MODE**: To force alerts (by lowering the threshold to $0.1), edit `docker-compose.yml`:
  ```yaml
  job-submitter:
    # ...
    environment:
      DEMO_MODE: "TRUE"
  ```
