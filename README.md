# Autonomous Artist

> **Successor project:** this work continued as [the-becoming](https://github.com/forbiddenlink/the-becoming). This repository is kept as the original version.

A Python project in which a simulated artist has moods, preferences and a memory of its past work. It picks its own subjects, styles and palettes, builds an image prompt from that state, and can send the prompt to Hugging Face to render a picture. It is an experiment in artistic agency, not a product. There is no hosted instance.

## What it does

The artist is a state machine that drives an image generator. It:

- **Has moods** that influence its artistic choices (contemplative, chaotic, melancholic, energized, etc.)
- **Develops preferences** over time based on what it's painted
- **Gets bored** of repeated themes and seeks novelty
- **Evolves its style** naturally through experience
- **Reflects on its work** like a real artist would
- **Maintains memory** of its artistic journey

## How it works

### The artist's state

The artist keeps several linked pieces of state:

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

Requires Python 3 (the `Dockerfile` uses Python 3.14).

```bash
git clone https://github.com/forbiddenlink/autonomous-artist
cd autonomous-artist
pip install -r requirements.txt
cp .env.example .env   # set HF_API_TOKEN to render images
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

# Also render images through Hugging Face (needs HF_API_TOKEN)
python3 artist_cli.py --paint --generate

# Create an artist with a different name
python3 artist_cli.py --name "Vincent" --paint
```

### Option 3: Web Interface

```bash
# Start the Flask server
python3 app.py

# Open http://localhost:5001 (the PORT setting; default 5001)
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

## Image generation

The system builds a detailed prompt from the artist's state. `generate_image_api()` in `utils.py` sends it to Hugging Face through `huggingface_hub.InferenceClient`. It needs `HF_API_TOKEN`. The default model is `black-forest-labs/FLUX.1-schnell` with `stabilityai/stable-diffusion-xl-base-1.0` as fallback (`IMAGE_MODEL` and `IMAGE_FALLBACK_MODEL` override them). Without a token the call returns an error and the web app records the painting with a placeholder image; the CLI only renders images when you pass `--generate`. To use another provider, replace `generate_image_api()`.

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
├── autonomous_artist.py   # AutonomousArtist: state, prompt generation, evolution
├── artist_modules/        # brain, critic, memory, painter
├── app.py                 # Flask web application and JSON API (see API.md)
├── artist_cli.py          # Command-line interface
├── utils.py               # Hugging Face image and vision calls, retries
├── config.py              # Environment-driven settings
├── cache_manager.py       # Response cache
├── demo.py, showcase.py   # Demo scripts
├── templates/index.html   # Web interface
├── test_comprehensive.py  # pytest suite (also test_no_hardcoded_tokens.py)
├── Dockerfile, docker-compose.yml, nginx.conf, deploy*.sh
├── .env.example           # Environment variable names and defaults
├── requirements.txt       # Python dependencies
└── artist_memory.json     # Persistent artist state (auto-created)
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
- **Whimsical**, **Gothic**, **Cyberpunk**, **Anxious**: also defined in `artist_modules/brain.py`

## Technical Details

### State Persistence
Artist state is automatically saved to `artist_memory.json` after each painting, including:
- Current mood and energy
- Style and subject preferences
- Portfolio (the last `MAX_PORTFOLIO_SIZE` paintings, default 50)
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
The artist uses weighted random selection. For style (`choose_style()`), 15% of picks are a random wildcard; otherwise it picks among the styles mapped to the current mood, weighted by its learned affinity plus a small mood boost. Subject and color choices also avoid recent repeats.

## Extending the System

### Add New Moods
Add the mood to `self.MOODS` in `artist_modules/brain.py`, then add it to `mood_style_map` in `choose_style()` so it maps to styles.

### Add New Styles
Add an entry to the initial `style_affinities` dict in `autonomous_artist.py` (around line 70).

### Integrate Different Image APIs
Modify `generate_image_api()` in `utils.py` to call your preferred API.

### Adjust Evolution Rate
Change the drift amounts in `evolve_state()` in `artist_modules/brain.py` (style affinities use `random.uniform(-0.05, 0.05)`).

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

Not built yet. Vision analysis of its own work (`analyze_image_api()`) and journal entries (`write_journal_entry()`) already exist.

- [ ] Collaborative mode (responding to viewer feedback)
- [ ] Multiple artist personalities that can interact
- [ ] Learning from art history (feeding it museum collections)
- [ ] Music composition based on visual mood
- [ ] Gallery website with automatic updates

## License

MIT. See `LICENSE`.

*"I'm not sure why I chose architecture, but it felt necessary."* - Aria
