# TikTok Affiliate Analyzer 🚀

> **Status: ⚠️ Active Development** — This project is under active development. Features, APIs, and database schemas may change without notice. Use in production at your own risk.

A comprehensive **TikTok Affiliate Marketing** management system built with Flask. This application helps manage the full lifecycle of TikTok affiliate content — from product research and opportunity analysis to video creation, upload scheduling, and post-performance tracking.

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Key Features](#-key-features)
- [Tech Stack](#-tech-stack)
- [Project Structure](#-project-structure)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Database Schema](#-database-schema)
- [Modules Breakdown](#-modules-breakdown)
- [Router Map](#-router-map)
- [API Endpoints](#-api-endpoints)
- [Development](#-development)
- [License](#-license)

---

## 🎯 Overview

**TikTok Affiliate Analyzer** is a full-stack web application designed for TikTok Shop affiliate marketers. It integrates multiple workflows into a single dashboard:

1. **Research** — Analyze TikTok Shop products for affiliate potential using data-driven opportunity scoring
2. **Create** — Process raw videos through an automated pipeline (denoise, upscale, add watermarks, zoom, add sound)
3. **Schedule** — Plan and batch-schedule video uploads across multiple TikTok creator accounts
4. **Upload** — Automate TikTok video uploads using Android device control (ADB/WebSocket)
5. **Monitor** — Track video performance with daily statistics and growth metrics

---

## ✨ Key Features

### 🔍 Product Analysis
- **Scrape** TikTok Shop product data (title, price, rating, sales, commission)
- **Opportunity Engine** — Multi-factor opportunity scoring:
  - `demand_score` — Market demand estimation
  - `competition_score` — Competitive landscape analysis
  - `conversion_score` — Conversion potential
  - `commission_score` — Commission attractiveness
  - `overall_score` — Weighted composite score (0–100)
- **LLM Integration** — AI-powered product analysis using OpenAI/OpenRouter API
- **OCR Support** — Extract text from product screenshots for analysis
- **Compare Products** — Side-by-side product comparison

### 📊 Video Analytics (NEW)
- **Dashboard** — Video analytics with Social Blade-style growth metrics
- **Thumbnail Caching** — Auto-download and resize TikTok video thumbnails (120px max height)
- **Duration Tracking** — Store and display video duration in `m:ss` format
- **Growth Calculation** — Per-video growth for Views, Likes, Comments, Shares, Favorites
- **Daily Snapshots** — Historical data preserved in `tiktok_video_stats` table
- **Efficient Queries** — Uses `ROW_NUMBER()` window function for fast 2-snapshot lookup

### 📈 Video Performance
- **TikTok Scraper** — CDP-based scraper using injected fetch interceptors (no API keys needed)
- **DOM Ordering** — Preserves TikTok's original video order (pinned videos first)
- **Auto-Matching** — Matches scraped videos to upload jobs using time proximity
- **Performance Summary** — Aggregate views/likes across all videos

### 🎬 Video Pipeline
- **Video2X Integration** — AI upscaling using Real-ESRGAN / Real-CUGAN / RIFE
- **Denoising** — Video noise reduction pipeline
- **Zoom Effects** — Automated zoom-in/zoom-out transitions
- **Sound Addition** — Add background audio to processed videos
- **Watermarking** — Overlay still image watermarks on videos

### 🤖 TikTok Uploader (Android-based)
- **ADB Control** — Direct Android device control via ADB
- **WebSocket** — Real-time upload progress monitoring
- **Accessibility Service** — Android accessibility-based UI automation
- **Multi-Account** — Supports multiple TikTok creator accounts

### 📅 Schedule Management
- **Batch Scheduling** — Schedule video uploads in batches with configurable intervals
- **Multiple Strategies** — Fixed time, interval-based, weekly recurring, pattern-based
- **Import Analyzer** — Analyze existing video folders for scheduling

### 👥 Creator Management
- **Multi-Creator** — Manage multiple TikTok creator profiles
- **Active/Inactive** — Toggle creator status
- **Per-Creator Workflows** — Custom workflows for different creators

---

## 🛠 Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3, Flask 3.1 |
| Database | MySQL / MariaDB 10.4+ (via PyMySQL) |
| Template | Jinja2 with Tabler UI (Bootstrap 5) |
| Scraping | Selenium + CDP (Chrome DevTools Protocol) |
| Image Processing | Pillow (PIL) |
| Video Processing | FFmpeg, Video2X, OpenCV |
| Device Control | ADB (Android Debug Bridge), WebSocket |
| AI Integration | OpenAI API, OpenRouter API |
| Real-time | Flask-Sock (WebSocket) |
| Frontend Icons | Tabler Icons |

---

## 📁 Project Structure

```
tiktok_affiliate_analyze/
├── app.py                          # Flask application entry point
├── requirements.txt                # Python dependencies
├── config/                         # Configuration files
├── includes/                       # Core business logic modules
│   ├── mysql.py                    # Database layer (all MySQL operations)
│   ├── config_loader.py            # Configuration loader
│   ├── logFX.py                    # Colored logging utility
│   ├── opportunity.py              # Opportunity analysis engine
│   ├── product_analyzer.py         # Product analysis logic
│   ├── compare_products.py         # Product comparison engine
│   ├── tiktok_scrape_videos/       # TikTok video scraper module
│   │   ├── scraper.py              # Main scraper engine
│   │   └── driver.py               # Selenium driver setup
│   ├── video_analytics/            # Video Analytics module (NEW)
│   │   ├── __init__.py
│   │   └── video_analytics.py      # Service Layer (business logic)
│   ├── video_performance/          # Video Performance module
│   │   ├── scanner.py, matching.py, service.py, manager.py
│   ├── video_pipeline/             # Video processing pipeline
│   │   ├── processor.py            # Main video processor
│   │   ├── decode_video.py, upscale_video.py
│   │   ├── zoom_video.py, add_sound.py
│   ├── android/                    # Android device control
│   │   ├── device.py, command.py, accessibility.py
│   │   ├── screenshot.py, file.py, websocket.py
│   ├── jobs/                       # Job runners & workflows
│   │   ├── job_runner.py, workflow.py
│   │   └── workflows_*.py          # Per-creator workflows
│   ├── schedule/                   # Schedule algorithms
│   │   ├── scheduler.py, algorithms.py, batch.py
│   └── opportunity/                # Opportunity sub-modules
│       ├── engine.py               # Scoring engine
│       ├── demand.py, competition.py, conversion.py
│       └── commission.py, explain.py
├── routers/                        # Flask Blueprint routes
│   ├── dashboard/                  # Main dashboard
│   ├── creator/                    # Creator-specific pages
│   │   ├── video_analytics.py      # Video Analytics page (NEW)
│   │   ├── video_performance.py, product_exposure.py
│   │   └── report.py
│   ├── product/, product_list/
│   ├── product_rating/             # Product rating & analysis
│   ├── tiktok_uploader/, upload_video/
│   ├── production_monitor/
│   ├── video_pipeline/, setting/
│   └── websocket/
├── templates/                      # Jinja2 HTML templates
│   ├── layouts/base.html           # Base layout (Tabler UI)
│   ├── dashboard/, creator/
│   ├── product/, product_list/
│   ├── video_analytics/            # Video Analytics template (NEW)
│   ├── video_performance/
│   └── ...
├── static/                         # Static assets
│   ├── css/, js/, img/, avatar/
│   ├── products/                   # Product screenshots
│   └── videos/                     # Cached video thumbnails (NEW)
├── data/                           # Per-creator data files
├── upload/                         # Upload directory
└── debug/                          # Debug artifacts
```

---

## 🔧 Installation

### Prerequisites

- **Python 3.10+**
- **MySQL 8.0+ / MariaDB 10.4+** (with `ROW_NUMBER()` window function support)
- **Google Chrome / Chromium** (for TikTok scraping)
- **FFmpeg** (for video processing)
- **Android Debug Bridge (ADB)** (optional, for automated uploads)

### Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/tiktok_affiliate_analyze.git
   cd tiktok_affiliate_analyze
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # or
   venv\Scripts\activate     # Windows
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure database**
   ```bash
   # Edit config to set your MySQL connection details
   # Required tables: creators, tiktok_products,
   # tiktok_product_analysis, tiktok_product_llm_analysis,
   # tiktok_videos, tiktok_video_stats, upload_jobs, schedule_batches
   ```

5. **Set up Chromium profile**
   ```bash
   mkdir chromium
   # Login to TikTok manually using the profile first
   ```

6. **Run the application**
   ```bash
   python app.py
   ```

---

## ⚙️ Configuration

Application settings managed in `config/`. Key settings:

| Key | Description | Default |
|-----|-------------|---------|
| `mysql.host` | MySQL host | `localhost` |
| `mysql.user` | MySQL user | `root` |
| `mysql.password` | MySQL password | — |
| `mysql.database` | MySQL database | `tiktok_affiliate` |
| `host` | Flask bind host | `0.0.0.0` |
| `port` | Flask port | `5000` |
| `debug` | Debug mode | `true` |
| `secret_key` | Flask session secret | — |

---

## 🗄 Database Schema

### Core Tables

| Table | Purpose |
|-------|---------|
| `creators` | TikTok creator accounts |
| `tiktok_products` | TikTok Shop products |
| `tiktok_product_analysis` | Product opportunity analysis results |
| `tiktok_product_llm_analysis` | AI-powered product analysis |
| `tiktok_videos` | Video metadata (NO stats columns) |
| `tiktok_video_stats` | Daily video snapshots (views, likes, comments, shares, favorites) |
| `upload_jobs` | Scheduled video upload jobs |
| `schedule_batches` | Batch scheduling records |

### Key Design Decisions

**`tiktok_videos` — METADATA ONLY**
- Stores: `video_id`, `creator_id`, `video_url`, `caption`, `upload_time`, `duration`, `match_score`
- **No** views/likes/comments/shares columns
- Statistics stored separately in `tiktok_video_stats`

**`tiktok_video_stats` — DAILY SNAPSHOTS**
- One record per video per day
- Columns: `views`, `likes`, `comments`, `shares`, `favorites`
- Enables growth calculation between snapshots

---

## 📦 Modules Breakdown

### 🔬 Product Analysis Engine

Multi-factor opportunity scoring system for TikTok Shop products.

**Scoring Factors:**
```
Opportunity Score (0-100)
├── Demand Score       — Market demand estimation
├── Competition Score  — Competitive intensity
├── Conversion Score   — Sales conversion potential
├── Commission Score   — Commission rate attractiveness
└── Overall Score      — Weighted composite
```

### 📊 Video Analytics (NEW)

Social Blade-style dashboard for tracking video performance over time.

**Key Capabilities:**
- **Thumbnail Caching** — Auto-downloads thumbnails from TikTok, resizes to 120px height using Pillow (LANCZOS), saves as optimized JPG
- **Duration Tracking** — Captures duration from TikTok API, displays as `m:ss`
- **Growth Metrics** — Per-video growth for 5 metrics: Views, Likes, Comments, Shares, Favorites
- **Historical Snapshots** — Each scan adds a snapshot; growth = latest - previous

**Architecture:**
```
Router (Thin Controller)
  ├── GET  /creator/<id>/video_analytics
  └── POST /creator/<id>/video_analytics/update
        ↓
Service Layer (VideoAnalyticsService)
  ├── index()           → read + prepare data
  ├── _read_analytics() → query 2 latest snapshots per video
  └── update_creator_analytics() → scrape + sync
        ↓
Database
  ├── tiktok_videos         (metadata + duration)
  └── tiktok_video_stats    (daily snapshots + favorites)
        ↓
Template (Jinja2 + Tabler UI)
```

**Growth Calculation:**
```sql
-- Uses ROW_NUMBER() to get 2 latest snapshots per video
ROW_NUMBER() OVER (
    PARTITION BY video_id
    ORDER BY snapshot_time DESC
) AS rn
-- rn=1 → current stats
-- rn=2 → previous stats (for growth calculation)
```

### 📈 Video Performance

Custom TikTok scraper with CDP-based fetch interception.

**Scraping Method:**
1. **CDP Injection** — Injects fetch interceptor via Chrome DevTools Protocol
2. **API Capture** — Intercepts TikTok's `/api/post/item_list` responses
3. **DOM Ordering** — Captures DOM video order (preserves pinned first)
4. **Auto-Matching** — Links scraped videos to upload jobs via time proximity

### 🎬 Video Pipeline

```
Input Video → Decode → Denoise → Upscale (AI) → Zoom → Add Sound → Output
```

### 🤖 TikTok Uploader (Android)

- ADB-based Android device control
- Accessibility service UI automation
- Real-time WebSocket progress monitoring
- Multi-account support

### 📅 Schedule Management

| Strategy | Description |
|----------|-------------|
| `fixed_time` | Upload at specific date/time |
| `interval` | Upload every N hours/days |
| `weekly` | Upload on specific weekdays |
| `pattern` | Custom time pattern |

---

## 🗺 Router Map

| Route | Method | Description |
|-------|--------|-------------|
| `/` | GET | Main dashboard |
| `/creator` | GET | Creator list |
| `/creator/<id>` | GET | Creator detail |
| `/creator/<id>/video_analytics` | GET | **Video Analytics page** |
| `/creator/<id>/video_analytics/update` | POST | **Trigger analytics update** |
| `/creator/<id>/video_performance` | GET | Video Performance page |
| `/creator/<id>/product_exposure` | GET | Product exposure analysis |
| `/creator/<id>/report` | GET | Creator reports |
| `/product/<id>` | GET | Product detail & analysis |
| `/product_list` | GET | Product list management |
| `/product_rating` | GET | Product rating dashboard |
| `/product_rating/form` | GET | Product analysis form |
| `/prepare_upload` | GET | Upload preparation |
| `/tiktok_uploader` | GET | TikTok uploader interface |
| `/upload_video` | GET | Video upload management |
| `/production_monitor` | GET | Production monitoring |
| `/video_pipeline` | GET | Video pipeline interface |
| `/setting` | GET | Application settings |
| `/analyze_by_phone` | GET | Phone-based analysis |

---

## 🚧 Development Status

### ✅ Implemented
- [x] Product scraping & opportunity analysis
- [x] LLM integration for AI analysis
- [x] Video performance tracking with daily snapshots
- [x] TikTok scraper with CDP interceptor
- [x] Video pipeline (upscale, zoom, sound)
- [x] Android-based TikTok uploader
- [x] Batch scheduling (fixed, interval, weekly, pattern)
- [x] Creator management
- [x] **Video Analytics dashboard** (growth, thumbnails, duration)
- [x] **Thumbnail caching** with Pillow resize
- [x] **Growth calculation** from 2 latest snapshots

### 🔄 In Progress
- [ ] Video Analytics: chart visualization (views timeline)
- [ ] Video Analytics: aggregate growth across all videos
- [ ] Performance optimization for large datasets
- [ ] Unit tests & integration tests
- [ ] Docker deployment support

### 📋 Planned
- [ ] Multi-language support (i18n)
- [ ] API documentation (Swagger/OpenAPI)
- [ ] Role-based access control
- [ ] Webhook notifications
- [ ] Mobile-responsive improvements

---

## 🤝 Contributing

This project is in active development. Contributions, bug reports, and feature requests are welcome!

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

This project is for educational and personal use. All rights reserved.

---

## ⚠️ Disclaimer

This tool is intended for **educational purposes only**. Users are responsible for complying with TikTok's Terms of Service. The developers assume no liability for misuse of this software.

---

*Built with ❤️ for TikTok Shop Affiliate Marketers*
