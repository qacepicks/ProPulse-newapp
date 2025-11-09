#!/usr/bin/env python3
# display_results.py — Enhanced display system for PropPulse+

import pandas as pd
from datetime import datetime
import os

# ==========================================
# DISPLAY UTILITIES
# ==========================================

def get_ev_tier(ev_pct):
    """Categorize EV into tiers"""
    if ev_pct >= 20:
        return "🔥🔥🔥", "ELITE"
    elif ev_pct >= 15:
        return "🔥🔥🔥", "ELITE"
    elif ev_pct >= 10:
        return "🔥🔥", "STRONG"
    elif ev_pct >= 5:
        return "🔥", "GOOD"
    elif ev_pct > 0:
        return "✅", "SLIGHT"
    else:
        return "⚠️", "NEGATIVE"


def get_confidence_level(model_prob, projection, line, n_games):
    """Calculate confidence score based on multiple factors"""
    score = 0
    
    # Probability edge
    if model_prob >= 0.60:
        score += 3
    elif model_prob >= 0.55:
        score += 2
    elif model_prob >= 0.52:
        score += 1
    
    # Projection vs line gap
    gap_pct = abs(projection - line) / line if line != 0 else 0
    if gap_pct >= 0.15:
        score += 2
    elif gap_pct >= 0.10:
        score += 1
    
    # Sample size
    if n_games >= 30:
        score += 2
    elif n_games >= 20:
        score += 1
    
    if score >= 6:
        return "🟢", "HIGH"
    elif score >= 4:
        return "🟡", "MEDIUM"
    elif score >= 2:
        return "🟠", "LOW"
    else:
        return "🔴", "VERY LOW"


# ==========================================
# SORTING & FILTERING
# ==========================================

def sort_results(results, sort_by="ev"):
    """
    Sort results by different metrics
    Options: 'ev', 'prob', 'projection', 'edge', 'odds', 'confidence'
    """
    if sort_by == "prob":
        return sorted(results, key=lambda x: x['p_model'], reverse=True)
    elif sort_by == "projection":
        return sorted(results, key=lambda x: x['projection'], reverse=True)
    elif sort_by == "edge":
        return sorted(results, key=lambda x: abs(x['p_model'] - x['p_book']), reverse=True)
    elif sort_by == "odds":
        return sorted(results, key=lambda x: x['odds'], reverse=True)
    elif sort_by == "confidence":
        return sorted(results, key=lambda x: get_confidence_level(
            x['p_model'], x['projection'], x['line'], x['n_games']
        )[1], reverse=True)
    else:  # default to EV
        return sorted(results, key=lambda x: x['ev'], reverse=True)


def filter_results(results, min_ev=None, min_prob=None, max_prob=None, 
                   stats=None, min_games=None, positions=None, player_search=None):
    """Filter results based on criteria"""
    filtered = results.copy()
    
    if min_ev is not None:
        filtered = [r for r in filtered if r['ev'] * 100 >= min_ev]
    
    if min_prob is not None:
        filtered = [r for r in filtered if r['p_model'] * 100 >= min_prob]
    
    if max_prob is not None:
        filtered = [r for r in filtered if r['p_model'] * 100 <= max_prob]
    
    if stats:
        stats_list = [s.strip().upper() for s in stats.split(',')]
        filtered = [r for r in filtered if r['stat'] in stats_list]
    
    if min_games is not None:
        filtered = [r for r in filtered if r['n_games'] >= min_games]
    
    if positions:
        pos_list = [p.strip().upper() for p in positions.split(',')]
        filtered = [r for r in filtered if r['position'] in pos_list]
    
    if player_search:
        search_lower = player_search.lower()
        filtered = [r for r in filtered if search_lower in r['player'].lower()]
    
    return filtered


# ==========================================
# PAGINATION HELPER
# ==========================================

