# Raneen GA4 Analytics Dashboard

A production-ready Streamlit dashboard that connects directly to **Google Analytics 4** via **Windsor.ai** to display real-time e-commerce analytics.

## Features

- **Overview** — KPIs, Revenue trends, New vs Returning
- **Funnel** — Full sales funnel with drop-off analysis
- **Traffic** — Channel efficiency (CVR, Rev/Session)
- **Devices** — Mobile vs Desktop vs Tablet breakdown
- **E-Commerce** — Top products, categories, cart rates
- **Campaigns** — Google Ads campaign performance
- **Insights** — Auto-generated P1/P2/P3 action plan

## Setup

### 1. Clone the repo
```bash
git clone https://github.com/YOUR_USERNAME/GA4.git
cd GA4
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Run locally
```bash
streamlit run app.py
```

### 4. Deploy on Streamlit Cloud

1. Push to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your GitHub repo → select `app.py`
4. Deploy — no secrets needed (API key is entered in the UI)

## Getting Your Windsor API Key

1. Go to [windsor.ai](https://windsor.ai)
2. Settings → API Keys
3. Copy your key and paste it in the dashboard sidebar

## Stack

- **Streamlit** — UI framework
- **Plotly** — Interactive charts
- **Windsor.ai API** — GA4 data connector
- **Pandas** — Data processing
