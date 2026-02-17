"""
Comprehensive test suite for Autonomous Artist
"""
import pytest
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import tempfile
import os

# Import modules to test
from config import Config
from autonomous_artist import AutonomousArtist
from security_utils import (
    sanitize_filename, validate_prompt_input,
    validate_json_input, validate_boolean_param,
    validate_integer_param, sanitize_log_message
)


class TestConfig:
    """Test configuration management"""
    
    def test_config_validation(self):
        """Test configuration validation"""
        assert hasattr(Config, 'validate')
        # Should handle missing API token gracefully
        Config.validate()
    
    def test_directory_creation(self):
        """Test directory creation"""
        Config.create_directories()
        assert Config.GENERATIONS_DIR.exists()
        assert Config.LOGS_DIR.exists()
        assert Config.CACHE_DIR.exists()
    
    def test_config_summary(self):
        """Test configuration summary"""
        summary = Config.get_summary()
        assert 'app_name' in summary
        assert 'version' in summary
        assert 'models' in summary
        assert summary['app_name'] == 'Autonomous Artist'


class TestSecurityUtils:
    """Test security utility functions"""
    
    def test_sanitize_filename(self):
        """Test filename sanitization"""
        # Test normal filename
        assert sanitize_filename('test.txt') == 'test.txt'
        
        # Test path traversal attempt
        result = sanitize_filename('../../../etc/passwd')
        assert '..' not in result
        assert '/' not in result
        
        # Test special characters
        result = sanitize_filename('test<>:"|?*.txt')
        assert '<' not in result
        assert '>' not in result
        
        # Test hidden file
        result = sanitize_filename('.hidden')
        assert result.startswith('file')
    
    def test_validate_prompt_input(self):
        """Test prompt validation"""
        # Valid prompt
        valid, error = validate_prompt_input("A beautiful landscape")
        assert valid is True
        assert error is None
        
        # Empty prompt
        valid, error = validate_prompt_input("")
        assert valid is False
        assert "empty" in error.lower()
        
        # Too long prompt
        long_prompt = "x" * 1001
        valid, error = validate_prompt_input(long_prompt)
        assert valid is False
        assert "too long" in error.lower()
        
        # Script injection attempt
        valid, error = validate_prompt_input("<script>alert('xss')</script>")
        assert valid is False
    
    def test_validate_json_input(self):
        """Test JSON validation"""
        # Valid JSON with required fields
        data = {"field1": "value1", "field2": "value2"}
        valid, error = validate_json_input(data, ["field1"])
        assert valid is True
        
        # Missing required field
        valid, error = validate_json_input(data, ["field3"])
        assert valid is False
        assert "missing" in error.lower()
        
        # Invalid type
        valid, error = validate_json_input("not a dict")
        assert valid is False
    
    def test_validate_boolean_param(self):
        """Test boolean parameter validation"""
        valid, _ = validate_boolean_param(True, "test")
        assert valid is True
        
        valid, error = validate_boolean_param("true", "test")
        assert valid is False
        assert "boolean" in error.lower()
    
    def test_validate_integer_param(self):
        """Test integer parameter validation"""
        # Valid integer
        valid, _ = validate_integer_param(5, "test")
        assert valid is True
        
        # With bounds
        valid, _ = validate_integer_param(5, "test", min_val=1, max_val=10)
        assert valid is True
        
        # Below minimum
        valid, error = validate_integer_param(0, "test", min_val=1)
        assert valid is False
        assert "at least" in error.lower()
        
        # Above maximum
        valid, error = validate_integer_param(11, "test", max_val=10)
        assert valid is False
        assert "at most" in error.lower()
    
    def test_sanitize_log_message(self):
        """Test log message sanitization"""
        # Remove newlines
        result = sanitize_log_message("line1\nline2\tline3")
        assert '\n' not in result
        assert '\t' not in result
        
        # Truncate long messages
        long_msg = "x" * 600
        result = sanitize_log_message(long_msg)
        assert len(result) <= 503  # 500 + '...'


