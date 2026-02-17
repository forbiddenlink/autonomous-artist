# QUICK START GUIDE

## What You Built

An autonomous AI artist that:
- Has genuine moods and personality
- Makes its own creative decisions
- Evolves preferences over time
- Maintains memory of past work
- Develops its own artistic journey

## Fastest Way to See It Work

```bash
# Install dependencies
pip install flask

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
# Then visit: http://localhost:5000
```

## What Makes It Cool

1. **Real Personality**: Each instance starts with unique preferences
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

To add actual image generation:
1. Get API access to Hugging Face
2. Uncomment image generation code in `app.py`
3. Or integrate with your preferred image API

The prompt generation system is fully functional - it just needs
to be connected to an image generator.

## Watch It Evolve

Run it for 20+ paintings and you'll see:
- Artistic "periods" emerge (like Picasso's blue period)
- Genuine stylistic evolution
- Consistent creative trajectory
- Personality shining through

Enjoy your autonomous artist! 🎨