def paginate_results(results, page_size=25):
    """Generator that yields pages of results"""
    for i in range(0, len(results), page_size):
        yield results[i:i + page_size], i // page_size + 1, (len(results) + page_size - 1) // page_size


# ==========================================
# COMPACT TABLE VIEW (WITH PAGINATION)
# ==========================================

def display_compact_table(results, top_n=50, title="TOP PROPS", paginate=False, page_size=25):
    """Clean, scannable table format with optional pagination"""
    
    if not results:
        print("\n⚠️ No results to display")
        return
    
    display_results = results[:top_n] if not paginate else results
    
    if paginate and len(display_results) > page_size:
        # Paginated display
        page_num = 1
        total_pages = (len(display_results) + page_size - 1) // page_size
        
        while True:
            start_idx = (page_num - 1) * page_size
            end_idx = min(start_idx + page_size, len(display_results))
            page_results = display_results[start_idx:end_idx]
            
            print("\n" + "="*100)
            print(f"📊 {title} - Page {page_num}/{total_pages} (Showing {start_idx+1}-{end_idx} of {len(display_results)})")
            print("="*100)
            
            # Header
            print(f"{'#':<4} {'Player':<20} {'Stat':<8} {'Line':<6} {'Proj':<6} "
                  f"{'Model%':<8} {'Book%':<8} {'EV%':<8} {'Odds':<7} {'Conf':<10}")
            print("-"*100)
            
            for i, r in enumerate(page_results, start_idx + 1):
                ev_pct = r['ev'] * 100
                model_pct = r['p_model'] * 100
                book_pct = r['p_book'] * 100
                
                emoji, tier = get_ev_tier(ev_pct)
                conf_emoji, conf_level = get_confidence_level(
                    r['p_model'], r['projection'], r['line'], r['n_games']
                )
                
                odds_str = f"+{r['odds']}" if r['odds'] >= 0 else str(r['odds'])
                
                print(f"{i:<4} {r['player'][:19]:<20} {r['stat']:<8} {r['line']:<6.1f} "
                      f"{r['projection']:<6.1f} {model_pct:<7.1f}% {book_pct:<7.1f}% "
                      f"{emoji} {ev_pct:<5.1f}% {odds_str:<7} {conf_emoji} {conf_level}")
            
            print("="*100)
            
            # Navigation
            if total_pages > 1:
                nav_options = []
                if page_num > 1:
                    nav_options.append("[p] Previous")
                if page_num < total_pages:
                    nav_options.append("[n] Next")
                nav_options.append("[q] Back to menu")
                
                print(f"\nNavigation: {' | '.join(nav_options)}")
                nav = input("Select: ").strip().lower()
                
                if nav == 'n' and page_num < total_pages:
                    page_num += 1
                elif nav == 'p' and page_num > 1:
                    page_num -= 1
                elif nav == 'q':
                    break
                else:
                    print("❌ Invalid option")
            else:
                input("\nPress Enter to continue...")
                break
    else:
        # Non-paginated display
        print("\n" + "="*100)
        print(f"📊 {title} (Showing {min(top_n, len(results))} of {len(results)})")
        print("="*100)
        
        # Header
        print(f"{'#':<4} {'Player':<20} {'Stat':<8} {'Line':<6} {'Proj':<6} "
              f"{'Model%':<8} {'Book%':<8} {'EV%':<8} {'Odds':<7} {'Conf':<10}")
        print("-"*100)
        
        for i, r in enumerate(display_results[:top_n], 1):
            ev_pct = r['ev'] * 100
            model_pct = r['p_model'] * 100
            book_pct = r['p_book'] * 100
            
            emoji, tier = get_ev_tier(ev_pct)
            conf_emoji, conf_level = get_confidence_level(
                r['p_model'], r['projection'], r['line'], r['n_games']
            )
            
            odds_str = f"+{r['odds']}" if r['odds'] >= 0 else str(r['odds'])
            
            print(f"{i:<4} {r['player'][:19]:<20} {r['stat']:<8} {r['line']:<6.1f} "
                  f"{r['projection']:<6.1f} {model_pct:<7.1f}% {book_pct:<7.1f}% "
                  f"{emoji} {ev_pct:<5.1f}% {odds_str:<7} {conf_emoji} {conf_level}")
        
        print("="*100 + "\n")


