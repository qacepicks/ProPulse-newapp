# ===============================
# 📊 DvP Auto Updater (Hashtag Basketball) - FIXED
# ===============================
import os, time, json, requests
import pandas as pd
from io import StringIO
from datetime import datetime

DATA_PATH = "data/"
DVP_FILE = os.path.join(DATA_PATH, "dvp_data.json")
REFRESH_HOURS = 12
URL = "https://hashtagbasketball.com/nba-defense-vs-position"

POSITIONS = ["PG", "SG", "SF", "PF", "C"]
STATS = ["PTS", "REB", "AST", "FG3M", "3PM"]  # Added 3PM as alias

# -------------------------------
# TEAM NAME → ABBR
# -------------------------------
def simplify_team_abbr(team_name):
    lookup = {
        "Atlanta": "ATL", "Boston": "BOS", "Brooklyn": "BKN", "Charlotte": "CHA",
        "Chicago": "CHI", "Cleveland": "CLE", "Dallas": "DAL", "Denver": "DEN",
        "Detroit": "DET", "Golden State": "GSW", "Houston": "HOU", "Indiana": "IND",
        "LA Clippers": "LAC", "LA Lakers": "LAL", "Lakers": "LAL", "Clippers": "LAC",
        "Memphis": "MEM", "Miami": "MIA", "Milwaukee": "MIL", "Minnesota": "MIN", 
        "New Orleans": "NOP", "New York": "NYK", "Oklahoma City": "OKC", "Orlando": "ORL",
        "Philadelphia": "PHI", "Phoenix": "PHX", "Portland": "POR", "Sacramento": "SAC",
        "San Antonio": "SAS", "Toronto": "TOR", "Utah": "UTA", "Washington": "WAS"
    }
    for k, v in lookup.items():
        if k.lower() in team_name.lower():
            return v
    return team_name[:3].upper()

# -------------------------------
# SCRAPER - FIXED
# -------------------------------
def fetch_hashtag_table():
    """Pull the master Defense vs Position table from Hashtag Basketball."""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/125.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9"
        }
        
        print(f"[DvP] Fetching {URL}...")
        r = requests.get(URL, headers=headers, timeout=15)
        
        if r.status_code != 200:
            print(f"[DvP] ❌ HTTP {r.status_code}")
            return None
        
        # Parse all tables
        tables = pd.read_html(StringIO(r.text))
        print(f"[DvP] Found {len(tables)} tables on page")
        
        if not tables:
            print(f"[DvP] ❌ No tables found")
            return None
        
        # ✅ FIX: The DvP data is in the LARGEST table (table 3, ~150 rows)
        # Find the table with the most rows (should be ~150 = 30 teams × 5 positions)
        df = max(tables, key=lambda t: len(t))
        
        print(f"[DvP] Selected table with {len(df)} rows × {len(df.columns)} columns")
        
        if len(df) < 30:
            print(f"[DvP] ⚠️ Table seems too small ({len(df)} rows), expected ~150")
            return None
        
        return df
        
    except Exception as e:
        print(f"[DvP] ❌ Error fetching Hashtag Basketball table: {e}")
        import traceback
        traceback.print_exc()
        return None

