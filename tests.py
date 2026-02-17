"""
Unit tests for Autonomous Artist
Run with: python -m pytest tests.py -v
"""
import pytest
from pathlib import Path
from autonomous_artist import AutonomousArtist
from artist_modules.brain import ArtistBrain
from artist_modules.painter import ArtistPainter
from artist_modules.memory import ArtistMemory
from config import Config


class TestConfig:
    """Test configuration management"""
    
    def test_config_validation(self):
        """Test that config validation works"""
        # Should not raise exception
        assert Config.validate() is not None
    
    def test_config_summary(self):
        """Test config summary generation"""
        summary = Config.get_summary()
        assert 'app' in summary
        assert 'api' in summary
        assert 'memory' in summary
    
    def test_config_directories(self):
        """Test directory creation"""
        Config.create_directories()
        assert Config.GENERATIONS_DIR.exists()
        assert Config.LOGS_DIR.exists()


class TestArtistBrain:
    """Test the artist's cognitive functions"""
    
    def setup_method(self):
        """Setup for each test"""
        self.brain = ArtistBrain()
    
    def test_mood_list_complete(self):
        """Test that anxious mood is in the list"""
        assert 'anxious' in self.brain.MOODS
        assert 'contemplative' in self.brain.MOODS
        assert len(self.brain.MOODS) == 16
    
    def test_choose_subject(self):
        """Test subject selection"""
        interests = {
            'nature': 0.8,
            'urban': 0.5,
            'portraits': 0.3
        }
        subject = self.brain.choose_subject(interests)
        assert subject in interests.keys()
    
    def test_choose_style(self):
        """Test style selection"""
        affinities = {
            'impressionist': 0.7,
            'abstract_expressionism': 0.5,
            'minimalist': 0.3
        }
        style = self.brain.choose_style('contemplative', affinities)
        assert style in affinities.keys()
    
    def test_choose_colors(self):
        """Test color selection"""
        colors = self.brain.choose_colors('energized', [])
        assert isinstance(colors, list)
        assert len(colors) > 0
    
    def test_evolve_state(self):
        """Test state evolution"""
        state = {
            'mood': 'contemplative',
            'energy': 0.5,
            'complexity_tolerance': 0.5,
            'painting_count': 0,
            'portfolio': [],
            'themes_explored': [],
            'last_colors_used': [],
            'mood_history': [],
            'personality': {
                'openness': 0.7,
                'conscientiousness': 0.5,
                'extraversion': 0.5,
                'agreeableness': 0.5,
                'neuroticism': 0.5
            },
            'style_affinities': {'impressionist': 0.5},
            'subject_interests': {'nature': 0.5}
        }
        
        new_state = self.brain.evolve_state(state)
        assert 'mood' in new_state
        assert 'energy' in new_state
        assert 0.15 <= new_state['energy'] <= 0.95
    
    def test_mood_transitions(self):
        """Test mood transition logic"""
        state = {
            'mood': 'contemplative',
            'energy': 0.5,
            'mood_history': []
        }
        
        new_mood = self.brain._select_next_mood('contemplative', 0.5, [])
        assert new_mood in self.brain.MOODS
    
    def test_learn_from_satisfaction(self):
        """Test learning from satisfaction"""
        painting_data = {
            'style': 'impressionist',
            'subject': 'nature'
        }
        
        # High satisfaction should increase affinity
        state_high = {
            'style_affinities': {'impressionist': 0.5},
            'subject_interests': {'nature': 0.5}
        }
        new_state = self.brain.learn_from_satisfaction(state_high, painting_data, 0.9)
        assert new_state['style_affinities']['impressionist'] > 0.5
        assert new_state['subject_interests']['nature'] > 0.5
        
        # Low satisfaction should decrease affinity
        state_low = {
            'style_affinities': {'impressionist': 0.5},
            'subject_interests': {'nature': 0.5}
        }
        new_state2 = self.brain.learn_from_satisfaction(state_low, painting_data, 0.2)
        assert new_state2['style_affinities']['impressionist'] < 0.5


class TestArtistPainter:
    """Test the painter's craft functions"""
    
    def setup_method(self):
        """Setup for each test"""
        self.painter = ArtistPainter()
    
    def test_assemble_prompt(self):
        """Test prompt assembly"""
        painting_data = self.painter.assemble_prompt(
            subject='nature',
            style='impressionist',
            colors=['soft blues', 'gentle greens'],
            mood='contemplative',
            energy=0.5,
            complexity=0.5,
            personality={'openness': 0.7, 'conscientiousness': 0.5, 
                        'extraversion': 0.5, 'agreeableness': 0.5, 'neuroticism': 0.5}
        )
        
        assert 'prompt' in painting_data
        assert 'subject' in painting_data
        assert 'style' in painting_data
        assert 'colors' in painting_data
        assert isinstance(painting_data['prompt'], str)
        assert len(painting_data['prompt']) > 0
    
    def test_composition_selection(self):
        """Test composition selection"""
        comp = self.painter._select_composition('serene', 0.3, None)
        assert comp in self.painter.COMPOSITIONS.values() or comp == ""


