"""
NBA Player Props Stats Fetcher - BallDontLie API Version
FIXED: Proper API authentication
"""

import pandas as pd
from datetime import datetime, timedelta
import time
import os
import requests

class NBAStatsFetcherBallDontLie:
    def __init__(self, file_path, api_key):
        """Initialize with your CSV file path and BallDontLie API key"""
        self.file_path = file_path
        self.file_type = 'csv' if file_path.endswith('.csv') else 'excel'
        self.api_key = api_key
        self.base_url = "https://api.balldontlie.io/v1"
        
        # Team abbreviation mapping
        self.team_aliases = {
            'PHX': ['PHOENIX', 'SUNS'],
            'GSW': ['GOLDEN STATE', 'WARRIORS'],
            'LAL': ['LA LAKERS', 'LAKERS', 'LOS ANGELES LAKERS'],
            'LAC': ['LA CLIPPERS', 'CLIPPERS', 'LOS ANGELES CLIPPERS'],
            'NYK': ['NEW YORK', 'KNICKS'],
            'BKN': ['BROOKLYN', 'NETS'],
            'NOP': ['NEW ORLEANS', 'PELICANS'],
            'NO': ['NEW ORLEANS', 'PELICANS'],
            'SAS': ['SAN ANTONIO', 'SPURS'],
            'SA': ['SAN ANTONIO', 'SPURS'],
            'CHI': ['CHICAGO', 'BULLS'],
            'CHA': ['CHARLOTTE', 'HORNETS'],
            'DET': ['DETROIT', 'PISTONS'],
            'ORL': ['ORLANDO', 'MAGIC'],
            'MIA': ['MIAMI', 'HEAT'],
            'MEM': ['MEMPHIS', 'GRIZZLIES'],
            'POR': ['PORTLAND', 'TRAIL BLAZERS'],
            'TOR': ['TORONTO', 'RAPTORS'],
            'WAS': ['WASHINGTON', 'WIZARDS'],
            'HOU': ['HOUSTON', 'ROCKETS'],
            'ATL': ['ATLANTA', 'HAWKS'],
            'BOS': ['BOSTON', 'CELTICS'],
            'CLE': ['CLEVELAND', 'CAVALIERS'],
            'DAL': ['DALLAS', 'MAVERICKS'],
            'DEN': ['DENVER', 'NUGGETS'],
            'IND': ['INDIANA', 'PACERS'],
            'MIL': ['MILWAUKEE', 'BUCKS'],
            'MIN': ['MINNESOTA', 'TIMBERWOLVES'],
            'OKC': ['OKLAHOMA CITY', 'THUNDER'],
            'PHI': ['PHILADELPHIA', '76ERS'],
            'SAC': ['SACRAMENTO', 'KINGS'],
            'UTA': ['UTAH', 'JAZZ'],
        }
        
        # Test API connection
        self._test_api_connection()
    
    def _get_headers(self):
        """Get proper headers for API requests"""
        # BallDontLie may use different header formats
        # Try the most common ones
        return {"Authorization": f"{self.api_key}"}
    
    def _test_api_connection(self):
        """Test if API key is valid"""
        headers = self._get_headers()
        try:
            response = requests.get(
                f"{self.base_url}/players?per_page=1", 
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                print("✅ BallDontLie API connected successfully!")
                return True
            elif response.status_code == 401:
                print("❌ API KEY ERROR: Invalid or missing API key")
                print("   → Get your key at: https://www.balldontlie.io/")
                print("   → Update line: API_KEY = 'your_key_here'")
                return False
            elif response.status_code == 429:
                print("⚠️ Rate limit reached - wait a moment")
                return False
            else:
                print(f"⚠️ API Warning: Status code {response.status_code}")
                print(f"   Response: {response.text[:200]}")
                return False
                
        except requests.exceptions.Timeout:
            print("❌ API Timeout - check your connection")
            return False
        except Exception as e:
            print(f"❌ API Connection Error: {e}")
            return False
    
    def normalize_opponent(self, opponent):
        """Normalize opponent abbreviation"""
        if not opponent:
            return None
        opponent = str(opponent).upper().strip()
        # Handle common variations
        if opponent == 'NO':
            return 'NOP'
        if opponent == 'NY':
            return 'NYK'
        if opponent == 'SA':
            return 'SAS'
        return opponent
    
    def find_player_id(self, player_name):
        """Find player ID by name using BallDontLie API"""
        headers = self._get_headers()
        
        # Try different name formats
        search_names = [
            player_name,
            player_name.replace('.', '').replace('  ', ' '),
            player_name.replace('C.J.', 'CJ'),
            player_name.replace('J.J.', 'JJ'),
        ]
        
        # Also try just last name if full name fails
        name_parts = player_name.split()
        if len(name_parts) >= 2:
            search_names.append(name_parts[-1])  # Last name only
        
        for search_name in search_names:
            try:
                # Search for player
                params = {"search": search_name, "per_page": 25}
                response = requests.get(
                    f"{self.base_url}/players",
                    headers=headers,
                    params=params,
                    timeout=10
                )
                
                if response.status_code == 401:
                    print(f"  ❌ API key invalid")
                    return None, None
                
                if response.status_code == 200:
                    data = response.json()
                    players = data.get('data', [])
                    
                    if players:
                        # Try to find best match
                        for player in players:
                            full_name = f"{player['first_name']} {player['last_name']}"
                            
                            # Exact match
                            if full_name.lower() == player_name.lower():
                                return player['id'], full_name
                            
                            # Close match (for names like "C.J." vs "CJ")
                            if player_name.replace('.', '').replace(' ', '').lower() == \
                               full_name.replace('.', '').replace(' ', '').lower():
                                print(f"  ℹ️ Found as: {full_name}")
                                return player['id'], full_name
                        
                        # If no exact match, use first result if searching last name
                        if search_name == name_parts[-1] and len(players) > 0:
                            player = players[0]
                            full_name = f"{player['first_name']} {player['last_name']}"
                            print(f"  ℹ️ Found as: {full_name}")
                            return player['id'], full_name
                
                time.sleep(0.03)  # Minimal rate limiting
                
            except Exception as e:
                continue
        
        return None, None
    
    def match_opponent(self, home_team, visitor_team, target_opponent):
        """Check if target opponent matches either team"""
        if not target_opponent:
            return False, None, None
        
        target = self.normalize_opponent(target_opponent)
        home_abbr = home_team.get('abbreviation', '').upper()
        visitor_abbr = visitor_team.get('abbreviation', '').upper()
        
        # Direct match
        if target == home_abbr:
            return True, home_team, 'vs'
        if target == visitor_abbr:
            return True, visitor_team, '@'
        
        # Check aliases
        home_name = home_team.get('full_name', '').upper()
        visitor_name = visitor_team.get('full_name', '').upper()
        
        if target in self.team_aliases:
            for alias in self.team_aliases[target]:
                if alias in home_name:
                    return True, home_team, 'vs'
                if alias in visitor_name:
                    return True, visitor_team, '@'
        
        return False, None, None
    
    def fetch_player_game_stats(self, player_name, opponent=None, max_date=None, days_window=7):
        """
        Fetch player stats using BallDontLie API
        """
        headers = self._get_headers()
        
        # Find player
        player_id, full_name = self.find_player_id(player_name)
        if not player_id:
            print(f"  ❌ Player not found in API")
            return None
        
        # Set date range
        if max_date is None:
            max_date = datetime.now()
        
        # Search window
        start_date = (max_date - timedelta(days=days_window)).strftime('%Y-%m-%d')
        end_date = (max_date - timedelta(days=1)).strftime('%Y-%m-%d')
        
        try:
            # Get player stats for date range
            params = {
                "player_ids[]": player_id,
                "start_date": start_date,
                "end_date": end_date,
                "per_page": 100
            }
            
            response = requests.get(
                f"{self.base_url}/stats",
                headers=headers,
                params=params,
                timeout=10
            )
            
            if response.status_code == 401:
                print(f"  ❌ API key invalid")
                return None
            
            if response.status_code != 200:
                print(f"  ❌ API Error: {response.status_code}")
                return None
            
            data = response.json()
            games = data.get('data', [])
            
            if not games:
                print(f"  ⚠️ No games in {days_window}-day window")
                return None
            
            print(f"  📅 {len(games)} game(s) found")
            
            # Get unique game IDs and fetch details efficiently
            game_ids = list(set([g.get('game', {}).get('id') for g in games if g.get('game', {}).get('id')]))
            
            game_details = {}
            for game_id in game_ids:
                try:
                    game_response = requests.get(
                        f"{self.base_url}/games/{game_id}",
                        headers=headers,
                        timeout=10
                    )
                    if game_response.status_code == 200:
                        game_details[game_id] = game_response.json().get('data', {})
                    time.sleep(0.03)  # Minimal delay
                except:
                    pass
            
            # If opponent specified, find matching game
            if opponent and opponent != '':
                opponent = self.normalize_opponent(opponent)
                print(f"  🔍 Target: {opponent}")
                
                # Debug: show all games in the window
                print(f"  📋 Available games:")
                for i, game_stat in enumerate(games):
                    game_id = game_stat.get('game', {}).get('id')
                    game_date = game_stat.get('game', {}).get('date', '').split('T')[0]
                    player_team = game_stat.get('team', {})
                    player_abbr = player_team.get('abbreviation', '?')
                    
                    # Get full game details
                    if game_id in game_details:
                        full_game = game_details[game_id]
                        home_team = full_game.get('home_team', {})
                        visitor_team = full_game.get('visitor_team', {})
                        home_abbr = home_team.get('abbreviation', '?')
                        visitor_abbr = visitor_team.get('abbreviation', '?')
                        
                        if player_abbr == home_abbr:
                            game_str = f"{player_abbr} vs {visitor_abbr}"
                        else:
                            game_str = f"{player_abbr} @ {home_abbr}"
                        
                        print(f"     [{i+1}] {game_date}: {game_str}")
                    else:
                        print(f"     [{i+1}] {game_date}: {player_abbr} (game details unavailable)")
                
                # Now match opponent
                for game_stat in games:
                    game_id = game_stat.get('game', {}).get('id')
                    
                    if game_id in game_details:
                        full_game = game_details[game_id]
                        home_team = full_game.get('home_team', {})
                        visitor_team = full_game.get('visitor_team', {})
                        player_team = game_stat.get('team', {})
                        
                        is_match, opp_team, location = self.match_opponent(home_team, visitor_team, opponent)
                        
                        if is_match:
                            game_date = full_game.get('date', '').split('T')[0]
                            player_abbr = player_team.get('abbreviation', 'TEAM')
                            opp_abbr = opp_team.get('abbreviation', 'OPP')
                            matchup = f"{player_abbr} {location} {opp_abbr}"
                            
                            print(f"  ✅ {matchup} ({game_date})")
                            
                            return {
                                'PTS': game_stat.get('pts', 0) or 0,
                                'REB': game_stat.get('reb', 0) or 0,
                                'AST': game_stat.get('ast', 0) or 0,
                                'FG3M': game_stat.get('fg3m', 0) or 0,
                                'game_date': game_date,
                                'matchup': matchup,
                                'match_method': 'BallDontLie API',
                                'days_old': (max_date.date() - datetime.strptime(game_date, '%Y-%m-%d').date()).days
                            }
                
                print(f"  ❌ No game vs {opponent}")
                return None
            
            # No opponent - use most recent game
            else:
                # Sort by date to get most recent
                games_sorted = sorted(games, key=lambda x: x.get('game', {}).get('date', ''), reverse=True)
                most_recent = games_sorted[0]
                
                game_id = most_recent.get('game', {}).get('id')
                game_date = most_recent.get('game', {}).get('date', '').split('T')[0]
                player_team = most_recent.get('team', {})
                player_abbr = player_team.get('abbreviation', 'TEAM')
                
                # Try to get full game details
                if game_id in game_details:
                    full_game = game_details[game_id]
                    home_team = full_game.get('home_team', {})
                    visitor_team = full_game.get('visitor_team', {})
                    home_abbr = home_team.get('abbreviation', 'HOME')
                    visitor_abbr = visitor_team.get('abbreviation', 'AWAY')
                    
                    if player_abbr == home_abbr:
                        matchup = f"{player_abbr} vs {visitor_abbr}"
                    else:
                        matchup = f"{player_abbr} @ {home_abbr}"
                else:
                    matchup = f"{player_abbr} (opponent unknown)"
                
                print(f"  ⚠️ No opponent - recent: {matchup}")
                
                return {
                    'PTS': most_recent.get('pts', 0) or 0,
                    'REB': most_recent.get('reb', 0) or 0,
                    'AST': most_recent.get('ast', 0) or 0,
                    'FG3M': most_recent.get('fg3m', 0) or 0,
                    'game_date': game_date,
                    'matchup': matchup,
                    'match_method': 'Most recent',
                    'days_old': (max_date.date() - datetime.strptime(game_date, '%Y-%m-%d').date()).days
                }
                
        except Exception as e:
            print(f"  ❌ Error: {str(e)}")
            return None
    
    def update_excel_with_results(self, max_date=None, days_window=7):
        """
        Process CSV and fetch stats
        """
        # Read file
        if self.file_type == 'csv':
            df = pd.read_csv(self.file_path)
            print(f"📁 CSV: {self.file_path}")
        else:
            df = pd.read_excel(self.file_path)
            print(f"📁 Excel: {self.file_path}")
        
        print(f"🎯 Cutoff: {max_date.strftime('%B %d, %Y') if max_date else 'Today'}")
        print(f"🔍 Window: {days_window} days\n")
        
        # Find opponent column
        opponent_col = None
        for col in df.columns:
            if col.lower() == 'opponent':
                opponent_col = col
                break
        
        if opponent_col:
            filled = df[opponent_col].notna() & (df[opponent_col] != '')
            print(f"✅ Opponent column: '{opponent_col}' ({filled.sum()}/{len(df)} filled)\n")
        
        # Add result columns
        new_columns = ['Actual_Stat', 'Hit_Miss', 'Result', 'Game_Date', 'Matchup', 'Match_Method', 'Days_Old']
        for col in new_columns:
            if col not in df.columns:
                df[col] = ''
        
        print(f"Processing {len(df)} players...")
        print("-" * 70)
        
        # Process each row
        for idx, row in df.iterrows():
            player_name = row['Player']
            stat_type = row['Stat']
            line = row['Line']
            
            opponent = None
            if opponent_col:
                opp_value = row[opponent_col]
                if pd.notna(opp_value) and str(opp_value).strip() != '':
                    opponent = str(opp_value).strip()
            
            print(f"\n{idx+1}. {player_name} - {stat_type} {line}")
            if opponent:
                print(f"   🎯 vs {opponent}", end=" ")
            
            stats = self.fetch_player_game_stats(
                player_name,
                opponent=opponent,
                max_date=max_date,
                days_window=days_window
            )
            
            if stats:
                actual_value = stats.get(stat_type, None)
                
                if actual_value is not None:
                    df.at[idx, 'Actual_Stat'] = actual_value
                    df.at[idx, 'Game_Date'] = stats.get('game_date', '')
                    df.at[idx, 'Matchup'] = stats.get('matchup', '')
                    df.at[idx, 'Match_Method'] = stats.get('match_method', '')
                    df.at[idx, 'Days_Old'] = stats.get('days_old', '')
                    
                    if actual_value > line:
                        df.at[idx, 'Hit_Miss'] = 'HIT'
                        df.at[idx, 'Result'] = '✓'
                        result = '✅'
                    else:
                        df.at[idx, 'Hit_Miss'] = 'MISS'
                        df.at[idx, 'Result'] = '✗'
                        result = '❌'
                    
                    print(f"  📊 {stat_type}: {actual_value} vs {line} {result}")
                else:
                    df.at[idx, 'Hit_Miss'] = 'ERROR'
                    print(f"  ⚠️ Stat '{stat_type}' not available")
            else:
                df.at[idx, 'Actual_Stat'] = 'N/A'
                df.at[idx, 'Hit_Miss'] = 'PENDING'
                df.at[idx, 'Result'] = '⏳'
            
            time.sleep(0.1)  # Faster rate limiting
        
        # Save
        base_name = os.path.splitext(self.file_path)[0]
        if self.file_type == 'csv':
            output_file = f"{base_name}_updated.csv"
            df.to_csv(output_file, index=False)
        else:
            output_file = f"{base_name}_updated.xlsx"
            df.to_excel(output_file, index=False)
        
        print("\n" + "=" * 70)
        print(f"✅ Saved: {output_file}\n")
        
        hits = (df['Hit_Miss'] == 'HIT').sum()
        misses = (df['Hit_Miss'] == 'MISS').sum()
        pending = (df['Hit_Miss'] == 'PENDING').sum()
        
        print(f"📊 RESULTS:")
        print(f"   ✅ Hits: {hits}")
        print(f"   ❌ Misses: {misses}")
        print(f"   ⏳ Pending: {pending}")
        
        if hits + misses > 0:
            hit_rate = hits / (hits + misses) * 100
            print(f"\n🎯 HIT RATE: {hits}/{hits + misses} = {hit_rate:.1f}%")
        
        return df


def main():
    """Main execution"""
    # ⬇️ SETTINGS ⬇️
    API_KEY = "642d8995-44d0-4c58-b051-d32e72cf6036"  # Your BallDontLie API key
    file_path = "export_prizepicks_with_opponent.csv"
    
    # For Nov 10, 2025 games, use cutoff of Nov 11, 2025
    cutoff_date = datetime(2025, 11, 11)
    days_window = 2  # Look back 2 days
    
    print("=" * 70)
    print("NBA PLAYER PROPS - BallDontLie API (REAL-TIME)")
    print("=" * 70)
    print()
    
    fetcher = NBAStatsFetcherBallDontLie(file_path, API_KEY)
    
    try:
        results_df = fetcher.update_excel_with_results(
            max_date=cutoff_date,
            days_window=days_window
        )
        
        if results_df is not None:
            print("\n✨ Complete!")
        
    except FileNotFoundError:
        print(f"❌ File not found: {file_path}")
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()