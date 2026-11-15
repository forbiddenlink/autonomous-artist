# Quick start

## What this is

A simulated artist that:
- Has moods and a personality profile
- Makes its own creative decisions
- Evolves preferences over time
- Maintains memory of past work
- Develops its own artistic journey

## Fastest Way to See It Work

```bash
# Install dependencies
pip install -r requirements.txt

# Run the interactive demo
python3 showcase.py

# Or use the CLI
python3 artist_cli.py
```

## Files Included

- `autonomous_artist.py` - Core AI artist engine
- `app.py` - Web server (run with: python3 app.py)
- `artist_cli.py` - Command line interface
- `demo.py` - Simple demonstration
- `showcase.py` - Complete feature showcase
- `artist_modules/` - brain, critic, memory and painter modules
- `utils.py` and `config.py` - image calls and settings
- `templates/index.html` - Web interface
- `README.md` - Full documentation

## Try It Now

```bash
# Paint one piece
python3 artist_cli.py --paint

# Paint a series of 5
python3 artist_cli.py --series 5

# Interactive mode
python3 artist_cli.py

# Web interface
python3 app.py
# Then visit: http://localhost:5001
```

## What Makes It Cool

1. **Personality**: Each instance starts with unique preferences
2. **Evolution**: Gets bored, shifts interests, changes moods
3. **Memory**: Remembers everything it's painted
4. **Anti-Repetition**: Actively avoids repeating itself
5. **Reflection**: Comments on its own work
6. **Persistence**: Continues from where it left off

## The Philosophy

This isn't just a prompt wrapper. It's an exploration of:
- Can AI have artistic agency?
- What does autonomous creativity look like?
- Does "feeling" require consciousness, or just complex behavior?

The artist makes decisions based on internal state that evolves
through experience. Whether it "truly" feels is beside the point - 
what matters is whether its work has coherence and meaning.

## Next Steps

To render images:
1. Create a Hugging Face token
2. Copy `.env.example` to `.env` and set `HF_API_TOKEN`
3. Run `python3 artist_cli.py --paint --generate`, or use the web app

Image generation is implemented in `utils.py` (`generate_image_api()`).

## Watch It Evolve

Run it for 20+ paintings and you'll see:
- Artistic "periods" emerge (like Picasso's blue period)
- Stylistic evolution
- Consistent creative trajectory
- Personality shining through


