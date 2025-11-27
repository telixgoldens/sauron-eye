# Sauron Eye - Babylon Analytics

**The All-Seeing Lens for the Babylon Blockchain.**

Sauron Eye is a production-ready analytics and forensic platform designed for the Babylon Protocol. It combines real-time blockchain indexing with AI-driven forensic analysis to detect "Smart Money," wash trading, and Sybil attacks.

##  Key Features

* **Dual-Layer Indexing:** Captures Babylon (Cosmos SDK) events and correlates them with BTC Staking.
* **🕵️ Wallet Inspector:** Deep-dive profiling of any address.
* **Forensic AI:** An embedded AI Agent (powered by LangChain + GPT-4) that writes psychological profiles of wallet owners based on transaction math.
* **Graph Theory Detection:** Uses NetworkX to mathematically prove "Fan-Out" (Sybil) and "Cycle" (Wash Trading) patterns.
* **Live Dashboard:** Built with Streamlit for real-time monitoring.

## Tech Stack

* **Ingestion:** Python (Async/Httpx)
* **Database:** PostgreSQL (Dockerized)
* **Visuals:** Streamlit + Plotly
* **Intelligence:** LangChain + OpenAI + Amazon Q Developer
* **Infrastructure:** Docker Compose

## Quick Start

### 1. Prerequisites
* Docker Desktop
* Python 3.9+
* OpenAI API Key

### 2. Installation
```bash

git clone [https://github.com/telixgoldens/sauron-eye.git](https://github.com/telixgoldens/sauron-eye.git)
cd sauron-eye

# Setup Environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt