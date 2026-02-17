import random
from typing import List, Dict

class ArtistPainter:
    """
    Responsible for the 'craft' of painting:
    - Translating abstract decisions (style, subject) into concrete prompts
    - Applying technique (descriptors, modifiers)
    - Adding compositional elements and quality modifiers
    """

    def __init__(self):
        # Compositional approaches
        self.COMPOSITIONS = {
            "dynamic": "dynamic diagonal composition with movement",
            "centered": "centered symmetrical composition",
            "rule_of_thirds": "composed following rule of thirds",
            "golden_ratio": "golden ratio spiral composition",
            "asymmetric": "deliberately asymmetric balance",
            "layered": "layered depth with foreground and background",
            "minimalist_comp": "sparse minimalist composition with negative space",
            "dense": "densely packed frame filling composition"
        }

        # Negative prompts for quality
        self.NEGATIVE_PROMPT = (
            "blurry, low quality, watermark, signature, text, deformed, "
            "ugly, bad anatomy, bad proportions, duplicate, cropped, "
            "out of frame, amateur, poorly drawn"
        )

        self.STYLE_DESCRIPTORS = {
            # Classic
            "impressionist": "impressionist painting with loose brushstrokes and light",
            "photorealistic": "hyper-realistic high-resolution photography",
            "figurative": "figurative art with clear human subjects",
            "still_life": "classic still life arrangement",
            
            # Abstract & Modern
            "abstract_expressionism": "chaotic abstract expressionist painting with splatters and bold strokes",
            "cubism": "avant-garde cubist fragmentation",
            "color_field": "large fields of flat, solid color",
            "geometric_abstraction": "precise geometric abstraction with sharp lines",
            "minimalist": "ultra-minimalist design with plenty of negative space",
            "maximalist": "intricate maximalist art filled with obsessive detail",
            
            # Surreal/Digital
            "surreal": "surreal dreamscape defying physics",
            "cyberpunk": "gritty high-tech cyberpunk aesthetic",
            "vaporwave": "retro-aesthetic vaporwave style with neon and statuary",
            "glitch_art": "digital glitch art with databending effects",
            "bauhaus": "functional bauhaus style with clean geometric forms"
        }

        self.SUBJECT_DESCRIPTORS = {
            # Physical
            "nature": "featuring natural landscapes, forests, or organic forms",
            "urban": "depicting dense city scenes and street life",
            "portraits": "intimate portraiture",
            "architecture": "modernist or brutalist architecture",
            "landscapes": "sweeping vistas and horizons",
            
            # Conceptual
            "emotions": "visualizing raw human emotion",
            "time": "symbolic representation of the passage of time",
            "chaos": "visualizing entropy and disorder",
            "silence": "depicting quietude and absence of sound",
            "memories": "hazy, fragmented memory visualization",
            
            # Sci-fi
            "cosmic": "nebulae, galaxies, and cosmic wonders",
            "microscopic": "magnified microscopic world",
            "mythology": "reinterpretation of ancient myth",
            "distorted_reality": "warped reality and bending physics"
        }

        self.MOOD_DESCRIPTORS = {
            "contemplative": "evoking quiet contemplation",
            "energized": "bursting with dynamic energy",
            "melancholic": "tinged with melancholy",
            "chaotic": "embracing visual chaos",
            "serene": "radiating serenity",
            "restless": "expressing restless tension",
            "nostalgic": "infused with nostalgia",
            "curious": "inviting curiosity",
            "introspective": "turning inward",
            "rebellious": "challenging conventions",
            "dreamy": "floating in dreamlike space",
            "focused": "with precise intention",
            "whimsical": "filled with wonder and playfulness",
            "gothic": "with a dark, mysterious atmosphere",
            "cyberpunk": "in a futuristic high-tech dystopian style"
        }

    def assemble_prompt(self, subject: str, style: str, colors: List[str], mood: str, energy: float, complexity: float, personality: Dict = None) -> Dict[str, any]:
        """Using the provided parameters, construct the full generative prompt"""

        prompt_parts = []

        # 1. Style
        prompt_parts.append(self.STYLE_DESCRIPTORS.get(style, style))

        # 2. Subject
        prompt_parts.append(self.SUBJECT_DESCRIPTORS.get(subject, subject))

        # 3. Colors (ensure we have colors)
        if colors:
            prompt_parts.append(f"using a palette of {', '.join(colors)}")
        else:
            prompt_parts.append("using expressive colors")

        # 4. Mood
        mood_desc = self.MOOD_DESCRIPTORS.get(mood, "")
        if mood_desc:
            prompt_parts.append(mood_desc)

        # 5. Composition (selected based on mood and personality)
        composition = self._select_composition(mood, energy, personality)
        if composition:
            prompt_parts.append(composition)

        # 6. Energy technique modifiers
        if energy > 0.75:
            prompt_parts.append("rendered with bold energetic brushwork and dynamic movement")
        elif energy > 0.5:
            prompt_parts.append("rendered with confident detail")
        elif energy < 0.35:
            prompt_parts.append("created with contemplative deliberate simplicity")

        # 7. Complexity (influenced by conscientiousness if available)
        effective_complexity = complexity
        if personality:
            # High conscientiousness increases detail attention
            effective_complexity = complexity * (0.7 + personality.get('conscientiousness', 0.5) * 0.6)

        if effective_complexity > 0.65:
            prompt_parts.append("with intricate layered complexity")
        elif effective_complexity > 0.45:
            prompt_parts.append("with thoughtful compositional depth")

        # 8. Personality-influenced modifiers
        if personality:
            # High extraversion = bolder
            if personality.get('extraversion', 0.5) > 0.7:
                prompt_parts.append("bold and attention-commanding")
            # Low agreeableness = more provocative
            if personality.get('agreeableness', 0.5) < 0.3:
                prompt_parts.append("unconventional and thought-provoking")
            # High openness = experimental
            if personality.get('openness', 0.5) > 0.8:
                prompt_parts.append("experimental and boundary-pushing")

        # Build final prompt
        full_text = ", ".join([p for p in prompt_parts if p])
        full_text += ", professional photography, 8k uhd, high quality, masterpiece"

        return {
            "prompt": full_text,
            "negative_prompt": self.NEGATIVE_PROMPT,
            "subject": subject,
            "style": style,
            "colors": colors,
            "mood": mood,
            "energy": energy,
            "composition": composition
        }

    def _select_composition(self, mood: str, energy: float, personality: Dict = None) -> str:
        """Select an appropriate composition style based on mood and energy"""
        # Mood-composition mappings
        mood_compositions = {
            "chaotic": ["dynamic", "asymmetric", "dense"],
            "serene": ["centered", "golden_ratio", "minimalist_comp"],
            "contemplative": ["rule_of_thirds", "layered", "centered"],
            "energized": ["dynamic", "asymmetric", "dense"],
            "melancholic": ["rule_of_thirds", "layered", "minimalist_comp"],
            "restless": ["dynamic", "asymmetric", "dense"],
            "dreamy": ["golden_ratio", "layered", "minimalist_comp"],
            "focused": ["centered", "rule_of_thirds", "golden_ratio"],
            "rebellious": ["asymmetric", "dynamic", "dense"],
            "whimsical": ["asymmetric", "dynamic", "layered"],
            "gothic": ["centered", "layered", "asymmetric"],
            "cyberpunk": ["dynamic", "dense", "layered"],
            "nostalgic": ["golden_ratio", "rule_of_thirds", "centered"],
            "curious": ["layered", "dynamic", "rule_of_thirds"],
            "introspective": ["centered", "minimalist_comp", "rule_of_thirds"]
        }

        # Get candidates for this mood
        candidates = mood_compositions.get(mood, list(self.COMPOSITIONS.keys()))

        # Energy influence
        if energy > 0.7:
            # Prefer dynamic compositions
            candidates = [c for c in candidates if c in ["dynamic", "asymmetric", "dense"]] or candidates
        elif energy < 0.4:
            # Prefer calmer compositions
            candidates = [c for c in candidates if c in ["centered", "golden_ratio", "minimalist_comp", "rule_of_thirds"]] or candidates

        # Select and return
        choice = random.choice(candidates)
        return self.COMPOSITIONS.get(choice, "")
