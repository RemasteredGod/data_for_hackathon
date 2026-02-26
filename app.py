#!/usr/bin/env python3
"""PRGI Data Search Web Application

Run with: streamlit run app.py
"""

import streamlit as st
import sqlite3
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any
import json

# Set page config
st.set_page_config(
    page_title="PRGI Data Search",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

TABLE_NAME = "registrations"
DEFAULT_DB = "prgi_data.db"


@st.cache_resource
def get_db_connection(db_path: str):
    """Create a cached database connection."""
    if not Path(db_path).exists():
        st.error(f"Database file '{db_path}' not found. Please import data first.")
        return None
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def get_unique_values(conn: sqlite3.Connection, column: str) -> List[str]:
    """Get unique values from a column for filter dropdowns."""
    try:
        cursor = conn.execute(f"SELECT DISTINCT {column} FROM {TABLE_NAME} WHERE {column} != '' ORDER BY {column}")
        return [""] + [row[0] for row in cursor.fetchall()]
    except:
        return [""]


def build_search_query(filters: Dict[str, str]) -> tuple:
    """Build SQL query based on search filters."""
    clauses = []
    params = []
    
    # Title search (contains)
    if filters.get('title'):
        clauses.append("LOWER(title_name) LIKE LOWER(?)")
        params.append(f"%{filters['title']}%")
    
    # Owner search (contains)
    if filters.get('owner'):
        clauses.append("LOWER(owner_name) LIKE LOWER(?)")
        params.append(f"%{filters['owner']}%")
    
    # Registration number search (contains)
    if filters.get('registration_number'):
        clauses.append("LOWER(registration_number) LIKE LOWER(?)")
        params.append(f"%{filters['registration_number']}%")
    
    # State (exact match)
    if filters.get('state'):
        clauses.append("LOWER(pub_state_name) = LOWER(?)")
        params.append(filters['state'])
    
    # District (exact match)
    if filters.get('district'):
        clauses.append("LOWER(pub_dist_name) = LOWER(?)")
        params.append(filters['district'])
    
    # Language (exact match)
    if filters.get('language'):
        clauses.append("LOWER(language) = LOWER(?)")
        params.append(filters['language'])
    
    # Class (exact match)
    if filters.get('class_name'):
        clauses.append("LOWER(class_name) = LOWER(?)")
        params.append(filters['class_name'])
    
    where_clause = " AND ".join(clauses) if clauses else "1=1"
    return where_clause, params


def search_database(conn: sqlite3.Connection, filters: Dict[str, str], limit: int = 1000) -> pd.DataFrame:
    """Search the database with given filters and return results as DataFrame."""
    where_clause, params = build_search_query(filters)
    
    query = f"""
        SELECT 
            sr_no,
            title_name,
            registration_number,
            owner_name,
            pub_state_name,
            pub_dist_name,
            language,
            class_name
        FROM {TABLE_NAME}
        WHERE {where_clause}
        ORDER BY id DESC
        LIMIT ?
    """
    params.append(limit)
    
    df = pd.read_sql_query(query, conn, params=params)
    return df


def get_stats(conn: sqlite3.Connection) -> Dict[str, int]:
    """Get database statistics."""
    stats = {}
    stats['total_records'] = conn.execute(f"SELECT COUNT(*) FROM {TABLE_NAME}").fetchone()[0]
    stats['unique_states'] = conn.execute(f"SELECT COUNT(DISTINCT pub_state_name) FROM {TABLE_NAME} WHERE pub_state_name != ''").fetchone()[0]
    stats['unique_languages'] = conn.execute(f"SELECT COUNT(DISTINCT language) FROM {TABLE_NAME} WHERE language != ''").fetchone()[0]
    stats['unique_districts'] = conn.execute(f"SELECT COUNT(DISTINCT pub_dist_name) FROM {TABLE_NAME} WHERE pub_dist_name != ''").fetchone()[0]
    return stats


def main():
    st.title("🔍 PRGI Registration Data Search")
    st.markdown("Search and explore Press Registration General Information data")
    
    # Database connection
    db_path = st.sidebar.text_input("Database Path", value=DEFAULT_DB)
    conn = get_db_connection(db_path)
    
    if conn is None:
        st.warning("⚠️ Database not found. Please import data using:")
        st.code("python prgi_data_manager.py import --csv prgi_registration_title_details.csv --db prgi_data.db")
        return
    
    # Display statistics
    with st.sidebar:
        st.header("📊 Database Stats")
        try:
            stats = get_stats(conn)
            st.metric("Total Records", f"{stats['total_records']:,}")
            st.metric("States", stats['unique_states'])
            st.metric("Languages", stats['unique_languages'])
            st.metric("Districts", stats['unique_districts'])
        except Exception as e:
            st.error(f"Error loading stats: {e}")
    
    # Search filters
    st.header("🔎 Search Filters")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        title_search = st.text_input("📰 Title (contains)", placeholder="Enter title keywords...")
        owner_search = st.text_input("👤 Owner (contains)", placeholder="Enter owner name...")
    
    with col2:
        reg_number = st.text_input("📝 Registration Number", placeholder="Enter reg. number...")
        state = st.selectbox("🗺️ State", get_unique_values(conn, "pub_state_name"))
    
    with col3:
        district = st.selectbox("📍 District", get_unique_values(conn, "pub_dist_name"))
        language = st.selectbox("🗣️ Language", get_unique_values(conn, "language"))
    
    # Additional filters
    col4, col5 = st.columns(2)
    with col4:
        class_name = st.selectbox("📚 Class", get_unique_values(conn, "class_name"))
    with col5:
        result_limit = st.slider("Maximum Results", min_value=10, max_value=5000, value=500, step=10)
    
    # Search button
    search_button = st.button("🔍 Search", type="primary", use_container_width=True)
    
    # Build filters dict
    filters = {
        'title': title_search,
        'owner': owner_search,
        'registration_number': reg_number,
        'state': state,
        'district': district,
        'language': language,
        'class_name': class_name
    }
    
    # Auto-search or manual search
    if search_button or any(filters.values()):
        with st.spinner("Searching database..."):
            try:
                results_df = search_database(conn, filters, result_limit)
                
                # Display results
                st.header(f"📋 Results ({len(results_df)} records found)")
                
                if len(results_df) > 0:
                    # Add row numbers
                    results_df.insert(0, 'No.', range(1, len(results_df) + 1))
                    
                    # Display table with better formatting
                    st.dataframe(
                        results_df,
                        use_container_width=True,
                        height=600,
                        column_config={
                            "No.": st.column_config.NumberColumn("No.", width="small"),
                            "title_name": st.column_config.TextColumn("Title", width="large"),
                            "owner_name": st.column_config.TextColumn("Owner", width="medium"),
                            "registration_number": st.column_config.TextColumn("Registration #", width="medium"),
                            "pub_state_name": st.column_config.TextColumn("State", width="small"),
                            "pub_dist_name": st.column_config.TextColumn("District", width="medium"),
                            "language": st.column_config.TextColumn("Language", width="small"),
                            "class_name": st.column_config.TextColumn("Class", width="small"),
                        }
                    )
                    
                    # Export options
                    st.divider()
                    col_exp1, col_exp2 = st.columns(2)
                    
                    with col_exp1:
                        # CSV download
                        csv = results_df.to_csv(index=False)
                        st.download_button(
                            label="📥 Download CSV",
                            data=csv,
                            file_name="prgi_search_results.csv",
                            mime="text/csv",
                            use_container_width=True
                        )
                    
                    with col_exp2:
                        # JSON download
                        json_str = results_df.to_json(orient='records', indent=2)
                        st.download_button(
                            label="📥 Download JSON",
                            data=json_str,
                            file_name="prgi_search_results.json",
                            mime="application/json",
                            use_container_width=True
                        )
                else:
                    st.info("No records found matching your search criteria. Try adjusting your filters.")
                    
            except Exception as e:
                st.error(f"Error during search: {e}")
                st.exception(e)
    else:
        st.info("👆 Use the filters above to search the database")


if __name__ == "__main__":
    main()
