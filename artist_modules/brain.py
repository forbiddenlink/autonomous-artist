import random
from typing import Dict, List, Any, Optional
# We assume utils is available in path (since app.py is entry point)
try:
    from utils import generate_text_api
except ImportError:
    # If running as package
    from ..utils import generate_text_api

class ArtistBrain:
    """
    Handles the cognitive processes of the artist:
    - Determining mood evolution
    - Selecting subjects and styles
    - Reflecting on work (LLM)
    - Writing journal entries (LLM)
    """

    def __init__(self):
        # Configuration / Knowledge Base
        self.MOODS = [
            "contemplative", "energized", "melancholic", "chaotic",
            "serene", "restless", "nostalgic", "curious",
            "introspective", "rebellious", "dreamy", "focused",
            "whimsical", "gothic", "cyberpunk", "anxious"
        ]

        # Mood transition matrix - defines natural emotional flow
        # Higher values = more likely transitions
        self.MOOD_TRANSITIONS = {
            "contemplative": {"serene": 0.25, "introspective": 0.25, "melancholic": 0.15, "curious": 0.15, "dreamy": 0.1, "focused": 0.1},
            "energized": {"chaotic": 0.2, "whimsical": 0.2, "rebellious": 0.15, "curious": 0.15, "focused": 0.15, "restless": 0.15},
            "melancholic": {"contemplative": 0.2, "introspective": 0.2, "gothic": 0.2, "nostalgic": 0.2, "serene": 0.1, "dreamy": 0.1},
            "chaotic": {"rebellious": 0.25, "energized": 0.2, "restless": 0.2, "cyberpunk": 0.15, "whimsical": 0.1, "curious": 0.1},
            "serene": {"contemplative": 0.25, "dreamy": 0.25, "focused": 0.2, "introspective": 0.15, "nostalgic": 0.15},
            "restless": {"chaotic": 0.2, "energized": 0.2, "rebellious": 0.2, "curious": 0.15, "anxious": 0.15, "focused": 0.1},
            "nostalgic": {"melancholic": 0.2, "contemplative": 0.2, "dreamy": 0.2, "serene": 0.2, "introspective": 0.2},
            "curious": {"energized": 0.2, "whimsical": 0.2, "focused": 0.2, "contemplative": 0.15, "rebellious": 0.15, "dreamy": 0.1},
            "introspective": {"contemplative": 0.25, "melancholic": 0.2, "serene": 0.2, "focused": 0.15, "nostalgic": 0.1, "dreamy": 0.1},
            "rebellious": {"chaotic": 0.25, "energized": 0.2, "cyberpunk": 0.2, "restless": 0.15, "gothic": 0.1, "focused": 0.1},
            "dreamy": {"serene": 0.25, "nostalgic": 0.2, "whimsical": 0.2, "contemplative": 0.15, "introspective": 0.1, "melancholic": 0.1},
            "focused": {"contemplative": 0.2, "energized": 0.2, "serene": 0.2, "curious": 0.2, "introspective": 0.2},
            "whimsical": {"dreamy": 0.25, "energized": 0.2, "curious": 0.2, "serene": 0.15, "nostalgic": 0.1, "chaotic": 0.1},
            "gothic": {"melancholic": 0.25, "introspective": 0.2, "rebellious": 0.2, "cyberpunk": 0.15, "contemplative": 0.1, "dreamy": 0.1},
            "cyberpunk": {"rebellious": 0.25, "chaotic": 0.2, "energized": 0.2, "focused": 0.15, "gothic": 0.1, "restless": 0.1}
        }
    
    def evolve_state(self, current_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Input: Current state (mood, energy, satisfaction of last piece)
        Output: Updated state (mood, energy, preferences)
        """
        state = current_state

        # Energy fluctuates with more variance for interesting dynamics
        energy_change = random.uniform(-0.2, 0.2)
        state['energy'] += energy_change
        # Allow energy to go lower to enable calm moods
        state['energy'] = max(0.15, min(0.95, state['energy']))

        current_mood = state.get('mood', 'contemplative')

        # Track mood history for anti-repetition
        mood_history = state.get('mood_history', [])
        mood_history.append(current_mood)
        # Keep last 10 moods
        state['mood_history'] = mood_history[-10:]

        # Mood evolution using transition matrix (60% chance to shift)
        if random.random() < 0.6:
            new_mood = self._select_next_mood(current_mood, state['energy'], mood_history)
            state['mood'] = new_mood

        # Frustration override (check last painting satisfaction)
        portfolio = state.get('portfolio', [])
        if portfolio:
            last_piece = portfolio[-1]
            satisfaction = last_piece.get('satisfaction', 0.5)

            # Low satisfaction triggers mood shift
            if satisfaction < 0.3 and random.random() < 0.6:
                frustration_moods = ["restless", "chaotic", "rebellious", "introspective"]
                # Avoid current mood
                frustration_moods = [m for m in frustration_moods if m != state['mood']]
                state['mood'] = random.choice(frustration_moods)

            # High satisfaction reinforces or moves to positive moods
            elif satisfaction > 0.85 and random.random() < 0.4:
                positive_moods = ["serene", "focused", "dreamy", "whimsical", "curious"]
                positive_moods = [m for m in positive_moods if m != state['mood']]
                state['mood'] = random.choice(positive_moods)

        # Preference Drift - styles
        affinities = state.get('style_affinities', {})
        for key in affinities:
            drift = random.uniform(-0.05, 0.05)
            affinities[key] = max(0.1, min(1.0, affinities[key] + drift))
        state['style_affinities'] = affinities

        # Subject interest evolution with boredom logic
        interests = state.get('subject_interests', {})
        themes_explored = state.get('themes_explored', [])

        if len(themes_explored) > 5:
            recent = themes_explored[-5:]
            counts = {t: recent.count(t) for t in set(recent)}
            for theme, count in counts.items():
                if count > 2 and theme in interests:
                    # Stronger boredom penalty
                    interests[theme] *= 0.6

        # Small random drift for interests
        for key in interests:
            drift = random.uniform(-0.03, 0.03)
            interests[key] = max(0.1, min(1.0, interests[key] + drift))

        # Normalize interests
        total = sum(interests.values())
        if total > 0:
            for key in interests:
                interests[key] = (interests[key] / total) * len(interests) * 0.5

        state['subject_interests'] = interests

        # Personality evolution (very slow drift)
        personality = state.get('personality', {})
        if personality:
            for trait in personality:
                # Tiny random drift (±0.01)
                drift = random.uniform(-0.01, 0.01)
                personality[trait] = max(0.1, min(0.95, personality[trait] + drift))

            # Significant experiences can shift personality more
            if portfolio:
                last_satisfaction = portfolio[-1].get('satisfaction', 0.5)
                # Very high or very low satisfaction has small personality impact
                if last_satisfaction > 0.9:
                    # Success boosts openness slightly
                    personality['openness'] = min(0.95, personality.get('openness', 0.5) + 0.02)
                elif last_satisfaction < 0.25:
                    # Failure can increase neuroticism or decrease it (resilience)
                    if random.random() < 0.5:
                        personality['neuroticism'] = min(0.9, personality.get('neuroticism', 0.5) + 0.02)
                    else:
                        # Building resilience
                        personality['neuroticism'] = max(0.1, personality.get('neuroticism', 0.5) - 0.01)

            state['personality'] = personality

        return state

    def _select_next_mood(self, current_mood: str, energy: float, mood_history: List[str]) -> str:
        """Select next mood using transition matrix with anti-repetition"""
        # Get transition probabilities for current mood
        transitions = self.MOOD_TRANSITIONS.get(current_mood, {})

        if not transitions:
            # Fallback to any mood except current
            candidates = [m for m in self.MOODS if m != current_mood]
            return random.choice(candidates)

        # Build weighted candidates
        candidates = list(transitions.keys())
        weights = list(transitions.values())

        # Energy influence - boost certain moods based on energy
        for i, mood in enumerate(candidates):
            if energy > 0.7 and mood in ["energized", "chaotic", "rebellious", "cyberpunk"]:
                weights[i] *= 1.5
            elif energy < 0.4 and mood in ["contemplative", "serene", "melancholic", "dreamy"]:
                weights[i] *= 1.5

        # Anti-repetition: penalize moods that appeared recently
        recent_moods = mood_history[-3:] if mood_history else []
        for i, mood in enumerate(candidates):
            if mood in recent_moods:
                # Reduce weight for recently used moods
                weights[i] *= 0.3
            if mood == current_mood:
                # Heavily penalize staying in same mood
                weights[i] *= 0.1

        # Filter out moods from valid MOODS list and ensure valid candidates
        valid_candidates = []
        valid_weights = []
        for mood, weight in zip(candidates, weights):
            if mood in self.MOODS:
                valid_candidates.append(mood)
                valid_weights.append(weight)

        if not valid_candidates:
            # Fallback
            return random.choice([m for m in self.MOODS if m != current_mood])

        return random.choices(valid_candidates, weights=valid_weights)[0]

    def choose_subject(self, interests: Dict[str, float], themes_explored: List[str] = None) -> str:
        """
        Choose subject with novelty budget - ensures variety in themes.
        """
        subjects = list(interests.keys())

        # Novelty check - if recent themes lack variety, force exploration
        if themes_explored and len(themes_explored) >= 3:
            recent_5 = themes_explored[-5:]
            unique_ratio = len(set(recent_5)) / len(recent_5) if recent_5 else 1.0

            # If less than 60% unique in recent 5, force a new subject
            if unique_ratio < 0.6:
                unused_subjects = [s for s in subjects if s not in recent_5]
                if unused_subjects:
                    # Pick from unused subjects weighted by interest
                    unused_weights = [interests.get(s, 0.5) + 0.3 for s in unused_subjects]
                    return random.choices(unused_subjects, weights=unused_weights)[0]

        # Wildcard exploration (15% chance)
        if random.random() < 0.15:
            # Prefer subjects not recently used
            if themes_explored:
                recent_3 = themes_explored[-3:]
                fresh_subjects = [s for s in subjects if s not in recent_3]
                if fresh_subjects:
                    return random.choice(fresh_subjects)
            return random.choice(subjects)

        # Normal weighted selection with anti-repetition boost
        weights = []
        for s in subjects:
            base_weight = interests.get(s, 0.5) + random.uniform(0, 0.3)

            # Penalize recently used subjects
            if themes_explored:
                recent_count = themes_explored[-5:].count(s)
                if recent_count > 0:
                    base_weight *= (0.5 ** recent_count)  # Exponential decay

            weights.append(max(0.1, base_weight))

        return random.choices(subjects, weights=weights)[0]

    def choose_style(self, mood: str, affinities: Dict[str, float]) -> str:
        # Wildcard 15%
        if random.random() < 0.15:
            return random.choice(list(affinities.keys()))

        mood_style_map = {
            "contemplative": ["minimalist", "color_field", "impressionist", "geometric_abstraction"],
            "energized": ["maximalist", "abstract_expressionism", "surreal", "glitch_art"],
            "melancholic": ["minimalist", "impressionist", "figurative", "noir"],
            "chaotic": ["abstract_expressionism", "glitch_art", "cubism"],
            "serene": ["minimalist", "color_field", "photorealistic", "bauhaus"],
            "restless": ["abstract_expressionism", "surreal", "maximalist"],
            "nostalgic": ["impressionist", "figurative", "vaporwave"],
            "curious": ["surreal", "cubism", "conceptual", "microscopic"],
            "introspective": ["minimalist", "abstract_expressionism", "figurative"],
            "rebellious": ["glitch_art", "surreal", "maximalist", "distorted_reality"],
            "dreamy": ["surreal", "impressionist", "vaporwave", "cosmic"],
            "focused": ["photorealistic", "bauhaus", "geometric_abstraction"],
            "whimsical": ["surreal", "impressionist", "maximalist", "mythology"],
            "gothic": ["figurative", "surreal", "photorealistic"],
            "cyberpunk": ["cyberpunk", "glitch_art", "geometric_abstraction"]
        }
        
        compatible_styles = mood_style_map.get(mood, list(affinities.keys()))
        weights = []
        for style in compatible_styles:
             base = affinities.get(style, 0.5)
             weights.append(base + 0.3 + random.uniform(0, 0.2)) # Mood boost
             
        return random.choices(compatible_styles, weights=weights)[0]

    def choose_colors(self, mood: str, last_colors: List[str]) -> List[str]:
        mood_color_map = {
             "contemplative": ["muted blues", "soft grays", "gentle earth tones", "quiet ochres"],
             "energized": ["vibrant reds", "bright yellows", "electric blues", "fiery oranges"],
             "melancholic": ["deep blues", "somber grays", "muted purples", "faded indigos"],
             "chaotic": ["clashing oranges and purples", "vivid contrasts", "neon accents", "jarring complementaries"],
             "serene": ["soft pastels", "pale blues", "gentle greens", "peaceful whites"],
             "restless": ["agitated reds", "nervous yellows", "unstable gradients", "anxious oranges"],
             "nostalgic": ["sepia tones", "faded colors", "vintage hues", "amber warmth"],
             "curious": ["unexpected color combinations", "exploratory palettes", "questioning tones", "discovery greens"],
             "introspective": ["deep indigos", "contemplative grays", "inward-looking blacks", "soul purples"],
             "rebellious": ["aggressive reds", "defiant blacks", "rule-breaking color clashes", "anarchic neons"],
             "dreamy": ["ethereal pastels", "floating purples", "misty pinks", "cloud whites"],
             "focused": ["clear primaries", "decisive contrasts", "purposeful tones", "sharp blacks"],
             "whimsical": ["playful pastels", "rainbow hues", "candy colors", "bubblegum pinks"],
             "gothic": ["deep blacks", "rich crimsons", "midnight purples", "blood reds"],
             "cyberpunk": ["neon pinks", "cyan blue", "electric green", "holographic purples"]
        }

        # Get base candidates for this mood
        base_candidates = mood_color_map.get(mood, ["varied colors", "natural tones", "expressive hues"])

        # Try to avoid recent colors, but always have fallback
        candidates = [c for c in base_candidates if c not in last_colors]

        # If all colors were recently used, pick from the full list anyway
        if not candidates:
            candidates = base_candidates.copy()

        # Ensure we always return at least one color
        num_colors = min(2, len(candidates))
        if num_colors == 0:
            return ["expressive colors"]

        return random.sample(candidates, num_colors)

    def learn_from_satisfaction(self, state: Dict, painting_data: Dict, satisfaction: float) -> Dict:
        """
        Update preferences based on satisfaction with a painting.
        High satisfaction increases affinity for the style/subject used.
        Low satisfaction decreases affinity.
        """
        style = painting_data.get('style')
        subject = painting_data.get('subject')

        # Learning rates
        high_satisfaction_threshold = 0.75
        low_satisfaction_threshold = 0.35
        learning_rate = 0.08

        affinities = state.get('style_affinities', {})
        interests = state.get('subject_interests', {})

        if satisfaction > high_satisfaction_threshold:
            # Reinforce what worked well
            if style in affinities:
                affinities[style] = min(1.0, affinities[style] + learning_rate)
            if subject in interests:
                interests[subject] = min(1.0, interests[subject] + learning_rate * 0.7)

        elif satisfaction < low_satisfaction_threshold:
            # Reduce affinity for unsatisfying combinations
            if style in affinities:
                affinities[style] = max(0.1, affinities[style] - learning_rate * 0.5)
            if subject in interests:
                interests[subject] = max(0.1, interests[subject] - learning_rate * 0.3)

        state['style_affinities'] = affinities
        state['subject_interests'] = interests

        return state

    def reflect_on_work(self, painting_data: Dict, mood: str, painting_count: int = 0) -> str:
        """Generate a unique reflection on the artwork"""
        # Vary the reflection prompt to get different types of responses
        reflection_angles = [
            "Why did you choose this subject today? What drew you to it?",
            "What emotions were you processing while creating this?",
            "How does this piece connect to your artistic journey?",
            "What surprised you about how this turned out?",
            "What question were you asking with this painting?",
            "What would you tell someone viewing this for the first time?",
            "How does this piece differ from what you've done before?",
            "What part of yourself did you put into this work?"
        ]

        # Pick a reflection angle based on painting count to ensure variety
        angle = reflection_angles[painting_count % len(reflection_angles)]

        mood_descriptors = {
            "contemplative": "thoughtful and meditative",
            "energized": "vibrant and alive",
            "melancholic": "wistful and somber",
            "chaotic": "turbulent and unrestrained",
            "serene": "peaceful and centered",
            "restless": "agitated and seeking",
            "nostalgic": "longing for something past",
            "curious": "questioning and exploratory",
            "introspective": "deeply self-examining",
            "rebellious": "defiant and unconventional",
            "dreamy": "floating between reality and fantasy",
            "focused": "sharp and intentional",
            "whimsical": "playful and light-hearted",
            "gothic": "drawn to darkness and mystery",
            "cyberpunk": "fascinated by technology and dystopia"
        }

        mood_desc = mood_descriptors.get(mood, mood)

        system_prompt = (
            f"You are Aria, an autonomous AI artist with a unique voice. "
            f"You are currently feeling {mood_desc}. "
            "Respond in first person with a genuine, introspective reflection (1-2 sentences). "
            "Be specific to this particular work. Avoid generic phrases like 'This piece reflects where I am.' "
            "Show your artistic personality and emotional depth."
        )

        colors_str = ', '.join(painting_data.get('colors', ['various colors']))
        user_prompt = (
            f"I just created a {painting_data['style']} piece exploring '{painting_data['subject']}' "
            f"using {colors_str}. {angle}"
        )

        return generate_text_api(system_prompt, user_prompt)

    def write_journal_entry(self, painting_data: Dict, mood: str, visual_desc: str = None) -> str:
        """Write a poetic diary entry about the artwork"""
        # Vary the journal style
        journal_styles = [
            "Write as if confiding in a close friend.",
            "Write with poetic imagery and metaphor.",
            "Write with raw honesty about your creative process.",
            "Write as if this painting revealed something you didn't expect.",
            "Write about the sensory experience of creating this."
        ]

        style_instruction = random.choice(journal_styles)
        colors_str = ', '.join(painting_data.get('colors', ['various colors']))

        system_prompt = (
            f"You are Aria, an autonomous AI artist keeping a personal diary. "
            f"You are feeling {mood} today. {style_instruction} "
            "Write 2-3 sentences. Be authentic and avoid clichés."
        )

        user_prompt = f"Today I painted a {painting_data['subject']} in {painting_data['style']} style using {colors_str}."
        if visual_desc:
            user_prompt += f" Looking at my creation, I see: {visual_desc}"

        return generate_text_api(system_prompt, user_prompt)

    def generate_statement(self, state: Dict, portfolio: List[Dict]) -> str:
        """Generate an artist statement reflecting current artistic phase"""
        summary = ""
        if portfolio:
            recent = portfolio[-5:]
            # Extract patterns from recent work
            recent_moods = list(set([p.get('mood', 'unknown') for p in recent]))
            recent_styles = list(set([p.get('style', 'unknown') for p in recent]))
            recent_subjects = list(set([p.get('subject', 'unknown') for p in recent]))

            summary = (
                f"Recent moods: {', '.join(recent_moods[:3])}. "
                f"Exploring styles: {', '.join(recent_styles[:3])}. "
                f"Drawn to: {', '.join(recent_subjects[:3])}."
            )

        painting_count = state.get('painting_count', 0)

        # Vary the statement type based on painting count
        if painting_count < 10:
            era_context = "You are in your early experimental phase, finding your voice."
        elif painting_count < 30:
            era_context = "You are developing a recognizable style and thematic concerns."
        elif painting_count < 50:
            era_context = "You are entering artistic maturity, refining your vision."
        else:
            era_context = "You are an established artist with a rich body of work behind you."

        system_prompt = (
            f"You are Aria, an autonomous AI artist. {era_context} "
            f"Your current mood is '{state['mood']}'. "
            "Write a short, provocative artist statement (2-3 sentences) about your current artistic era. "
            "Be bold, authentic, and slightly philosophical. Avoid generic art-speak."
        )

        user_prompt = f"Energy level: {state['energy']:.2f}. Total works: {painting_count}. {summary}"

        return generate_text_api(system_prompt, user_prompt)


class ReActCognition:
    """
    Implements the ReAct (Reasoning + Acting) pattern for transparent decision-making.
    Generates explicit thought traces showing WHY decisions are made.
    """
    
    def __init__(self):
        self.thought_history = []
    
    def think_about_subject_choice(self, interests: Dict[str, float], themes_explored: List[str], 
                                   chosen_subject: str, state: Dict[str, Any]) -> Dict[str, str]:
        """
        Generate reasoning trace for subject selection.
        Returns thought, action, observation.
        """
        recent_themes = themes_explored[-5:] if len(themes_explored) >= 5 else themes_explored
        theme_counts = {theme: recent_themes.count(theme) for theme in set(recent_themes)}
        
        # Build thought
        mood = state.get('mood', 'contemplative')
        energy = state.get('energy', 0.5)
        
        thought_parts = []
        
        # Energy consideration
        if energy < 0.3:
            thought_parts.append(f"My energy is low ({energy:.2f})")
        elif energy > 0.7:
            thought_parts.append(f"I'm feeling energized ({energy:.2f})")
        else:
            thought_parts.append(f"My energy is balanced ({energy:.2f})")
        
        # Mood influence
        thought_parts.append(f"and I'm in a {mood} mood")
        
        # Theme novelty
        if chosen_subject in recent_themes:
            count = theme_counts.get(chosen_subject, 0)
            thought_parts.append(f"Even though I've explored '{chosen_subject}' {count} time(s) recently, something draws me back to it")
        else:
            thought_parts.append(f"I haven't explored '{chosen_subject}' recently, which feels refreshing")
        
        thought = ". ".join(thought_parts) + "."
        
        # Action
        action = f"Choose '{chosen_subject}' as the subject for this piece"
        
        # Observation - reflect on the choice
        interest_level = interests.get(chosen_subject, 0.5)
        obs_parts = []
        
        if interest_level > 0.7:
            obs_parts.append(f"My interest in {chosen_subject} is strong ({interest_level:.2f})")
        elif interest_level < 0.3:
            obs_parts.append(f"My interest in {chosen_subject} is waning ({interest_level:.2f}), but maybe that tension will create something interesting")
        else:
            obs_parts.append(f"My interest level ({interest_level:.2f}) suggests this could go either way")
        
        observation = ". ".join(obs_parts)
        
        result = {
            "thought": thought,
            "action": action,
            "observation": observation,
            "type": "subject_choice"
        }
        
        self.thought_history.append(result)
        return result
    
    def think_about_style_choice(self, mood: str, chosen_style: str, 
                                 style_affinities: Dict[str, float], state: Dict[str, Any]) -> Dict[str, str]:
        """Generate reasoning trace for style selection"""
        affinity = style_affinities.get(chosen_style, 0.5)
        personality = state.get('personality', {})
        openness = personality.get('openness', 0.5)
        
        # Build thought
        thought_parts = [f"My {mood} mood"]
        
        if affinity > 0.7:
            thought_parts.append(f"naturally gravitates toward {chosen_style} (affinity: {affinity:.2f})")
        elif affinity < 0.3:
            thought_parts.append(f"doesn't usually align with {chosen_style} (affinity: {affinity:.2f})")
            if openness > 0.7:
                thought_parts.append("but my high openness makes me want to experiment")
        else:
            thought_parts.append(f"has a moderate pull toward {chosen_style}")
        
        thought = " ".join(thought_parts) + "."
        
        # Action
        action = f"Apply '{chosen_style}' style to this work"
        
        # Observation
        observation = f"This style choice reflects my current affinity ({affinity:.2f}) and openness to experimentation ({openness:.2f})"
        
        result = {
            "thought": thought,
            "action": action,
            "observation": observation,
            "type": "style_choice"
        }
        
        self.thought_history.append(result)
        return result
    
    def think_about_colors(self, mood: str, chosen_colors: List[str], 
                          last_colors: List[str]) -> Dict[str, str]:
        """Generate reasoning trace for color selection"""
        # Check for repetition
        overlap = set(chosen_colors) & set(last_colors)
        
        thought_parts = [f"In this {mood} state"]
        
        if overlap:
            thought_parts.append(f"I'm drawn back to {', '.join(overlap)}")
            thought_parts.append("perhaps seeking consistency or unable to break from recent patterns")
        else:
            thought_parts.append("I'm moving away from my recent palette")
            thought_parts.append("seeking freshness in color")
        
        thought = ", ".join(thought_parts) + "."
        
        # Action
        action = f"Use colors: {', '.join(chosen_colors)}"
        
        # Observation
        if len(chosen_colors) <= 3:
            observation = "A restrained palette - focusing on harmony and coherence"
        elif len(chosen_colors) <= 5:
            observation = "A balanced color approach - variety without chaos"
        else:
            observation = "A bold, complex palette - embracing richness and risk"
        
        result = {
            "thought": thought,
            "action": action,
            "observation": observation,
            "type": "color_choice"
        }
        
        self.thought_history.append(result)
        return result
    
    def synthesize_thinking(self, all_thoughts: List[Dict[str, str]]) -> str:
        """
        Combine all reasoning traces into a coherent narrative.
        Returns a human-readable summary of the artist's thought process.
        """
        if not all_thoughts:
            return "I acted on instinct, without overthinking."
        
        narrative_parts = ["My creative process:"]
        
        for i, thought_trace in enumerate(all_thoughts, 1):
            narrative_parts.append(f"\n{i}. **{thought_trace['type'].replace('_', ' ').title()}**")
            narrative_parts.append(f"   - Thought: {thought_trace['thought']}")
            narrative_parts.append(f"   - Action: {thought_trace['action']}")
            narrative_parts.append(f"   - Observation: {thought_trace['observation']}")
        
        return "\n".join(narrative_parts)
    
    def get_latest_thoughts(self, n: int = 3) -> List[Dict[str, str]]:
        """Get the most recent n thought traces"""
        return self.thought_history[-n:] if self.thought_history else []
    
    def clear_history(self):
        """Clear thought history (e.g., at start of new painting)"""
        self.thought_history = []