# ==========================================
# DETAILED VIEW (Original Style)
# ==========================================

def display_detailed(results, top_n=20):
    """Original detailed view with all info"""
    
    if not results:
        print("\n⚠️ No results to display")
        return
    
    print("\n" + "="*80)
    print(f"🔥 TOP {min(top_n, len(results))} HIGHEST EV PROPS 🔥")
    print("="*80)
    
    for i, r in enumerate(results[:top_n], 1):
        ev_pct = r['ev'] * 100
        prob_pct = r['p_model'] * 100
        book_pct = r['p_book'] * 100
        
        emoji, tier = get_ev_tier(ev_pct)
        conf_emoji, conf_level = get_confidence_level(
            r['p_model'], r['projection'], r['line'], r['n_games']
        )
        
        print(f"\n{i}. {emoji} {tier} — {r['player']} - {r['stat']} {r['line']}")
        print(f"   {'─'*70}")
        print(f"   Opponent: {r['opponent'] or 'N/A'} | Position: {r['position']} | "
              f"DvP: {r['dvp_mult']:.3f} | Confidence: {conf_emoji} {conf_level}")
        print(f"   Projection: {r['projection']:.1f} | Model Prob: {prob_pct:.1f}% | "
              f"Book Prob: {book_pct:.1f}%")
        print(f"   Odds: {r['odds']:+d} | EV: {ev_pct:+.1f}¢ per $1 | "
              f"Edge: {prob_pct - book_pct:+.1f}%")
        print(f"   Games Analyzed: {r['n_games']} | Injury: {r['injury'] or '✅ Healthy'}")
        
        direction = "🟢 OVER" if r['projection'] > r['line'] else "🔴 UNDER"
        gap = abs(r['projection'] - r['line'])
        print(f"   {direction} VALUE (Proj {r['projection']:.1f} vs Line {r['line']}, "
              f"Gap: {gap:.1f})")


# ==========================================
# SUMMARY STATS VIEW
# ==========================================

def display_summary_stats(results):
    """Show aggregate statistics"""
    
    if not results:
        print("\n⚠️ No results to summarize")
        return
    
    df = pd.DataFrame(results)
    
    print("\n" + "="*80)
    print("📈 SUMMARY STATISTICS")
    print("="*80)
    
    # Overall stats
    total = len(results)
    positive_ev = len([r for r in results if r['ev'] > 0])
    avg_ev = df['ev'].mean() * 100
    avg_prob = df['p_model'].mean() * 100
    
    print(f"\n📊 Overall:")
    print(f"   Total Props Analyzed: {total}")
    print(f"   Positive EV Props: {positive_ev} ({positive_ev/total*100:.1f}%)")
    print(f"   Average EV: {avg_ev:.2f}¢")
    print(f"   Average Model Probability: {avg_prob:.1f}%")
    
    # EV tiers
    elite = len([r for r in results if r['ev'] * 100 >= 15])
    strong = len([r for r in results if 10 <= r['ev'] * 100 < 15])
    good = len([r for r in results if 5 <= r['ev'] * 100 < 10])
    slight = len([r for r in results if 0 < r['ev'] * 100 < 5])
    
    print(f"\n🔥 EV Distribution:")
    print(f"   🔥🔥🔥 Elite (15%+): {elite}")
    print(f"   🔥🔥 Strong (10-15%): {strong}")
    print(f"   🔥 Good (5-10%): {good}")
    print(f"   ✅ Slight (0-5%): {slight}")
    print(f"   ⚠️ Negative: {total - positive_ev}")
    
    # By stat type
    print(f"\n📋 By Stat Type:")
    stat_counts = df['stat'].value_counts()
    for stat, count in stat_counts.items():
        avg_stat_ev = df[df['stat'] == stat]['ev'].mean() * 100
        print(f"   {stat}: {count} props (Avg EV: {avg_stat_ev:+.1f}¢)")
    
    # Top players
    print(f"\n👤 Most Analyzed Players:")
    player_counts = df['player'].value_counts().head(5)
    for player, count in player_counts.items():
        print(f"   {player}: {count} props")
    
    # Confidence distribution
    high_conf = len([r for r in results if get_confidence_level(
        r['p_model'], r['projection'], r['line'], r['n_games']
    )[1] == "HIGH"])
    medium_conf = len([r for r in results if get_confidence_level(
        r['p_model'], r['projection'], r['line'], r['n_games']
    )[1] == "MEDIUM"])
    
    print(f"\n🎯 Confidence Levels:")
    print(f"   🟢 High Confidence: {high_conf}")
    print(f"   🟡 Medium Confidence: {medium_conf}")
    print(f"   🟠 Low Confidence: {total - high_conf - medium_conf}")
    
    print("="*80 + "\n")


