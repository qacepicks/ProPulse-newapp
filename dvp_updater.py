#!/usr/bin/env python3
# dvp_updater.py — PropPulse+ v2025 (HashtagBasketball Edition - HTML Scraper)
#
# Scrapes DvP from:
# https://hashtagbasketball.com/nba-defense-vs-position
#
# Output format:
#   dvp[TEAM_ABBR][POS][STAT] = rank
#
# Supported stats:
#   PTS, REB, AST, FG3M

import os
import json
import time
import requests
import pandas as pd
from bs4 import BeautifulSoup
from io import StringIO

CACHE_FILE = "data/dvp_cache.json"
CACHE_HOURS = 12

HASHTAG_URL = "https://hashtagbasketball.com/nba-defense-vs-position"


# ------------------------------------------------------
# Team Mapping (abbreviations used on HashtagBasketball)
# ------------------------------------------------------
TEAM_MAP = {
    "ATL": "ATL", "BOS": "BOS", "BKN": "BKN", "CHA": "CHA", "CHI": "CHI",
    "CLE": "CLE", "DAL": "DAL", "DEN": "DEN", "DET": "DET", "GSW": "GS",
    "GS": "GSW", "HOU": "HOU", "IND": "IND", "LAC": "LAC", "LAL": "LAL",
    "MEM": "MEM", "MIA": "MIA", "MIL": "MIL", "MIN": "MIN", "NOP": "NO",
    "NO": "NOP", "NYK": "NY", "NY": "NYK", "OKC": "OKC", "ORL": "ORL",
    "PHI": "PHI", "PHX": "PHX", "POR": "POR", "SAC": "SAC", "SAS": "SA",
    "SA": "SAS", "TOR": "TOR", "UTA": "UTA", "WAS": "WAS"
}


