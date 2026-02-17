from autonomous_artist import AutonomousArtist
import sys

print("Initializing Artist...")
try:
    artist = AutonomousArtist()
    print(f"Artist initialized: {artist.name}")
    print(f"Current Mood: {artist.mood}")
    print(f"Portfolio size: {len(artist.portfolio)}")
    
    print("Testing Generation...")
    prompt = artist.generate_prompt()
    print(f"Generated prompt about: {prompt['subject']}")
    
    print("SUCCESS: Architecture valid.")
except Exception as e:
    print(f"FAILURE: {e}")
    import traceback
    traceback.print_exc()