# ==========================================
# EXPORT FUNCTIONS
# ==========================================

def export_to_csv(results, filename=None):
    """Export results to CSV"""
    if not results:
        print("\n⚠️ No results to export")
        return None
    
    if not filename:
        filename = f"prop_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    
    df = pd.DataFrame(results)
    
    # Add calculated fields
    df['ev_pct'] = df['ev'] * 100
    df['model_prob_pct'] = df['p_model'] * 100
    df['book_prob_pct'] = df['p_book'] * 100
    df['edge_pct'] = df['model_prob_pct'] - df['book_prob_pct']
    df['proj_line_gap'] = df['projection'] - df['line']
    
    # Reorder columns
    cols = ['player', 'stat', 'line', 'projection', 'proj_line_gap', 
            'model_prob_pct', 'book_prob_pct', 'edge_pct', 'ev_pct', 'odds',
            'opponent', 'position', 'dvp_mult', 'n_games', 'injury']
    
    df = df[cols]
    df.to_csv(filename, index=False)
    print(f"✅ Exported {len(results)} props to {filename}")
    return filename


def export_to_markdown(results, filename=None, top_n=20):
    """Export top props to Markdown for easy sharing"""
    if not results:
        print("\n⚠️ No results to export")
        return None
    
    if not filename:
        filename = f"prop_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    
    with open(filename, 'w') as f:
        f.write(f"# PropPulse+ Analysis Report\n")
        f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"**Total Props Analyzed:** {len(results)}\n\n")
        f.write("---\n\n")
        f.write("## Top Props by EV\n\n")
        
        for i, r in enumerate(results[:top_n], 1):
            ev_pct = r['ev'] * 100
            emoji, tier = get_ev_tier(ev_pct)
            
            f.write(f"### {i}. {emoji} {r['player']} - {r['stat']} {r['line']}\n\n")
            f.write(f"- **Tier:** {tier}\n")
            f.write(f"- **Opponent:** {r['opponent'] or 'N/A'}\n")
            f.write(f"- **Projection:** {r['projection']:.1f}\n")
            f.write(f"- **Model Probability:** {r['p_model']*100:.1f}%\n")
            f.write(f"- **Book Probability:** {r['p_book']*100:.1f}%\n")
            f.write(f"- **Expected Value:** {ev_pct:+.1f}¢ per $1\n")
            f.write(f"- **Odds:** {r['odds']:+d}\n")
            f.write(f"- **Games Analyzed:** {r['n_games']}\n\n")
    
    print(f"✅ Exported top {min(top_n, len(results))} props to {filename}")
    return filename


# ==========================================
# INTERACTIVE MENU (ENHANCED FOR 200+ PROPS)
# ==========================================