# ------------------------------------------------------
# Scrape HashtagBasketball HTML
# ------------------------------------------------------
def _fetch_dvp_from_hashtag():
    """
    Scrapes the HashtagBasketball DvP page.
    The full table (Table 4) has 150 rows: 30 teams × 5 positions
    Each row shows: Position, Team, PTS rank, FG%, FT%, 3PM rank, REB rank, AST rank, STL, BLK, TO
    """
    print("[DVP] 🔄 Fetching DvP from HashtagBasketball HTML...")

    # Initialize nested dict structure
    all_teams = set(TEAM_MAP.values())
    dvp = {abbr: {pos: {} for pos in ["PG", "SG", "SF", "PF", "C"]}
           for abbr in all_teams}

    # Map of our stat names to column names in the table
    stat_columns = {
        "PTS": "Sort: PTS",
        "REB": "Sort: REB", 
        "AST": "Sort: AST",
        "FG3M": "Sort: 3PM"
    }

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }

    try:
        # Fetch the page (we can get all stats from one page)
        print(f"[DVP]   Fetching from {HASHTAG_URL}")
        response = requests.get(HASHTAG_URL, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find all tables
        tables = soup.find_all('table')
        print(f"[DVP]   Found {len(tables)} tables")
        
        # We want the largest table (should be 150 rows for all team-position combos)
        target_table = None
        max_rows = 0
        
        for table in tables:
            try:
                df = pd.read_html(StringIO(str(table)))[0]
                if len(df) > max_rows:
                    max_rows = len(df)
                    target_table = df
            except:
                continue
        
        if target_table is None:
            print("[DVP] ❌ Could not find data table")
            return dvp
        
        df = target_table
        print(f"[DVP]   Processing table with {len(df)} rows")
        
        # Clean column names
        df.columns = df.columns.astype(str)
        
        # The table has columns: Position, Team, PTS, FG%, FT%, 3PM, REB, AST, STL, BLK, TO
        pos_col = "Sort: Position"
        team_col = "Sort: Team"
        
        if pos_col not in df.columns or team_col not in df.columns:
            print(f"[DVP] ❌ Missing required columns. Found: {list(df.columns)}")
            return dvp
        
        # Process each row
        for idx, row in df.iterrows():
            try:
                position = str(row[pos_col]).strip().upper()
                team_raw = str(row[team_col]).strip().upper()
                
                # Extract team abbreviation (might have numbers after it)
                # e.g., "NY 3" -> "NY"
                team_abbr = ''.join(c for c in team_raw.split()[0] if c.isalpha())
                
                # Map to standard abbreviation
                team_abbr = TEAM_MAP.get(team_abbr, team_abbr)
                
                # Validate position
                if position not in ["PG", "SG", "SF", "PF", "C"]:
                    continue
                
                if team_abbr not in dvp:
                    continue
                
                # Extract rank values for each stat
                for stat_key, col_name in stat_columns.items():
                    if col_name in df.columns:
                        try:
                            # The value might be like "15.6 1" where the number after space is the rank
                            # Or it might just be a rank number
                            value_str = str(row[col_name]).strip()
                            
                            # Try to extract rank (typically the last number, or first if it's just rank)
                            parts = value_str.split()
                            
                            # If there are multiple numbers, the last one is usually the rank
                            # If just one number, it could be either value or rank
                            if len(parts) >= 2:
                                # Format like "15.6 1" - last number is rank
                                rank = float(parts[-1])
                            else:
                                # Single number - try to parse it
                                rank = float(parts[0])
                            
                            dvp[team_abbr][position][stat_key] = rank
                            
                        except (ValueError, IndexError):
                            pass
            
            except Exception as e:
                continue
        
        # Count successful extractions
        total_entries = sum(
            len(dvp[team][pos]) 
            for team in dvp 
            for pos in dvp[team]
        )
        
        if total_entries > 0:
            print(f"[DVP] ✅ Successfully loaded {total_entries} DvP rank entries")
        else:
            print("[DVP] ⚠️ No data was extracted from table")
        
    except Exception as e:
        print(f"[DVP] ❌ Error fetching data: {e}")
    
    return dvp


# ------------------------------------------------------
# Cache Handling
# ------------------------------------------------------
def _load_cache():
    if not os.path.exists(CACHE_FILE):
        return None

    try:
        age = (time.time() - os.path.getmtime(CACHE_FILE)) / 3600
        if age < CACHE_HOURS:
            with open(CACHE_FILE, "r") as f:
                print(f"[DVP] 🟢 Using cached DvP ({age:.1f}h old)")
                return json.load(f)["dvp"]
    except Exception as e:
        print(f"[DVP] ⚠️ Cache load error: {e}")
        pass

    return None


def _save_cache(dvp):
    os.makedirs("data", exist_ok=True)
    with open(CACHE_FILE, "w") as f:
        json.dump({"timestamp": time.time(), "dvp": dvp}, f, indent=2)
    print("[DVP] 💾 Saved DvP cache.")


# ------------------------------------------------------
# Public Loader
# ------------------------------------------------------
def load_dvp_data(force_refresh=False):
    """
    Load Defense vs Position data.
    Returns dict: dvp[TEAM_ABBR][POS][STAT] = rank
    """
    if not force_refresh:
        cached = _load_cache()
        if cached:
            return cached

    dvp = _fetch_dvp_from_hashtag()
    
    # Check if we got data
    total_entries = sum(
        len(dvp[team][pos]) 
        for team in dvp 
        for pos in dvp[team]
    )
    
    if total_entries > 0:
        _save_cache(dvp)
        return dvp
    
    print("[DVP] ⚠️ No DvP available. Returning empty.")
    return {}


# ------------------------------------------------------
# Test function
# ------------------------------------------------------
if __name__ == "__main__":
    print("Testing DvP scraper...")
    dvp_data = load_dvp_data(force_refresh=True)
    
    if dvp_data:
        # Count total entries
        total = sum(
            len(dvp_data[team][pos]) 
            for team in dvp_data 
            for pos in dvp_data[team]
        )
        print(f"\n[DVP] Total entries: {total}")
        
        # Print sample data for a few teams
        print("\n[DVP] Sample data:")
        for sample_team in ["NYK", "GSW", "LAL"][:3]:
            if sample_team in dvp_data:
                print(f"\n{sample_team}:")
                for pos in ["PG", "SG", "SF", "PF", "C"]:
                    if dvp_data[sample_team][pos]:
                        print(f"  {pos}: {dvp_data[sample_team][pos]}")
                break
    else:
        print("\n[DVP] ❌ No data retrieved")