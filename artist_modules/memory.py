import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any
import logging

try:
    from config import Config
except ImportError:
    # Fallback if config not available
    class Config:
        MAX_PORTFOLIO_SIZE = 50
        MAX_THEMES_TRACKED = 100
        MAX_COLORS_TRACKED = 20
        MAX_MOOD_HISTORY = 10

logger = logging.getLogger("autonomous_artist")

class ArtistMemory:
    """
    Handles the storage and retrieval of long-term artist memory (portfolio, state history).
    Future expansion: Vector store integration for Deep Memory (RAG).
    """

    def __init__(self, memory_file: str = "artist_memory.json"):
        self.memory_file = Path(memory_file)
    
    def load(self) -> Dict[str, Any]:
        """Load memory from disk or return empty state structure"""
        if self.memory_file.exists():
            try:
                with open(self.memory_file, 'r') as f:
                    data = json.load(f)
                logger.info(f"Memory loaded from {self.memory_file}")
                return data
            except json.JSONDecodeError as e:
                logger.error(f"Corrupt memory file {self.memory_file}: {e}. Starting fresh.")
                return {}
            except Exception as e:
                logger.error(f"Error loading memory: {e}. Starting fresh.")
                return {}
        return {}
    
    def save(self, current_state: Dict[str, Any]) -> None:
        """Persist current state to disk with size limits"""
        try:
            # Ensure we don't save ephemeral objects, only the data structure
            # Apply size limits from config to prevent unbounded growth
            data = {
                'portfolio': current_state.get('portfolio', [])[-Config.MAX_PORTFOLIO_SIZE:],
                'painting_count': current_state.get('painting_count', 0),
                'themes_explored': current_state.get('themes_explored', [])[-Config.MAX_THEMES_TRACKED:],
                'last_colors_used': current_state.get('last_colors_used', [])[-Config.MAX_COLORS_TRACKED:],
                'mood': current_state.get('mood', 'contemplative'),
                'mood_history': current_state.get('mood_history', [])[-Config.MAX_MOOD_HISTORY:],
                'energy': current_state.get('energy', 0.5),
                'complexity_tolerance': current_state.get('complexity_tolerance', 0.5),
                'style_affinities': current_state.get('style_affinities', {}),
                'subject_interests': current_state.get('subject_interests', {}),
                'personality': current_state.get('personality', {}),
                'last_updated': datetime.now().isoformat()
            }

            with open(self.memory_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            logger.debug(f"Memory saved to {self.memory_file}")
        except Exception as e:
            logger.error(f"Failed to save memory: {e}")
            
    def add_painting(self, painting_record: Dict, current_state: Dict):
        """Helper to add painting and save immediately"""
        portfolio = current_state.get('portfolio', [])
        portfolio.append(painting_record)
        current_state['portfolio'] = portfolio
        
        themes = current_state.get('themes_explored', [])
        themes.append(painting_record['subject'])
        current_state['themes_explored'] = themes
        
        self.save(current_state)