def interactive_display(results):
    """Interactive menu for exploring results - optimized for large datasets"""
    
    if not results:
        print("\n⚠️ No results to display")
        return
    
    current_results = results.copy()
    
    while True:
        print("\n" + "="*80)
        print("🎮 INTERACTIVE RESULTS VIEWER")
        print("="*80)
        print(f"📊 Current dataset: {len(current_results)} props (Original: {len(results)})")
        
        if len(current_results) != len(results):
            print(f"⚠️ Filters active - showing {len(current_results)}/{len(results)} props")
        
        print("\n📋 DISPLAY OPTIONS:")
        print("  [1] View All Props (Paginated - RECOMMENDED for 200+)")
        print("  [2] View Top N Props (Compact Table)")
        print("  [3] Detailed View (Top 20)")
        print("  [4] Summary Statistics")
        
        print("\n🔍 SORTING:")
        print("  [5] Sort by EV (default)")
        print("  [6] Sort by Model Probability")
        print("  [7] Sort by Projection")
        print("  [8] Sort by Confidence Level")
        print("  [9] Sort by Probability Edge")
        
        print("\n🎯 FILTERING:")
        print("  [10] Filter by Minimum EV %")
        print("  [11] Filter by Stat Type (PTS, REB, etc.)")
        print("  [12] Filter by Position")
        print("  [13] Filter by Probability Range")
        print("  [14] Search by Player Name")
        print("  [15] Show Only Positive EV")
        print("  [16] Show High Confidence Only")
        print("  [17] Reset All Filters")
        
        print("\n💾 EXPORT:")
        print("  [18] Export Current View to CSV")
        print("  [19] Export Top N to Markdown")
        print("  [20] Export All to CSV")
        
        print("\n  [0] Exit to Main Menu")
        print("="*80)
        
        choice = input("\n👉 Select option: ").strip()
        
        if choice == "0":
            print("\n✅ Returning to main menu...")
            break
        
        elif choice == "1":
            # Paginated view - best for 200+ props
            page_size = input("Props per page? (default=25, options: 10/25/50/100): ").strip()
            page_size = int(page_size) if page_size and page_size.isdigit() else 25
            display_compact_table(current_results, top_n=len(current_results), 
                                paginate=True, page_size=page_size)
        
        elif choice == "2":
            n = input("Show how many props? (default=50): ").strip()
            n = int(n) if n and n.isdigit() else 50
            display_compact_table(current_results, top_n=n)
        
        elif choice == "3":
            n = input("Show how many props? (default=20): ").strip()
            n = int(n) if n and n.isdigit() else 20
            display_detailed(current_results, top_n=n)
        
        elif choice == "4":
            display_summary_stats(current_results)
        
        elif choice == "5":
            current_results = sort_results(current_results, "ev")
            print("✅ Sorted by Expected Value (highest first)")
        
        elif choice == "6":
            current_results = sort_results(current_results, "prob")
            print("✅ Sorted by Model Probability (highest first)")
        
        elif choice == "7":
            current_results = sort_results(current_results, "projection")
            print("✅ Sorted by Projection (highest first)")
        
        elif choice == "8":
            current_results = sort_results(current_results, "confidence")
            print("✅ Sorted by Confidence Level (highest first)")
        
        elif choice == "9":
            current_results = sort_results(current_results, "edge")
            print("✅ Sorted by Probability Edge (highest first)")
        
        elif choice == "10":
            min_ev = input("Minimum EV % (e.g., 5 for 5%): ").strip()
            if min_ev:
                try:
                    min_ev = float(min_ev)
                    current_results = filter_results(current_results, min_ev=min_ev)
                    print(f"✅ Filtered to {len(current_results)} props with EV >= {min_ev}%")
                except ValueError:
                    print("❌ Invalid number")
        
        elif choice == "11":
            stats = input("Stat types (comma-separated, e.g., PTS,REB,AST): ").strip()
            if stats:
                current_results = filter_results(current_results, stats=stats)
                print(f"✅ Filtered to {len(current_results)} {stats} props")
        
        elif choice == "12":
            positions = input("Positions (comma-separated, e.g., PG,SG,SF): ").strip()
            if positions:
                current_results = filter_results(current_results, positions=positions)
                print(f"✅ Filtered to {len(current_results)} props")
        
        elif choice == "13":
            min_p = input("Minimum probability % (default=0): ").strip()
            max_p = input("Maximum probability % (default=100): ").strip()
            try:
                min_p = float(min_p) if min_p else 0
                max_p = float(max_p) if max_p else 100
                current_results = filter_results(current_results, min_prob=min_p, max_prob=max_p)
                print(f"✅ Filtered to {len(current_results)} props with prob {min_p}%-{max_p}%")
            except ValueError:
                print("❌ Invalid number")
        
        elif choice == "14":
            player = input("Enter player name (partial match OK): ").strip()
            if player:
                current_results = filter_results(current_results, player_search=player)
                print(f"✅ Found {len(current_results)} props matching '{player}'")
        
        elif choice == "15":
            current_results = filter_results(current_results, min_ev=0.01)
            print(f"✅ Filtered to {len(current_results)} positive EV props")
        
        elif choice == "16":
            high_conf = [r for r in current_results if get_confidence_level(
                r['p_model'], r['projection'], r['line'], r['n_games']
            )[1] == "HIGH"]
            current_results = high_conf
            print(f"✅ Filtered to {len(current_results)} high confidence props")
        
        elif choice == "17":
            current_results = results.copy()
            print(f"✅ Reset to all {len(current_results)} props")
        
        elif choice == "18":
            filename = input("Filename (press Enter for auto): ").strip()
            filename = filename if filename else None
            export_to_csv(current_results, filename)
        
        elif choice == "19":
            n = input("Export how many top props? (default=20): ").strip()
            n = int(n) if n and n.isdigit() else 20
            export_to_markdown(current_results, top_n=n)
        
        elif choice == "20":
            export_to_csv(current_results)
        
        else:
            print("❌ Invalid option - please try again")


