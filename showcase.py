#!/usr/bin/env python3
"""
AUTONOMOUS ARTIST - COMPLETE SHOWCASE
Shows all features of the autonomous artist system
"""

from autonomous_artist import AutonomousArtist
import time

def separator(title=""):
    """Print a fancy separator"""
    if title:
        print(f"\n{'='*70}")
        print(f"  {title.upper()}")
        print(f"{'='*70}\n")
    else:
        print(f"{'─'*70}\n")

def showcase():
    """Complete showcase of the autonomous artist"""
    
    print("""
╔════════════════════════════════════════════════════════════════════╗
║                                                                    ║
║              AUTONOMOUS ARTIST - COMPLETE SHOWCASE                 ║
║                                                                    ║
║              An AI That Paints What It Feels                       ║
║              Demonstrating all features                            ║
║                                                                    ║
╚════════════════════════════════════════════════════════════════════╝
    """)
    
    # Create artist
    artist = AutonomousArtist(name="Aria")
    
    # ============================================================
    # FEATURE 1: Initial State & Personality
    # ============================================================
    separator("Feature 1: Unique Personality & State")
    
    print("Every artist instance starts with a unique personality:")
    state = artist.get_current_state()
    
    print(f"\n  Artist Name: {state['name']}")
    print(f"  Starting Mood: {state['mood'].upper()}")
    print(f"  Energy Level: {state['energy']}")
    print(f"  Complexity Tolerance: {state['complexity_tolerance']}")
    
    print("\n  Initial Style Affinities:")
    for style, value in state['style_affinities'].items():
        print(f"    • {style}: {value}")
    
    print("\n  Initial Subject Interests:")
    for interest, value in state['current_interests'].items():
        print(f"    • {interest}: {value}")
    
    # ============================================================
    # FEATURE 2: Artist Statement
    # ============================================================
    separator("Feature 2: Artist Statement (Personality)")
    
    statement = artist.get_artist_statement()
    print(f'"{statement}"')
    
    input("\n\nPress Enter to watch the artist paint...")
    
    # ============================================================
    # FEATURE 3: Autonomous Decision Making
    # ============================================================
    separator("Feature 3: Autonomous Decision Making")
    
    print("The artist decides what to paint based on its current state...\n")
    time.sleep(1)
    
    painting_data = artist.generate_prompt()
    
    print(f"✓ Subject chosen: {painting_data['subject']}")
    print(f"  (Based on interests: {artist.subject_interests.get(painting_data['subject'], 0.5):.2f})")
    
    print(f"\n✓ Style chosen: {painting_data['style']}")
    print(f"  (Based on affinity: {artist.style_affinities.get(painting_data['style'], 0.5):.2f})")
    
    print(f"\n✓ Color palette: {', '.join(painting_data['colors'])}")
    print(f"  (Influenced by mood: {painting_data['mood']})")
    
    print(f"\n✓ Energy affects complexity: {painting_data['energy']:.2f}")
    
    print("\n📝 Generated Prompt:")
    print(f"  {painting_data['prompt']}")
    
    # ============================================================
    # FEATURE 4: Reflection & Memory
    # ============================================================
    separator("Feature 4: Reflection & Memory")
    
    image_url = f"painting_{artist.painting_count + 1}.jpg"
    record = artist.record_painting(painting_data, image_url)
    
    print("After painting, the artist reflects on its work:\n")
    print(f'💭 "{record["reflection"]}"')
    
    print(f"\n✓ Painting recorded as #{record['number']}")
    print(f"✓ Satisfaction level: {record['satisfaction']:.2f}")
    print(f"✓ Theme added to memory: {record['subject']}")
    
    # ============================================================
    # FEATURE 5: State Evolution
    # ============================================================
    separator("Feature 5: State Evolution")
    
    print("After each painting, the artist's state evolves...\n")
    
    print("BEFORE:")
    print(f"  Energy: {state['energy']:.2f}")
    print(f"  Top style: {list(state['style_affinities'].keys())[0]} " +
          f"({list(state['style_affinities'].values())[0]:.2f})")
    
    new_state = artist.get_current_state()
    print(f"\nAFTER:")
    print(f"  Energy: {new_state['energy']:.2f} " +
          f"({'↑' if new_state['energy'] > state['energy'] else '↓'} change)")
    print(f"  Top style: {list(new_state['style_affinities'].keys())[0]} " +
          f"({list(new_state['style_affinities'].values())[0]:.2f})")
    
    input("\n\nPress Enter to paint more and see evolution...")
    
    # ============================================================
    # FEATURE 6: Learning & Anti-Repetition
    # ============================================================
    separator("Feature 6: Learning & Anti-Repetition")
    
    print("Painting 3 more pieces to demonstrate learning...\n")
    
    for i in range(3):
        print(f"Painting {i+2}/4...")
        painting_data = artist.generate_prompt()
        image_url = f"painting_{artist.painting_count + 1}.jpg"
        record = artist.record_painting(painting_data, image_url)
        
        print(f"  → {record['subject']} in {record['style']} style")
        print(f"  → Colors: {', '.join(record['colors'][:2])}")
        
        time.sleep(0.5)
    
    print("\n\nThemes explored so far:")
    for theme in set(artist.themes_explored):
        count = artist.themes_explored.count(theme)
        print(f"  • {theme}: {count} time(s)")
    
    print("\n✓ Notice: The artist avoids repeating the same theme too much")
    print("✓ Interests automatically rebalance to seek novelty")
    
    # ============================================================
    # FEATURE 7: Portfolio & History
    # ============================================================
    separator("Feature 7: Portfolio & History")
    
    print(f"Total paintings created: {len(artist.portfolio)}")
    print("\nRecent work:")
    
    for painting in artist.portfolio[-3:]:
        print(f"\n  #{painting['number']} - {painting['timestamp'][:19]}")
        print(f"  Subject: {painting['subject']} | Style: {painting['style']}")
        print(f"  Mood: {painting['mood']} | Energy: {painting['energy']:.2f}")
        print(f"  Reflection: \"{painting['reflection']}\"")
    
    # ============================================================
    # FEATURE 8: Mood Changes
    # ============================================================
    separator("Feature 8: Mood Can Change")
    
    print("Let's simulate what happens if the artist gets frustrated...\n")
    
    # Artificially lower satisfaction on last piece
    artist.portfolio[-1]['satisfaction'] = 0.2
    
    old_mood = artist.mood
    artist.evolve_state()
    
    print(f"Previous mood: {old_mood}")
    print(f"Current mood: {artist.mood}")
    
    if artist.mood != old_mood:
        print("\n✓ Mood shifted due to dissatisfaction with recent work!")
    else:
        print("\n(Mood remained stable this time)")
    
    # ============================================================
    # FEATURE 9: Persistence
    # ============================================================
    separator("Feature 9: Persistent Memory")
    
    print("All of this is automatically saved to disk:")
    print(f"  • Portfolio history (last 50 paintings)")
    print(f"  • Current mood and energy")
    print(f"  • Learned preferences")
    print(f"  • Theme history")
    print(f"  • Color usage patterns")
    
    print("\nIf you restart the program, the artist continues from where it left off")
    print("with all its memories and personality intact!")
    
    # ============================================================
    # FEATURE 10: The Artist's Journey
    # ============================================================
    separator("Feature 10: Artistic Journey")
    
    print("Watch how preferences evolve over time:\n")
    
    print("Style Affinity Changes:")
    for style in ['abstract', 'impressionist', 'minimalist']:
        if style in artist.style_affinities:
            print(f"  • {style}: {artist.style_affinities[style]:.2f}")
    
    print("\nThe artist is developing its own unique voice!")
    print("Over dozens of paintings, you'll see:")
    print("  • 'Periods' emerge (like Picasso's blue period)")
    print("  • Consistent stylistic evolution")
    print("  • Genuine creative trajectory")
    
    # ============================================================
    # CONCLUSION
    # ============================================================
    separator("Summary")
    
    print("""
This autonomous artist system demonstrates:

✓ Genuine decision-making based on internal state
✓ Personality that evolves through experience  
✓ Memory of past work influencing future choices
✓ Anti-repetition mechanisms for creative exploration
✓ Mood-driven aesthetic preferences
✓ Reflection and self-awareness
✓ Persistent identity across sessions
✓ Emergent artistic trajectory

It's not just a random art generator - it's an agent with
something resembling artistic intentionality.

The question isn't whether it "truly" feels - it's whether
the work it produces has coherence, personality, and meaning.

You decide.
    """)
    
    print("="*70)
    print(f"\n  Final Artist Statement:\n")
    print(f'  "{artist.get_artist_statement()}"')
    print("\n" + "="*70)

if __name__ == "__main__":
    try:
        showcase()
    except KeyboardInterrupt:
        print("\n\n👋 Showcase interrupted. The artist returns to dreaming...\n")