# -------------------------------
# PARSER - IMPROVED
# -------------------------------
def process_hashtag_table(df):
    """Convert the big Hashtag Basketball table into our nested dict."""
    dvp = {}
    
    # Clean column names - remove "Sort: " prefix
    df.columns = [str(c).replace("Sort: ", "").strip() for c in df.columns]
    
    print(f"[DvP] Processing columns: {list(df.columns)[:10]}")
    
    for _, row in df.iterrows():
        # Get team name
        team_name = None
        for col in ["Team", "TEAM", "team"]:
            if col in df.columns:
                team_name = str(row.get(col, "")).strip()
                break
        
        if not team_name or team_name == "":
            continue
        
        abbr = simplify_team_abbr(team_name)
        
        # Get position
        position = None
        for col in ["Position", "POSITION", "position", "Pos", "POS"]:
            if col in df.columns:
                position = str(row.get(col, "")).strip().upper()
                break
        
        if not position or position not in POSITIONS:
            continue
        
        # Initialize team if needed
        if abbr not in dvp:
            dvp[abbr] = {}
        
        # Initialize position if needed
        if position not in dvp[abbr]:
            dvp[abbr][position] = {}
        
        # Extract stats - be more flexible with column matching
        for stat in ["PTS", "REB", "AST", "FG3M", "3PM"]:
            # Try exact match first, then partial match
            stat_col = None
            
            # Exact match
            if stat in df.columns:
                stat_col = stat
            # Partial match (case insensitive)
            else:
                for col in df.columns:
                    col_upper = str(col).upper()
                    if stat == "FG3M" and "3PM" in col_upper:
                        stat_col = col
                        break
                    elif stat in col_upper:
                        stat_col = col
                        break
            
            if stat_col:
                val = row.get(stat_col)
                
                # ✅ FIX: Values might be strings like "21.8 54" (stat + rank)
                # Extract just the first number
                if isinstance(val, str):
                    val = val.strip().split()[0]  # Take first part before space
                
                # Debug first few
                if abbr in list(dvp.keys())[:2] and position in ["PG", "SF"][:1]:
                    print(f"[DvP Debug] {abbr} {position} {stat}: col={stat_col}, val={val}")
                
                val_numeric = pd.to_numeric(val, errors="coerce")
                if pd.notna(val_numeric):
                    # Normalize stat name
                    normalized_stat = "FG3M" if stat in ["FG3M", "3PM"] else stat
                    dvp[abbr][position][normalized_stat] = float(val_numeric)
            else:
                # Debug missing columns
                if abbr == list(dvp.keys())[0] and position == "PG":
                    print(f"[DvP Debug] Could not find column for stat '{stat}' in columns: {df.columns.tolist()}")
    
    print(f"[DvP] Parsed {len(dvp)} teams")
    
    if not dvp:
        print("[DvP] ❌ No data parsed!")
        return {}
    
    # Convert values to ranks (1-30, lower allowed = tougher defense = rank 1)
    for pos in POSITIONS:
        for stat in ["PTS", "REB", "AST", "FG3M"]:
            # Collect all values for this position-stat combo
            vals = {}
            for team in dvp:
                if pos in dvp[team] and stat in dvp[team][pos]:
                    vals[team] = dvp[team][pos][stat]
            
            if not vals:
                continue
            
            # Sort by value (ascending = better defense)
            sorted_teams = sorted(vals.items(), key=lambda x: x[1])
            
            # Assign ranks 1-30
            for rank, (team, _) in enumerate(sorted_teams, start=1):
                dvp[team][pos][stat] = rank
    
    print(f"[DvP] ✅ Converted to ranks (1-30)")
    
    # Verify we got data
    sample_team = list(dvp.keys())[0] if dvp else None
    if sample_team:
        print(f"[DvP] Sample - {sample_team}: {dvp[sample_team]}")
    
    return dvp

# -------------------------------
# MAIN LOADER
# -------------------------------
def load_dvp_data():
    os.makedirs(DATA_PATH, exist_ok=True)
    need_refresh = True

    if os.path.exists(DVP_FILE):
        age_hours = (time.time() - os.path.getmtime(DVP_FILE)) / 3600
        
        # Also check if file is valid (not empty)
        try:
            with open(DVP_FILE, "r") as f:
                data = json.load(f)
                if data and len(data) > 0:  # Has content
                    if age_hours < REFRESH_HOURS:
                        print(f"[DvP] Using cached data (updated {age_hours:.1f}h ago)")
                        return data
                else:
                    print(f"[DvP] ⚠️ Cache is empty, forcing refresh")
        except:
            print(f"[DvP] ⚠️ Cache corrupted, forcing refresh")

    if need_refresh:
        print("[DvP] ⏳ Refreshing DvP data from Hashtag Basketball...")
        df = fetch_hashtag_table()
        
        if df is not None and not df.empty:
            dvp_dict = process_hashtag_table(df)
            
            if dvp_dict and len(dvp_dict) > 0:
                with open(DVP_FILE, "w") as f:
                    json.dump(dvp_dict, f, indent=2)
                print(f"[DvP] ✅ Data refreshed: {len(dvp_dict)} teams saved ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})")
                return dvp_dict
            else:
                print("[DvP] ❌ Processed data is empty!")
        else:
            print("[DvP] ❌ Failed to fetch Hashtag Basketball data.")
        
        # Fallback to old cache if available
        if os.path.exists(DVP_FILE):
            print("[DvP] ⚠️ Using last cached data.")
            with open(DVP_FILE, "r") as f:
                return json.load(f)
        
        print("[DvP] 🚫 No valid data available; using neutral multipliers.")
        return {}
    
    with open(DVP_FILE, "r") as f:
        return json.load(f)

# -------------------------------
# TEST MODE
# -------------------------------
if __name__ == "__main__":
    data = load_dvp_data()
    print(f"\n[DvP] Final result: Loaded {len(data)} teams.")
    
    if data:
        print(f"[DvP] Sample teams: {list(data.keys())[:5]}")
        
        # Test ATL
        if "ATL" in data:
            print(f"\n[DvP] ATL data:")
            print(f"  Positions: {list(data['ATL'].keys())}")
            if "SF" in data["ATL"]:
                print(f"  SF stats: {data['ATL']['SF']}")