# ==========================================
# MAIN REPLACEMENT FUNCTIONS
# ==========================================

def display_top_props(results, top_n=10, view="detailed"):
    """
    Main display function - replaces the one in prop_ev.py
    
    view options: "detailed", "compact", "summary", "interactive"
    """
    if not results:
        print("\n⚠️ No results to display")
        return
    
    if view == "compact":
        display_compact_table(results, top_n=top_n)
    elif view == "summary":
        display_summary_stats(results)
        display_compact_table(results, top_n=top_n)
    elif view == "interactive":
        interactive_display(results)
    else:  # detailed
        display_detailed(results, top_n=top_n)


# Quick access functions
def show_by_probability(results, top_n=50):
    """Show props sorted by model probability"""
    sorted_results = sort_results(results, "prob")
    display_compact_table(sorted_results, top_n=top_n, 
                         title=f"TOP PROPS BY MODEL PROBABILITY")


def show_high_confidence(results, top_n=30):
    """Show only high confidence props sorted by EV"""
    high_conf = [r for r in results if get_confidence_level(
        r['p_model'], r['projection'], r['line'], r['n_games']
    )[1] == "HIGH"]
    
    if not high_conf:
        print("\n⚠️ No high confidence props found")
        return
    
    display_compact_table(high_conf, top_n=top_n,
                         title=f"HIGH CONFIDENCE PROPS (n={len(high_conf)})")


def show_by_stat_type(results, stat_type="PTS"):
    """Show props for a specific stat type"""
    filtered = filter_results(results, stats=stat_type)
    
    if not filtered:
        print(f"\n⚠️ No {stat_type} props found")
        return
    
    display_compact_table(filtered, top_n=len(filtered),
                         title=f"{stat_type} PROPS (n={len(filtered)})")