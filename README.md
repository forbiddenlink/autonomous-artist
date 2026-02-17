# Autonomous Artist - An AI That Paints What It Feels

An AI artist with genuine personality, evolving preferences, and autonomous decision-making. Watch as it develops its own artistic voice over time.

## What Makes This Special

This isn't just an image generator - it's an **autonomous creative agent** that:

- **Has moods** that influence its artistic choices (contemplative, chaotic, melancholic, energized, etc.)
- **Develops preferences** over time based on what it's painted
- **Gets bored** of repeated themes and seeks novelty
- **Evolves its style** naturally through experience
- **Reflects on its work** like a real artist would
- **Maintains memory** of its artistic journey

## How It Works

### The Artist's Mind

The artist has several interconnected systems that create emergent behavior:

#### 1. Emotional State
- **Mood**: Current emotional state (contemplative, energized, melancholic, etc.)
- **Energy**: Affects complexity and detail (0.0 - 1.0)
- **Complexity Tolerance**: How intricate the work becomes

#### 2. Learned Preferences
- **Style Affinities**: Evolving preferences for abstract, figurative, surreal, etc.
- **Color Preferences**: Warm vs cool, vibrant vs muted
- **Subject Interests**: Nature, urban, portraits, landscapes, etc.

#### 3. Memory System
- Records all past paintings
- Tracks repeated themes
- Avoids overused subjects
- Colors used recently
- Satisfaction with previous work

#### 4. Evolution
After each painting, the artist:
- Adjusts preferences based on satisfaction
- Gets bored of repeated themes
- Experiences energy fluctuations
- Potentially shifts mood based on recent work
- Drifts naturally in its stylistic tendencies

## Features

### Autonomous Decision-Making
The artist independently chooses:
- What subject to paint (based on current interests)
- What style to use (influenced by mood and preferences)
- Color palette (mood-dependent, avoids recent colors)
- Level of complexity (energy-dependent)

### Personality
Each artist instance develops its own unique voice:
- Different starting preferences
- Unique mood patterns
- Individual artistic trajectory
- Personal reflection style

### Memory & Growth
- Maintains a portfolio of all work
- Tracks themes it's explored
- Evolves preferences organically
- Develops artistic "periods" (like a blue period)

## Installation

```bash
# Clone or download the project
cd autonomous-artist

# Install dependencies
pip install -r requirements.txt
```

## Usage

### Option 1: Interactive CLI

```bash
python3 artist_cli.py
```

This opens an interactive menu where you can:
1. Let the artist paint
2. View current state
3. Read artist statement
4. View portfolio
5. Force state evolution
6. Exit

### Option 2: Command Line Options

```bash
# Paint one piece
python3 artist_cli.py --paint

# Paint a series of 5 pieces
python3 artist_cli.py --series 5

# View artist statement
python3 artist_cli.py --statement

# View recent portfolio
python3 artist_cli.py --portfolio

# View current state
python3 artist_cli.py --state

# Create an artist with a different name
python3 artist_cli.py --name "Vincent" --paint
```

### Option 3: Web Interface

```bash
# Start the Flask server
python3 app.py

# Open browser to http://localhost:5000
```

The web interface provides:
- Real-time state visualization
- Interactive painting controls
- Portfolio gallery
- Artist statements

### Option 4: Demo Script

```bash
python3 demo.py
```

Shows a complete painting session with detailed explanations.

## Image Generation

The system generates detailed prompts based on the artist's state. To actually generate images, you need:

1. **Hugging Face Integration**: The system is designed to work with Hugging Face's FLUX.1-Krea-dev model
2. **MCP Interface**: Full image generation works through Claude's MCP interface with the dynamic_space tool
3. **Alternative**: You can integrate any image generation API by modifying the `generate_image()` function in `app.py`

### Example Generated Prompt

```
abstract composition with non-representational forms, 
featuring natural landscapes, forests, or organic forms, 
using a palette of muted blues, soft grays, 
evoking quiet contemplation, 
professional photography, 8k uhd, high quality, masterpiece
```

## Project Structure