class TestArtistMemory:
    """Test memory persistence"""
    
    def setup_method(self):
        """Setup for each test"""
        self.test_file = Path("test_memory.json")
        self.memory = ArtistMemory(str(self.test_file))
    
    def teardown_method(self):
        """Cleanup after test"""
        if self.test_file.exists():
            self.test_file.unlink()
    
    def test_save_and_load(self):
        """Test saving and loading memory"""
        test_state = {
            'mood': 'contemplative',
            'energy': 0.5,
            'painting_count': 5,
            'portfolio': [{'number': i} for i in range(5)],
            'themes_explored': ['nature'] * 3,
            'last_colors_used': ['blue', 'green'],
            'mood_history': ['contemplative', 'serene'],
            'complexity_tolerance': 0.5,
            'style_affinities': {'impressionist': 0.5},
            'subject_interests': {'nature': 0.5},
            'personality': {'openness': 0.7}
        }
        
        self.memory.save(test_state)
        assert self.test_file.exists()
        
        loaded_state = self.memory.load()
        assert loaded_state['mood'] == 'contemplative'
        assert loaded_state['painting_count'] == 5
    
    def test_portfolio_limit(self):
        """Test that portfolio is limited to MAX_PORTFOLIO_SIZE"""
        large_portfolio = [{'number': i} for i in range(100)]
        test_state = {
            'portfolio': large_portfolio,
            'painting_count': 100,
            'mood': 'contemplative',
            'energy': 0.5
        }
        
        self.memory.save(test_state)
        loaded_state = self.memory.load()
        
        # Should be limited to Config.MAX_PORTFOLIO_SIZE
        assert len(loaded_state['portfolio']) <= Config.MAX_PORTFOLIO_SIZE


class TestAutonomousArtist:
    """Test the main artist coordinator"""
    
    def setup_method(self):
        """Setup for each test"""
        self.test_file = Path("test_artist_memory.json")
        self.artist = AutonomousArtist(name="TestArtist", memory_file=str(self.test_file))
    
    def teardown_method(self):
        """Cleanup after test"""
        if self.test_file.exists():
            self.test_file.unlink()
    
    def test_initialization(self):
        """Test artist initialization"""
        assert self.artist.name == "TestArtist"
        assert 'mood' in self.artist.state
        assert 'energy' in self.artist.state
        assert 'personality' in self.artist.state
    
    def test_generate_prompt(self):
        """Test prompt generation"""
        painting_data = self.artist.generate_prompt()
        
        assert 'prompt' in painting_data
        assert 'subject' in painting_data
        assert 'style' in painting_data
        assert 'colors' in painting_data
    
    def test_get_current_state(self):
        """Test state retrieval"""
        state = self.artist.get_current_state()
        
        assert 'name' in state
        assert 'mood' in state
        assert 'energy' in state
        assert 'paintings_created' in state
        assert 'current_interests' in state
        assert 'style_affinities' in state
    
    def test_evolve_state(self):
        """Test state evolution"""
        # Just verify that evolve_state runs without error
        self.artist.evolve_state()
        
        # State should have required keys
        assert 'mood' in self.artist.state
        assert 'energy' in self.artist.state
        assert 0.15 <= self.artist.state['energy'] <= 0.95
    
    def test_properties(self):
        """Test backward compatibility properties"""
        assert isinstance(self.artist.portfolio, list)
        assert isinstance(self.artist.painting_count, int)
        assert isinstance(self.artist.mood, str)


class TestInputValidation:
    """Test input validation and security"""
    
    def test_validate_prompt(self):
        """Test prompt validation"""
        from utils import validate_prompt
        
        # Valid prompt
        valid = validate_prompt("Create a beautiful painting")
        assert isinstance(valid, str)
        
        # Empty prompt should raise error
        with pytest.raises(ValueError):
            validate_prompt("")
        
        # Non-string should raise error
        with pytest.raises(ValueError):
            validate_prompt(123)
        
        # Very long prompt should be truncated
        long_prompt = "a" * 2000
        truncated = validate_prompt(long_prompt)
        assert len(truncated) <= 1000


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
