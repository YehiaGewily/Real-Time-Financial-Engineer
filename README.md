# ⚡ Real-Time Crypto Arbitrage Detector

![Python](https://img.shields.io/badge/Python-3.10+-blue?style=for-the-badge&logo=python) ![Apache Flink](https://img.shields.io/badge/Apache%20Flink-1.18-eb6c2d?style=for-the-badge&logo=apacheflink) ![Kafka](https://img.shields.io/badge/Kafka-3.x-black?style=for-the-badge&logo=apachekafka) ![Docker](https://img.shields.io/badge/Docker-Enabled-2496ed?style=for-the-badge&logo=docker) ![Streamlit](https://img.shields.io/badge/Streamlit-Dashboard-FF4B4B?style=for-the-badge&logo=streamlit)

A robust, real-time data engineering pipeline that detects Bitcoin (BTC) price discrepancies between **Coinbase** and **Binance** using Apache Flink and Kafka. The system processes market data in real-time, identifies arbitrage opportunities, and alerts users via Discord and a live Streamlit dashboard.

---

## 🏗️ Architecture

The pipeline consists of four main microservices orchestrated via Docker Compose:

1.  **Consumer/Producer (`src/producer.py`)**:
    *   Connects to **Coinbase** and **Binance** WebSockets.
    *   Normalizes real-time trade data.
    *   Publishes to Kafka topic `crypto-prices`.

2.  **Stream Processor (`src/processor.py`)**:
    *   **Apache Flink** (PyFlink) job.
    *   Consumes from `crypto-prices`.
    *   Applies **Tumbling Windows** (10 seconds) to aggregate prices.
    *   Joins streams from both exchanges.
    *   Detects spreads > $50.
    *   Sinks alerts to Kafka topic `arbitrage-alerts`.

3.  **Alerter Service (`src/alerter.py`)**:
    *   Consumes from `arbitrage-alerts`.
    *   Sends real-time notifications to a **Discord Webhook**.

4.  **Dashboard (`src/dashboard.py`)**:
    *   **Streamlit** application.
    *   Consumes `arbitrage-alerts` to visualize price spreads and alert history in real-time.

---

## 🚀 Quick Start

### 1. Prerequisites
*   **Docker** & **Docker Compose** installed.
*   **Git** installed.

### 2. Setup Project Structure
Ensure your workspace directory looks like this:
```
.
├── docker-compose.yml
├── Dockerfile
├── jars/
│   └── flink-sql-connector-kafka-3.0.1-1.18.jar  <-- Download manually if missing
└── src/
    ├── producer.py
    ├── processor.py
    ├── alerter.py
    └── dashboard.py
```
> **Note**: The `flink-sql-connector-kafka` JAR is required for Flink to talk to Kafka.

### 3. Run the System
Build the custom images and start the services:

```bash
docker-compose up --build -d
```

### 4. Verify Output

#### 📊 Dashboard
Access the real-time dashboard at:
👉 **[http://localhost:8501](http://localhost:8501)**

#### 💬 Discord Alerts
If the spread exceeds the threshold (or in Demo Mode), alerts will be sent to the configured Discord Webhook.

#### 📝 Flink Logs
To view the underlying processing logs:
```bash
docker logs -f taskmanager
```

---

## ⚙️ Configuration & Demo Mode

### Demo Mode
To force alerts for testing (even if there is no profitable spread), you can enable **DEMO_MODE**. This effectively lowers the detection threshold to **$0.1**.

1.  Open `docker-compose.yml`.
2.  Find the `job-submitter` service.
3.  Set `DEMO_MODE=TRUE`:
    ```yaml
    job-submitter:
      environment:
        - DEMO_MODE=TRUE
    ```
4.  Restart the services: `docker-compose up -d`

---

## 📂 Project Structure

| File/Folder | Description |
| :--- | :--- |
| `src/producer.py` | Python script to fetch WS data and push to Kafka. |
| `src/processor.py` | PyFlink SQL job for windowing and arbitrage logic. |
| `src/alerter.py` | Service to push alerts to Discord. |
| `src/dashboard.py` | Streamlit web app for visualization. |
| `docker-compose.yml` | Orchestrates Zookeeper, Kafka, JobManager, TaskManager, and App services. |
| `Dockerfile` | Custom image definition for Python dependencies. |

---

## 🛠️ Troubleshooting

*   **"Leader Not Available" in Kafka Logs**:
    *   This is common during startup. The services are designed to retry and should recover automatically after 30-60 seconds.
*   **Dashboard shows "Waiting for Kafka"**:
    *   Ensure the Kafka container is healthy (`docker ps`).
*   **No Alerts**:
    *   Real arbitrage is rare! Enable **DEMO_MODE** to verify the pipeline is working.
