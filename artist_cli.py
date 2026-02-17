#!/usr/bin/env python3
"""
Autonomous Artist CLI - Let the AI paint on its own
"""

import json
import time
from autonomous_artist import AutonomousArtist
import argparse
import sys
from utils import generate_image_api, analyze_image_api
from pathlib import Path
import sys

def print_banner():
    """Print a nice banner"""
    banner = """
    ╔═══════════════════════════════════════════════╗
    ║                                               ║
    ║        AUTONOMOUS ARTIST - ARIA               ║
    ║        An AI That Paints What It Feels       ║
    ║                                               ║
    ╚═══════════════════════════════════════════════╝
    """
    print(banner)

def paint_session(artist, use_real_generation=False):
    """Conduct a full painting session"""
    print("\n" + "="*50)
    print("STARTING NEW PAINTING SESSION")
    print("="*50)
    
    # 1. Evolve state slightly before starting
    print("\n🧠 Artist is thinking...")
    artist.evolve_state()
    
    # 2. Decide what to paint
    painting_data = artist.generate_prompt()
    print_painting_decision(artist, painting_data, use_real_generation)
    
    return painting_data

def print_state(artist):
    """Print the artist's current state"""
    print("\n" + "="*50)
    print("ARTIST'S CURRENT STATE")
    print("="*50)
    state = artist.get_current_state()
    
    print(f"\nMood: {state['mood'].upper()}")
    print(f"Energy: {state['energy']}")
    print(f"Paintings Created: {state['paintings_created']}")
    
    print("\nCurrent Interests:")
    for interest, value in state['current_interests'].items():
        print(f"  • {interest}: {value}")
    
    print("\nStyle Affinities:")
    for style, value in state['style_affinities'].items():
        print(f"  • {style}: {value}")
    
    print("\n" + "="*50)

def print_painting_decision(artist, painting_data, use_real_generation=False):
    """Print what the artist decided to paint"""
    print("\n" + "─"*50)
    print("THE ARTIST HAS DECIDED TO PAINT...")
    print("─"*50)
    
    # ... (print statements omitted for brevity, they are unchanged)
    
    print(f"\nSubject: {painting_data['subject']}")
    print(f"Style: {painting_data['style']}")
    print(f"Colors: {', '.join(painting_data['colors'])}")
    print(f"Mood Influence: {painting_data['mood']}")
    print(f"Energy Level: {painting_data['energy']:.2f}")
    
    print("\nFull Prompt:")
    print(f"  {painting_data['prompt']}")
    print("\n" + "─"*50)

    
    # Generate image if requested
    visual_description = None
    if use_real_generation:
        print("\n🖼️  Generating image via Hugging Face (Flux.1/SDXL)...")
        result = generate_image_api(painting_data['prompt'])
        
        if result['success']:
            image_url = result['image_url']
            print(f"✓ Image generated: {image_url}")
            
            # Vision Step
            print("👁️  The Artist is looking at the work...")
            visual_description = analyze_image_api(image_url, prompt_context=painting_data['prompt'])
            print(f"   Analysis: \"{visual_description}\"")
            
        else:
            print(f"❌ Generation failed: {result.get('error')}")
            image_url = "generation_failed.jpg"
    else:
        image_url = f"painting_{artist.painting_count + 1}.jpg"
        print("\n(Skipping actual image generation - use --generate flag to enable)")
    
    # Record the painting
    record = artist.record_painting(painting_data, image_url, visual_description)
    
    # Show artist's reflection
    print("\n💭 Artist's Reflection:")
    print(f"  \"{record['reflection']}\"")
    
    print(f"\n✓ Painting #{record['number']} complete!")
    
    return record

def artist_statement(artist):
    """Show the artist's statement"""
    statement = artist.get_artist_statement()
    
    print("\n" + "="*50)
    print("ARTIST STATEMENT")
    print("="*50)
    print(f"\n{statement}\n")
    print("="*50)

def portfolio_view(artist):
    """Show recent portfolio"""
    print("\n" + "="*50)
    print("RECENT PORTFOLIO")
    print("="*50)
    
    if not artist.portfolio:
        print("\nNo paintings yet. Let the artist create something!")
        return
    
    recent = artist.portfolio[-5:]
    for painting in recent:
        print(f"\n#{painting['number']} - {painting['timestamp'][:10]}")
        print(f"  Subject: {painting['subject']}")
        print(f"  Style: {painting['style']}")
        print(f"  Mood: {painting['mood']}")
        print(f"  Reflection: \"{painting['reflection']}\"")
    
    print(f"\nTotal paintings: {len(artist.portfolio)}")
    print("="*50)

def interactive_mode(artist):
    """Interactive CLI mode"""
    print_banner()
    
    while True:
        print("\n\nWhat would you like to do?")
        print("1. Let the artist paint")
        print("2. View artist's current state")
        print("3. Read artist statement")
        print("4. View recent portfolio")
        print("5. Force state evolution")
        print("6. Exit")
        
        choice = input("\nEnter choice (1-6): ").strip()
        
        if choice == '1':
            paint_session(artist)
        elif choice == '2':
            print_state(artist)
        elif choice == '3':
            artist_statement(artist)
        elif choice == '4':
            portfolio_view(artist)
        elif choice == '5':
            print("\n🔄 Evolving artist's state...")
            artist.evolve_state()
            print("✓ State evolved!")
            print_state(artist)
        elif choice == '6':
            print("\n👋 Goodbye! The artist will continue dreaming...\n")
            break
        else:
            print("\n❌ Invalid choice. Please try again.")

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Autonomous Artist CLI')
    parser.add_argument('--paint', action='store_true', help='Paint one piece and exit')
    parser.add_argument('--series', type=int, metavar='N', help='Paint N pieces in a row')
    parser.add_argument('--statement', action='store_true', help='Show artist statement')
    parser.add_argument('--portfolio', action='store_true', help='Show recent portfolio')
    parser.add_argument('--state', action='store_true', help='Show current state')
    parser.add_argument('--generate', action='store_true', help='Actually generate images (requires HF)')
    parser.add_argument('--name', type=str, default='Aria', help='Artist name')
    
    args = parser.parse_args()
    
    # Create artist
    artist = AutonomousArtist(name=args.name)
    
    # Handle different modes
    if args.statement:
        print_banner()
        artist_statement(artist)
    elif args.portfolio:
        print_banner()
        portfolio_view(artist)
    elif args.state:
        print_banner()
        print_state(artist)
    elif args.paint:
        print_banner()
        paint_session(artist, use_real_generation=args.generate)
    elif args.series:
        print_banner()
        print(f"\n🎨 Starting series of {args.series} paintings...\n")
        for i in range(args.series):
            print(f"\n{'='*50}")
            print(f"PAINTING {i+1} of {args.series}")
            print(f"{'='*50}")
            paint_session(artist, use_real_generation=args.generate)
            if i < args.series - 1:
                time.sleep(2)  # Pause between paintings
    else:
        # Interactive mode
        interactive_mode(artist)

if __name__ == '__main__':
    main()