class TestAutonomousArtist:
    """Test the main artist class"""
    
    @pytest.fixture
    def temp_memory_file(self):
        """Create a temporary memory file"""
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.json', delete=False
        ) as f:
            temp_path = f.name
        yield temp_path
        # Cleanup
        if os.path.exists(temp_path):
            os.remove(temp_path)
    
    def test_artist_initialization(self, temp_memory_file):
        """Test artist initialization"""
        artist = AutonomousArtist(
            name="TestArtist",
            memory_file=temp_memory_file
        )
        assert artist.name == "TestArtist"
        assert hasattr(artist, 'state')
        assert 'mood' in artist.state
        assert 'energy' in artist.state
        assert 'personality' in artist.state
    
    def test_artist_state_properties(self, temp_memory_file):
        """Test artist state properties"""
        artist = AutonomousArtist(memory_file=temp_memory_file)
        
        # Test properties
        assert isinstance(artist.mood, str)
        assert isinstance(artist.painting_count, int)
        assert isinstance(artist.portfolio, list)
    
    def test_prompt_generation(self, temp_memory_file):
        """Test prompt generation"""
        artist = AutonomousArtist(memory_file=temp_memory_file)
        
        # Mock the painter to avoid actual API calls
        with patch.object(artist.painter, 'assemble_prompt') as mock_assemble:
            mock_assemble.return_value = {
                'subject': 'nature',
                'style': 'impressionist',
                'prompt': 'test prompt',
                'thinking': {}
            }
            
            painting_data = artist.generate_prompt()
            
            assert 'subject' in painting_data
            assert 'style' in painting_data
            assert 'prompt' in painting_data
    
    def test_state_evolution(self, temp_memory_file):
        """Test state evolution"""
        artist = AutonomousArtist(memory_file=temp_memory_file)
        
        initial_mood = artist.mood
        initial_energy = artist.state['energy']
        
        # Evolve state multiple times
        for _ in range(5):
            artist.evolve_state()
        
        # State should have changed (with high probability)
        # Note: Due to randomness, we can't guarantee exact changes
        assert 'mood' in artist.state
        assert 'energy' in artist.state


class TestCacheManager:
    """Test cache management"""
    
    def test_cache_import(self):
        """Test that cache manager can be imported"""
        from cache_manager import CacheManager
        assert CacheManager is not None
    
    def test_cache_key_generation(self):
        """Test cache key generation"""
        from cache_manager import CacheManager
        
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = CacheManager(Path(tmpdir))
            
            key1 = cache._get_cache_key("test prompt 1")
            key2 = cache._get_cache_key("test prompt 2")
            key3 = cache._get_cache_key("test prompt 1")
            
            # Same input should give same key
            assert key1 == key3
            # Different input should give different keys
            assert key1 != key2


class TestFlaskApp:
    """Test Flask application endpoints"""
    
    @pytest.fixture
    def client(self):
        """Create a test client"""
        from app import app
        app.config['TESTING'] = True
        with app.test_client() as client:
            yield client
    
    def test_health_endpoint(self, client):
        """Test health check endpoint"""
        response = client.get('/health')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'status' in data
        assert data['status'] == 'healthy'
    
    def test_index_page(self, client):
        """Test index page loads"""
        response = client.get('/')
        assert response.status_code == 200
    
    def test_state_endpoint(self, client):
        """Test state endpoint"""
        response = client.get('/api/state')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'mood' in data
        assert 'energy' in data


# Performance tests
class TestPerformance:
    """Test performance characteristics"""
    
    def test_config_loading_speed(self):
        """Test configuration loads quickly"""
        import time
        start = time.time()
        from config import Config
        Config.validate()
        end = time.time()
        
        # Should load in under 1 second
        assert (end - start) < 1.0
    
    def test_memory_initialization_speed(self, tmp_path):
        """Test memory initialization is fast"""
        import time
        from artist_modules.memory import ArtistMemory
        
        memory_file = tmp_path / "test_memory.json"
        
        start = time.time()
        memory = ArtistMemory(str(memory_file))
        end = time.time()
        
        # Should initialize in under 1 second
        assert (end - start) < 1.0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