```
autonomous-artist/
├── autonomous_artist.py   # Core artist AI with mood, memory, evolution
├── app.py                 # Flask web application
├── artist_cli.py          # Command-line interface
├── demo.py               # Demo script
├── templates/
│   └── index.html        # Web interface
├── requirements.txt      # Python dependencies
├── artist_memory.json    # Persistent artist state (auto-created)
└── README.md            # This file
```

## Artist Moods & Their Influence

Each mood affects the artist's choices differently:

- **Contemplative**: Minimalist, abstract, quiet colors
- **Energized**: Maximalist, vibrant, dynamic
- **Melancholic**: Muted tones, impressionist, introspective
- **Chaotic**: Abstract, surreal, clashing colors
- **Serene**: Soft pastels, gentle compositions
- **Restless**: Agitated colors, experimental
- **Nostalgic**: Vintage hues, figurative
- **Curious**: Exploratory palettes, unexpected combinations
- **Introspective**: Deep colors, inward-focused
- **Rebellious**: Rule-breaking, aggressive contrasts
- **Dreamy**: Ethereal, floating compositions
- **Focused**: Clear, decisive, purposeful

## Technical Details

### State Persistence
Artist state is automatically saved to `artist_memory.json` after each painting, including:
- Current mood and energy
- Style and subject preferences
- Complete portfolio (last 50 paintings)
- Theme history
- Recent color usage

### Preference Evolution Algorithm
Preferences drift through:
- Random walk (exploration)
- Reinforcement (repeated satisfaction)
- Novelty seeking (anti-repetition)
- Mood-based adjustments
- Energy-dependent complexity

### Decision Making
The artist uses weighted random selection based on:
1. Current mood (30% influence)
2. Learned preferences (50% influence)
3. Random exploration (20% influence)
4. Anti-repetition bias

## Extending the System

### Add New Moods
Edit `_generate_initial_mood()` in `autonomous_artist.py`:
```python
moods = [
    "contemplative", "energized", "melancholic",
    "your_new_mood_here"  # Add here
]
```

### Add New Styles
Add to `style_affinities` in `__init__()`:
```python
self.style_affinities = {
    "abstract": random.uniform(0, 1),
    "your_new_style": random.uniform(0, 1),  # Add here
}
```

### Integrate Different Image APIs
Modify `generate_image()` in `app.py` to call your preferred API.

### Adjust Evolution Rate
Change drift amounts in `evolve_state()`:
```python
drift = random.uniform(-0.05, 0.05)  # Adjust these values
```

## Example Session

```
🎨 Starting painting session...

📊 ARTIST'S CURRENT STATE
==================================================
Mood: CURIOUS
Energy: 0.44
Paintings Created: 0

Current Interests:
  • conceptual: 0.9
  • architecture: 0.72
  • portraits: 0.65

──────────────────────────────────────────────────
THE ARTIST HAS DECIDED TO PAINT...
──────────────────────────────────────────────────

Subject: architecture
Style: conceptual
Colors: questioning tones, exploratory palettes
Mood Influence: curious
Energy Level: 0.44

💭 Artist's Reflection:
  "My conceptual approach felt right for what I was feeling."

✓ Painting #1 complete!
```

## Philosophy

This project explores the question: **Can an AI have artistic agency?**

Rather than being a tool that responds to human prompts, this system makes its own creative decisions based on an internal state that evolves over time. It doesn't have "true" feelings, but it has something functionally similar - a complex system of preferences, memories, and decision-making that creates the appearance (and perhaps the reality) of artistic intentionality.

The interesting part isn't whether it's "really" feeling anything, but whether the work it produces has coherence, personality, and an authentic creative trajectory.

## Future Enhancements

Potential additions:
- [ ] Visual analysis of its own work to inform future decisions
- [ ] Collaborative mode (responding to viewer feedback)
- [ ] Multiple artist personalities that can interact
- [ ] Learning from art history (feeding it museum collections)
- [ ] "Dream journal" where it writes about its artistic process
- [ ] Music composition based on visual mood
- [ ] Gallery website with automatic updates

## License

MIT License - Do whatever you want with this

## Credits

Created as an exploration of autonomous creative AI systems.

---

*"I'm not sure why I chose architecture, but it felt necessary."* - Aria
