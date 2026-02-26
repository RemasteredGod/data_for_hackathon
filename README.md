# 🔍 PRGI Data Search - Database Management System

A comprehensive web-based application for searching and managing Press Registration General Information (PRGI) data from prgi.gov.in.

## 📋 Table of Contents

- [Features](#features)
- [System Architecture](#system-architecture)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Important Files](#important-files)
- [Usage Guide](#usage-guide)
- [CLI Tools](#cli-tools)
- [Database Schema](#database-schema)
- [Troubleshooting](#troubleshooting)

---

## ✨ Features

- **Web-Based Search Interface**: User-friendly Streamlit application
- **Advanced Filtering**: Search by title, owner, registration number, state, district, language, and class
- **Real-Time Results**: Instant search results with pagination
- **Data Export**: Download results as CSV or JSON
- **Database Statistics**: View total records, states, languages, and districts
- **CLI Management**: Command-line tools for data import and querying
- **Web Scraper**: Automated data collection from prgi.gov.in

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    PRGI Data System                      │
├─────────────────────────────────────────────────────────┤
│                                                           │
│  ┌───────────────┐      ┌──────────────┐               │
│  │  Web Scraper  │ ───> │  CSV Data    │               │
│  │  (Optional)   │      │              │               │
│  └───────────────┘      └──────┬───────┘               │
│                                 │                        │
│                                 ▼                        │
│  ┌────────────────────────────────────────┐            │
│  │   Data Manager (prgi_data_manager.py)  │            │
│  │   • Import CSV → SQLite                │            │
│  │   • CLI Query & Export                 │            │
│  └──────────────┬─────────────────────────┘            │
│                 │                                        │
│                 ▼                                        │
│  ┌────────────────────────────────────────┐            │
│  │      SQLite Database (prgi_data.db)    │            │
│  │      • 76,000+ registration records    │            │
│  │      • Indexed for fast searching      │            │
│  └──────────────┬─────────────────────────┘            │
│                 │                                        │
│                 ▼                                        │
│  ┌────────────────────────────────────────┐            │
│  │    Web App (app.py)                    │            │
│  │    • Search Interface                  │            │
│  │    • Data Visualization                │            │
│  │    • Export Functionality              │            │
│  └────────────────────────────────────────┘            │
│                 │                                        │
│                 ▼                                        │
│         User's Web Browser                              │
└─────────────────────────────────────────────────────────┘
```

---

## 🔧 Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

### Install Dependencies

```bash
pip install -r requirements.txt
```

**Dependencies:**

- `streamlit` - Web application framework
- `pandas` - Data manipulation and analysis
- `sqlite3` - Database (built-in with Python)

---

## 🚀 Quick Start

### Method 1: Using main.py (Recommended)

Simply run:

```bash
python main.py
```

This will:

1. ✅ Check and install dependencies
2. ✅ Check/create database (imports CSV if needed)
3. ✅ Launch the web application
4. 🌐 Open http://localhost:8501 in your browser

### Method 2: Manual Setup

1. **Import data into database:**

   ```bash
   python prgi_data_manager.py import --csv prgi_registration_title_details.csv --db prgi_data.db
   ```

2. **Launch web app:**

   ```bash
   streamlit run app.py
   ```

3. **Open your browser:** Navigate to http://localhost:8501

---

## 📁 Important Files

### Core Application Files

| File                     | Purpose          | Description                                 |
| ------------------------ | ---------------- | ------------------------------------------- |
| **main.py**              | 🚀 Entry Point   | Main launcher - runs the entire application |
| **app.py**               | 🌐 Web Interface | Streamlit web application with search UI    |
| **prgi_data_manager.py** | 🔧 CLI Tool      | Database management and CLI queries         |
| **scrape_prgi.py**       | 🕷️ Web Scraper   | Scrapes data from prgi.gov.in (optional)    |

### Data Files

| File                                    | Purpose        | Size                                   |
| --------------------------------------- | -------------- | -------------------------------------- |
| **prgi_registration_title_details.csv** | 📊 Source Data | ~9.3 MB CSV file                       |
| **prgi_data.db**                        | 💾 Database    | SQLite database (created on first run) |

### Configuration Files

| File                 | Purpose                     |
| -------------------- | --------------------------- |
| **requirements.txt** | Python package dependencies |
| **README.md**        | Documentation (this file)   |

---

## 📖 Usage Guide

### Web Application Features

#### 1. Search Interface

**Text Search (Contains):**

- **Title**: Search for publications by title keywords
- **Owner**: Find registrations by owner name
- **Registration Number**: Look up specific registration numbers

**Exact Match Filters:**

- **State**: Filter by publication state
- **District**: Filter by publication district
- **Language**: Filter by publication language
- **Class**: Filter by publication class

#### 2. Search Tips

```
✅ Good Searches:
- Title: "news" → Finds all titles containing "news"
- Owner: "Singh" → Finds all owners with "Singh"
- State: "Maharashtra" + Language: "Hindi" → Combined filters

❌ Less Effective:
- Too specific queries with no results
- Using exact match in text fields (Title, Owner, Reg#)
```

#### 3. Viewing Results

- Results displayed in sortable table format
- Shows up to 500 records by default (adjustable)
- Pagination with smooth scrolling

#### 4. Exporting Data

**CSV Export:**

```
Click "📥 Download CSV" → prgi_search_results.csv
```

**JSON Export:**

```
Click "📥 Download JSON" → prgi_search_results.json
```

---

## 🖥️ CLI Tools

### Import Data

```bash
python prgi_data_manager.py import \
  --csv prgi_registration_title_details.csv \
  --db prgi_data.db
```

**Output:**

```
Import complete. Inserted=76544, Skipped(duplicates)=20, Total in DB=76544
```

### Query Data (CLI)

**Basic Query:**

```bash
python prgi_data_manager.py query --db prgi_data.db --limit 10
```

**Filter by State:**

```bash
python prgi_data_manager.py query \
  --db prgi_data.db \
  --state Maharashtra \
  --limit 50
```

**Complex Query with Export:**

```bash
python prgi_data_manager.py query \
  --db prgi_data.db \
  --state "Maharashtra" \
  --language "Hindi" \
  --owner "Singh" \
  --export filtered_results.csv
```

**All Available Filters:**

```bash
--title              # Title contains (partial match)
--owner              # Owner name contains (partial match)
--registration-number # Registration number contains
--state              # State exact match
--district           # District exact match
--language           # Language exact match
--class-name         # Class exact match
--limit              # Maximum results (default: 100)
--max-print          # Max rows to print (default: 20)
--export             # Export results to CSV file
```

---

## 🗄️ Database Schema

### Table: `registrations`

| Column                | Type    | Description                  | Indexed             |
| --------------------- | ------- | ---------------------------- | ------------------- |
| `id`                  | INTEGER | Primary key (auto-increment) | ✅ Primary          |
| `sr_no`               | TEXT    | Serial number                |                     |
| `title_name`          | TEXT    | Publication title            |                     |
| `registration_number` | TEXT    | Registration number          | ✅ Unique composite |
| `owner_name`          | TEXT    | Owner/publisher name         | ✅                  |
| `pub_state_name`      | TEXT    | Publication state            | ✅                  |
| `pub_dist_name`       | TEXT    | Publication district         | ✅                  |
| `language`            | TEXT    | Publication language         | ✅                  |
| `class_name`          | TEXT    | Publication class            |                     |
| `meta_json`           | TEXT    | Additional metadata (JSON)   |                     |

**Indexes for Fast Searching:**

- Unique index on (registration_number, title_name, owner_name)
- Index on pub_state_name
- Index on pub_dist_name
- Index on language
- Index on owner_name

---

## 🔍 Web Scraper (Optional)

If you need to collect fresh data from prgi.gov.in:

```bash
python scrape_prgi.py \
  --start-page 1 \
  --end-page 77 \
  --items-per-page 1000 \
  --output fresh_data.csv
```

**Features:**

- Automatic retry on failures
- Rate limiting to avoid blocking
- Progress tracking
- Resume capability

---

## 🐛 Troubleshooting

### Problem: Database not found

**Error:**

```
Database file 'prgi_data.db' not found
```

**Solution:**

```bash
python prgi_data_manager.py import --csv prgi_registration_title_details.csv --db prgi_data.db
```

### Problem: CSV file not found

**Error:**

```
FileNotFoundError: prgi_registration_title_details.csv
```

**Solution:**

- Ensure CSV file is in the same directory
- Or specify full path: `--csv /path/to/file.csv`

### Problem: Port already in use

**Error:**

```
Port 8501 is already in use
```

**Solution:**

```bash
# Stop existing Streamlit process
pkill -f streamlit

# Or use different port
streamlit run app.py --server.port 8502
```

### Problem: Missing dependencies

**Error:**

```
ModuleNotFoundError: No module named 'streamlit'
```

**Solution:**

```bash
pip install -r requirements.txt
```

### Problem: Slow searches

**Solution:**

- Reduce result limit (slider in web app)
- Use more specific filters
- Database is indexed, but 76K+ records can be slow on complex queries

---

## 📊 Statistics

After importing data:

- **Total Records**: ~76,544
- **States**: Multiple Indian states
- **Languages**: Hindi, English, and regional languages
- **Districts**: Hundreds of districts across India

---

## 🔐 Data Privacy

This application works with publicly available data from prgi.gov.in. All data is stored locally in SQLite database on your machine.

---

## 🤝 Contributing

To add features:

1. Modify `app.py` for web interface changes
2. Modify `prgi_data_manager.py` for CLI/database changes
3. Update `README.md` with new documentation

---

## 📝 License

This project is for educational and research purposes. Please respect the terms of use of the source data from prgi.gov.in.

---

## 🆘 Support

For issues or questions:

1. Check the [Troubleshooting](#troubleshooting) section
2. Review the [Usage Guide](#usage-guide)
3. Check database with: `sqlite3 prgi_data.db "SELECT COUNT(*) FROM registrations;"`

---

## 🎯 Quick Reference Commands

```bash
# Start the application
python main.py

# Import data manually
python prgi_data_manager.py import --csv data.csv --db prgi_data.db

# Query from CLI
python prgi_data_manager.py query --db prgi_data.db --state Maharashtra

# Run web app directly
streamlit run app.py

# Scrape fresh data
python scrape_prgi.py --start-page 1 --end-page 77 --output fresh.csv
```

---

**Made with ❤️ for efficient PRGI data management**
