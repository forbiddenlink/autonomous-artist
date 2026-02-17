import random
import logging
from typing import Dict, Optional, Any, Tuple
from artist_modules.memory import ArtistMemory
from artist_modules.brain import ArtistBrain, ReActCognition
from artist_modules.painter import ArtistPainter
from artist_modules.critic import ArtistCritic

logger = logging.getLogger("autonomous_artist")


class AutonomousArtist:
    """
    The central coordinator / agent shell.
    Delegates cognition to Brain, craft to Painter, and storage to Memory.
    """
    
    def __init__(
        self,
        name: str = "Aria",
        memory_file: str = "artist_memory.json"
    ):
        self.name = name
        
        # Initialize Modules
        self.memory = ArtistMemory(memory_file)
        self.brain = ArtistBrain()
        self.painter = ArtistPainter()
        self.cognition = ReActCognition()  # ReAct thinking module
        self.critic = ArtistCritic()  # Critique agent
        
        # Load or Initialize State
        loaded_state = self.memory.load()
        
        # Initialize defaults
        default_state = self._get_default_state()
        
        # Merge: Loaded overrides defaults
        self.state = {**default_state, **loaded_state}
            
    def _get_default_state(self) -> Dict[str, Any]:
        """Generate fresh default state"""
        return {
            "mood": random.choice(self.brain.MOODS),
            "energy": random.uniform(0.3, 1.0),
            "complexity_tolerance": random.uniform(0.2, 0.8),
            "painting_count": 0,
            "portfolio": [],
            "themes_explored": [],
            "last_colors_used": [],
            "mood_history": [],

            # Big Five Personality Traits (OCEAN)
            # stable characteristics
            # These evolve slowly and influence artistic decisions
            "personality": {
                # Creativity, curiosity, experimentation
                "openness": random.uniform(0.5, 0.9),
                # Detail orientation, planning
                "conscientiousness": random.uniform(0.3, 0.7),
                # Bold vs subtle expression
                "extraversion": random.uniform(0.3, 0.8),
                # Conventional vs provocative
                "agreeableness": random.uniform(0.2, 0.6),
                # Emotional volatility
                "neuroticism": random.uniform(0.3, 0.7)
            },

            # Preferences
            "style_affinities": {
                k: random.uniform(0.2, 0.8)
                for k in self.painter.STYLE_DESCRIPTORS.keys()
            },
            "subject_interests": {
                k: random.uniform(0.2, 0.8)
                for k in self.painter.SUBJECT_DESCRIPTORS.keys()
            }
        }
    
    # --- Properties for Backward Compatibility with app.py ---
    @property
    def portfolio(self):
        return self.state.get('portfolio', [])
    
    @property
    def painting_count(self):
        return self.state.get('painting_count', 0)
        
    @property
    def mood(self):
        return self.state.get('mood', 'contemplative')

    # --- Core Actions ---

    def evolve_state(self):
        """Trigger cognitive evolution cycle"""
        self.state = self.brain.evolve_state(self.state)
        # We don't save immediately here usually, but we could.
        # Typically saved after painting.
        
    def generate_prompt(self) -> Dict[str, Any]:
        """Orchestrate the creation of a new painting concept with explicit reasoning"""
        try:
            # Clear previous thinking
            self.cognition.clear_history()
            
            # 1. Brain decides *what* to paint (with novelty budget)
            subject = self.brain.choose_subject(
                self.state['subject_interests'],
                themes_explored=self.state.get('themes_explored', [])
            )
            
            # Generate thinking trace for subject choice
            subject_thinking = self.cognition.think_about_subject_choice(
                self.state['subject_interests'],
                self.state.get('themes_explored', []),
                subject,
                self.state
            )
            
            style = self.brain.choose_style(self.state['mood'], self.state['style_affinities'])
            
            # Generate thinking trace for style choice
            style_thinking = self.cognition.think_about_style_choice(
                self.state['mood'],
                style,
                self.state['style_affinities'],
                self.state
            )
            
            colors = self.brain.choose_colors(self.state['mood'], self.state.get('last_colors_used', []))
            
            # Generate thinking trace for color choice
            color_thinking = self.cognition.think_about_colors(
                self.state['mood'],
                colors,
                self.state.get('last_colors_used', [])
            )
            
            # 2. Painter crafts the *how* (the prompts)
            painting_data = self.painter.assemble_prompt(
                subject=subject,
                style=style,
                colors=colors,
                mood=self.state['mood'],
                energy=self.state['energy'],
                complexity=self.state.get('complexity_tolerance', 0.5),
                personality=self.state.get('personality')
            )
            
            # 3. Attach thinking traces
            painting_data['thinking'] = {
                'subject': subject_thinking,
                'style': style_thinking,
                'colors': color_thinking,
                'narrative': self.cognition.synthesize_thinking([
                    subject_thinking, style_thinking, color_thinking
                ])
            }
            
            return painting_data
        except Exception as e:
            logger.error(f"Error generating prompt: {e}")
            # Return a safe fallback prompt
            return {
                "prompt": "abstract art, expressive colors, emotional depth",
                "subject": "emotions",
                "style": "abstract_expressionism",
                "colors": ["expressive colors"],
                "mood": self.state.get('mood', 'contemplative'),
                "energy": self.state.get('energy', 0.5)
            }
    
    def record_painting(self, painting_data: Dict[str, Any], image_url: str, visual_description: Optional[str] = None) -> Dict[str, Any]:
        """Commit the work to memory after reflection"""
        from datetime import datetime

        # Get current painting count for reflection variety
        current_count = self.state.get('painting_count', 0)

        # 1. Brain reflects on the work (with painting count for variety)
        reflection = self.brain.reflect_on_work(painting_data, self.state['mood'], current_count)

        # 2. Adjust satisfaction based on visual confirmation (if available)
        satisfaction = random.uniform(0.4, 0.9)
        if visual_description:
            # Simple check for subject/style match
            matches = 0
            if painting_data['subject'].lower() in visual_description.lower():
                matches += 1
            if painting_data['style'].lower() in visual_description.lower():
                matches += 1
            # Check for color keywords
            for color in painting_data.get('colors', []):
                if any(c in visual_description.lower() for c in color.lower().split()):
                    matches += 0.5

            if matches >= 1.5:
                satisfaction = min(1.0, satisfaction + 0.15)
            elif matches > 0:
                satisfaction = min(1.0, satisfaction + 0.1)
            else:
                satisfaction = max(0.1, satisfaction - 0.15)

        # 3. Brain learns from satisfaction (preference adjustment)
        self.state = self.brain.learn_from_satisfaction(self.state, painting_data, satisfaction)

        # 4. Brain writes journal
        journal = self.brain.write_journal_entry(painting_data, self.state['mood'], visual_description)

        # 5. Update colors used
        last_colors = self.state.get('last_colors_used', [])
        last_colors.extend(painting_data.get('colors', []))
        self.state['last_colors_used'] = last_colors[-20:]  # Keep last 20

        # 6. Construct Record
        self.state['painting_count'] = current_count + 1

        record = {
            "number": self.state['painting_count'],
            "timestamp": datetime.now().isoformat(),
            **painting_data,
            "satisfaction": round(satisfaction, 3),
            "image_url": image_url,
            "visual_description": visual_description,
            "reflection": reflection,
            "journal": journal
        }

        # 7. Save to Memory
        self.memory.add_painting(record, self.state)

        # 8. Evolve state
        self.evolve_state()
        self.memory.save(self.state)

        return record

    def get_current_state(self) -> Dict:
        """Return public state view"""
        # Similar logic to original, but pulling from state dict
        # Sort interests/affinities for display
        
        sorted_interests = dict(sorted(
            self.state['subject_interests'].items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:3])
        
        sorted_affinities = dict(sorted(
            self.state['style_affinities'].items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:3])
        
        return {
            "name": self.name,
            "mood": self.state['mood'],
            "energy": round(self.state['energy'], 2),
            "complexity_tolerance": round(self.state.get('complexity_tolerance', 0.5), 2),
            "paintings_created": self.state.get('painting_count', 0),
            "current_interests": {k: round(v, 2) for k,v in sorted_interests.items()},
            "style_affinities": {k: round(v, 2) for k,v in sorted_affinities.items()}
        }

    def get_artist_statement(self) -> str:
        return self.brain.generate_statement(self.state, self.state.get('portfolio', []))
    
    def create_with_critique(self, max_iterations: int = 2) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
        """
        Generate painting concept with critic feedback loop.
        Returns (final_concept, critique_history)
        """
        critique_history = []
        concept = None
        
        for iteration in range(max_iterations):
            # Generate concept
            concept = self.generate_prompt()
            
            # Get critique
            critique = self.critic.critique_concept(concept, self.state)
            critique_history.append(critique)
            
            # Artist's response to critique (personality-based)
            artist_response = self._respond_to_critique(critique, iteration)
            critique['artist_response'] = artist_response
            
            # If approved or artist rebels, accept the concept
            if critique['approved'] or artist_response['rebels']:
                break
            
            # Otherwise, on last iteration, accept anyway
            if iteration == max_iterations - 1:
                critique_history.append({
                    'critic_name': 'Artist Decision',
                    'critique': 'Enough deliberation. I\'m going with my instinct.',
                    'approved': True,
                    'artist_overrides': True
                })
        
        return concept, critique_history
    
    def _respond_to_critique(self, critique: Dict[str, Any], iteration: int) -> Dict[str, Any]:
        """
        Artist's internal response to critique based on personality and mood.
        Returns dict with 'accepts', 'rebels', and 'reasoning'
        """
        personality = self.state.get('personality', {})
        mood = self.state.get('mood', 'contemplative')
        
        # Factors influencing response
        openness = personality.get('openness', 0.5)
        neuroticism = personality.get('neuroticism', 0.5)
        agreeableness = personality.get('agreeableness', 0.5)
        
        # Rebellious moods are less likely to accept critique
        rebellious_moods = ['rebellious', 'chaotic', 'restless']
        is_rebellious_mood = mood in rebellious_moods
        
        # Calculate acceptance probability
        base_acceptance = 0.7
        
        # High openness = more receptive to feedback
        acceptance_prob = base_acceptance + (openness * 0.2)
        
        # Low agreeableness = more likely to push back
        acceptance_prob -= (1 - agreeableness) * 0.3
        
        # Rebellious moods reduce acceptance
        if is_rebellious_mood:
            acceptance_prob -= 0.3
        
        # First iteration: more willing to listen
        if iteration == 0:
            acceptance_prob += 0.2
        
        # If critique confidence is low, artist is less swayed
        confidence = critique.get('confidence', 0.5)
        acceptance_prob *= confidence
        
        # Decision
        accepts = random.random() < acceptance_prob
        rebels = not accepts and (is_rebellious_mood or agreeableness < 0.3)
        
        # Reasoning
        if accepts:
            reasoning = "The critique has merit. I'll consider another approach."
        elif rebels:
            if is_rebellious_mood:
                reasoning = f"My {mood} mood won't be constrained. I'm following my instinct."
            else:
                reasoning = "I appreciate the feedback, but I trust my vision on this."
        else:
            reasoning = "I'm not fully convinced, but let me think about it..."
        
        return {
            'accepts': accepts,
            'rebels': rebels,
            'reasoning': reasoning,
            'mood': mood,
            'openness': openness,
            'agreeableness': agreeableness
        }
