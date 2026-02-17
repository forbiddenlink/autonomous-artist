from autonomous_artist import AutonomousArtist
import json
import time
from autonomous_artist import AutonomousArtist
import json
import time
from utils import generate_image_api, analyze_image_api

def demo_painting_session():
    """Run a demo painting session with the autonomous artist"""
    
    print("""
    ╔════════════════════════════════════════════════════════════╗
    ║                                                            ║
    ║              AUTONOMOUS ARTIST - DEMO                      ║
    ║              Watch an AI paint what it feels               ║
    ║                                                            ║
    ╚════════════════════════════════════════════════════════════╝
    """)
    
    # Create the artist
    artist = AutonomousArtist(name="Aria")
    
    # Show initial state
    print("\n📊 ARTIST'S CURRENT STATE")
    print("─" * 60)
    state = artist.get_current_state()
    print(f"Name: {state['name']}")
    print(f"Mood: {state['mood'].upper()}")
    print(f"Energy: {state['energy']}")
    print(f"Paintings Created So Far: {state['paintings_created']}")
    
    print("\nTop Interests:")
    for interest, value in list(state['current_interests'].items())[:3]:
        print(f"  • {interest}: {value}")
    
    print("\nPreferred Styles:")
    for style, value in list(state['style_affinities'].items())[:3]:
        print(f"  • {style}: {value}")
    
    # Get artist statement
    print(f"\n💬 ARTIST STATEMENT")
    print("─" * 60)
    print(artist.get_artist_statement())
    
    # Generate a painting
    print(f"\n\n🎨 THE ARTIST IS DECIDING WHAT TO PAINT...")
    print("─" * 60)
    time.sleep(1)
    
    painting_data = artist.generate_prompt()
    
    print(f"\nThe artist has decided to create:")
    print(f"  Subject: {painting_data['subject']}")
    print(f"  Style: {painting_data['style']}")
    print(f"  Colors: {', '.join(painting_data['colors'])}")
    print(f"  Mood: {painting_data['mood']}")
    print(f"  Energy Level: {painting_data['energy']:.2f}")
    
    print(f"\n📝 GENERATED PROMPT:")
    print("─" * 60)
    print(painting_data['prompt'])
    
    print(f"\n\n🖼️  Generating image using Flux.1 (Hugging Face)...")
    result = generate_image_api(painting_data['prompt'])
    
    image_url = "generation_failed.jpg"
    visual_description = None
    
    if result["success"]:
        print(f"✓ Success! Image saved to: {result['image_url']}")
        image_url = result['image_url']
        
        # Analyze the image (Vision)
        print(f"\n👁️  The Artist is looking at the work...")
        visual_description = analyze_image_api(result['image_url'], prompt_context=painting_data['prompt'])
        print(f"   Vision Analysis: \"{visual_description}\"")
        
    else:
        print(f"❌ Error: {result.get('error')}")
    
    # Simulate recording the painting with critique
    record = artist.record_painting(painting_data, image_url, visual_description)
    
    print(f"\n💭 ARTIST'S REFLECTION:")
    print("─" * 60)
    print(f"\"{record['reflection']}\"")
    
    if record.get('journal'):
        print(f"\n📖 DIARY ENTRY:")
        print(f"\"{record['journal']}\"")
    
    print(f"\n\n✅ PAINTING COMPLETE")
    print("─" * 60)
    print(f"Painting #{record['number']} has been created and recorded.")
    print(f"The artist's state has evolved based on this experience.")
    
    # Show how state changed
    new_state = artist.get_current_state()
    print(f"\nNew mood: {new_state['mood']}")
    print(f"New energy: {new_state['energy']}")
    print("\n" + "="*60)

if __name__ == "__main__":
    demo_painting_session()
