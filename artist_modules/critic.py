import random
from typing import Dict, Any, List
import logging

try:
    from utils import generate_text_api
except ImportError:
    from ..utils import generate_text_api

logger = logging.getLogger("autonomous_artist")

class ArtistCritic:
    """
    An AI agent that provides constructive critique of painting concepts.
    Acts as a collaborative partner, offering feedback that the artist
    may accept, ignore, or rebel against based on personality and mood.
    """
    
    def __init__(self, name: str = "The Critic"):
        self.name = name
        
        # Critique focus areas
        self.CRITIQUE_ASPECTS = [
            "composition",
            "color_harmony",
            "mood_alignment",
            "technical_execution",
            "conceptual_depth",
            "novelty"
        ]
        
        # Critic's personality traits (stable across critiques)
        self.personality = {
            "strictness": random.uniform(0.4, 0.7),  # How harsh vs encouraging
            "technical_focus": random.uniform(0.3, 0.8),  # Technical vs conceptual
            "risk_tolerance": random.uniform(0.4, 0.7)  # Conservative vs experimental
        }
    
    def critique_concept(self, painting_data: Dict[str, Any], artist_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze a painting concept and provide constructive feedback.
        
        Returns:
            Dict with critique, approval recommendation, and specific feedback points
        """
        try:
            # Analyze the concept
            analysis = self._analyze_concept(painting_data, artist_state)
            
            # Generate critique using LLM
            critique_text = self._generate_critique_text(painting_data, artist_state, analysis)
            
            # Decide whether to approve or suggest revision
            approval_decision = self._decide_approval(analysis, artist_state)
            
            return {
                "critic_name": self.name,
                "critique": critique_text,
                "approved": approval_decision["approved"],
                "confidence": approval_decision["confidence"],
                "suggestions": approval_decision.get("suggestions", []),
                "analysis": analysis
            }
        except Exception as e:
            logger.error(f"Error generating critique: {e}")
            # Fallback: always approve with generic encouragement
            return {
                "critic_name": self.name,
                "critique": "An intriguing concept. I trust your artistic vision.",
                "approved": True,
                "confidence": 0.5,
                "suggestions": [],
                "analysis": {}
            }
    
    def _analyze_concept(self, painting_data: Dict[str, Any], artist_state: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze various aspects of the painting concept"""
        analysis = {}
        
        # Composition check (stored for potential future use)
        _ = painting_data.get('composition', 'unknown')
        analysis['composition_score'] = random.uniform(0.5, 0.9)
        
        # Color harmony
        colors = painting_data.get('colors', [])
        analysis['color_harmony'] = self._assess_color_harmony(colors)
        
        # Mood alignment
        mood = painting_data.get('mood', 'contemplative')
        style = painting_data.get('style', 'abstract')
        analysis['mood_alignment'] = self._check_mood_style_fit(mood, style)
        
        # Novelty assessment
        recent_themes = artist_state.get('themes_explored', [])[-5:]
        current_subject = painting_data.get('subject', '')
        analysis['novelty_score'] = 0.8 if current_subject not in recent_themes else 0.3
        
        # Technical complexity
        complexity = painting_data.get('complexity', 0.5)
        energy = artist_state.get('energy', 0.5)
        analysis['technical_feasibility'] = 0.9 if complexity <= energy + 0.2 else 0.5
        
        # Overall quality estimate
        scores = [v for k, v in analysis.items() if isinstance(v, (int, float))]
        analysis['overall_score'] = sum(scores) / len(scores) if scores else 0.7
        
        return analysis
    
    def _assess_color_harmony(self, colors: List[str]) -> float:
        """Assess how well colors work together"""
        if not colors:
            return 0.7
        
        # Simple heuristic: fewer colors = more harmonious
        if len(colors) <= 3:
            return random.uniform(0.7, 0.9)
        elif len(colors) <= 5:
            return random.uniform(0.5, 0.8)
        else:
            return random.uniform(0.4, 0.7)
    
    def _check_mood_style_fit(self, mood: str, style: str) -> float:
        """Check if mood and style complement each other"""
        # Some combinations work particularly well
        strong_pairings = {
            "melancholic": ["gothic", "abstract_expressionism", "impressionist"],
            "energized": ["cyberpunk", "chaotic", "abstract_expressionism"],
            "serene": ["minimalist", "color_field", "impressionist"],
            "rebellious": ["cyberpunk", "abstract_expressionism", "surreal"],
            "dreamy": ["surreal", "impressionist", "vaporwave"]
        }
        
        if mood in strong_pairings and style in strong_pairings[mood]:
            return random.uniform(0.8, 1.0)
        return random.uniform(0.5, 0.8)
    
    def _generate_critique_text(self, painting_data: Dict[str, Any], artist_state: Dict[str, Any], analysis: Dict[str, Any]) -> str:
        """Generate detailed critique using LLM"""
        # Build context for the critic
        prompt = f"""You are an art critic providing constructive feedback on a painting concept.

Artist's Current State:
- Mood: {artist_state.get('mood', 'unknown')}
- Energy: {artist_state.get('energy', 0.5):.2f}
- Recent themes explored: {', '.join(artist_state.get('themes_explored', [])[-3:])}

Painting Concept:
- Subject: {painting_data.get('subject', 'unknown')}
- Style: {painting_data.get('style', 'unknown')}
- Colors: {', '.join(painting_data.get('colors', []))}
- Mood: {painting_data.get('mood', 'unknown')}
- Composition: {painting_data.get('composition', 'unknown')}
- Prompt: {painting_data.get('prompt', '')}

Analysis Scores:
- Overall quality: {analysis.get('overall_score', 0.7):.2f}
- Novelty: {analysis.get('novelty_score', 0.5):.2f}
- Mood alignment: {analysis.get('mood_alignment', 0.5):.2f}

Provide a brief (2-3 sentences) critique that is:
1. Constructive and specific
2. Acknowledges strengths
3. Suggests one area for consideration (if any)
4. Matches the artistic mood (be encouraging for low energy, more challenging for high energy)

Keep it conversational and respectful of the artist's vision."""

        system_prompt = "You are an insightful art critic providing constructive feedback."
        critique = generate_text_api(system_prompt, prompt)
        
        if not critique or len(critique) < 20:
            # Fallback critiques based on analysis
            if analysis.get('overall_score', 0) > 0.75:
                return "This is a strong concept. The composition and color choices show maturity. I'm curious to see how it develops."
            elif analysis.get('novelty_score', 0) < 0.4:
                return "A solid approach, though you've explored similar territory recently. Perhaps push the boundaries a bit more?"
            else:
                return "An interesting direction. The mood and style pairing is unconventional, which could yield surprising results."
        
        return critique
    
    def _decide_approval(self, analysis: Dict[str, Any], artist_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Decide whether to approve the concept or suggest revision.
        Considers critic's personality and artist's state.
        """
        overall_score = analysis.get('overall_score', 0.7)
        
        # Adjust threshold based on critic's strictness
        approval_threshold = 0.5 + (self.personality['strictness'] * 0.2)
        
        # Consider artist's personality - rebel artists get more pushback
        artist_personality = artist_state.get('personality', {})
        if artist_personality.get('openness', 0.5) > 0.8:
            # Very open artists benefit from challenge
            approval_threshold += 0.1
        
        # Decision
        approved = overall_score >= approval_threshold
        
        # Confidence in the decision
        confidence = abs(overall_score - approval_threshold) + 0.5
        confidence = min(1.0, confidence)
        
        result = {
            "approved": approved,
            "confidence": confidence
        }
        
        # If not approved, provide specific suggestions
        if not approved:
            suggestions = []
            if analysis.get('color_harmony', 1.0) < 0.6:
                suggestions.append("Consider simplifying the color palette")
            if analysis.get('novelty_score', 1.0) < 0.4:
                suggestions.append("This theme has been explored recently - try a fresh angle")
            if analysis.get('technical_feasibility', 1.0) < 0.6:
                suggestions.append("The complexity might exceed current energy levels")
            
            result['suggestions'] = suggestions
        
        return result
    
    def get_personality_description(self) -> str:
        """Describe the critic's personality"""
        strictness = self.personality['strictness']
        tech_focus = self.personality['technical_focus']
        risk_tol = self.personality['risk_tolerance']
        
        style = "demanding" if strictness > 0.6 else "encouraging"
        focus = "technically-minded" if tech_focus > 0.6 else "conceptually-focused"
        risk = "experimental" if risk_tol > 0.6 else "traditional"
        
        return f"A {style}, {focus} critic with {risk} tendencies"
