"""
Comprehensive caching system for AI Prompt Toolkit.
Supports Redis, in-memory, and hybrid caching strategies.
"""

import json
import hashlib
import pickle
from typing import Any, Optional, Dict, List, Union, Callable
from datetime import datetime, timedelta
from functools import wraps
from dataclasses import dataclass
import structlog
import asyncio

try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

from ai_prompt_toolkit.core.config import settings

logger = structlog.get_logger(__name__)


@dataclass
class CacheEntry:
    """Represents a cache entry with metadata."""
    key: str
    value: Any
    created_at: datetime
    expires_at: Optional[datetime] = None
    access_count: int = 0
    last_accessed: datetime = None
    tags: List[str] = None
    size_bytes: int = 0


class InMemoryCache:
    """High-performance in-memory cache with LRU eviction."""
    
    def __init__(self, max_size: int = 1000, default_ttl: int = 3600):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._cache: Dict[str, CacheEntry] = {}
        self._access_order: List[str] = []
        self.logger = structlog.get_logger(__name__)
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        if key not in self._cache:
            return None
        
        entry = self._cache[key]
        
        # Check expiration
        if entry.expires_at and datetime.utcnow() > entry.expires_at:
            await self.delete(key)
            return None
        
        # Update access statistics
        entry.access_count += 1
        entry.last_accessed = datetime.utcnow()
        
        # Update LRU order
        if key in self._access_order:
            self._access_order.remove(key)
        self._access_order.append(key)
        
        return entry.value
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache."""
        try:
            # Calculate expiration
            expires_at = None
            if ttl or self.default_ttl:
                expires_at = datetime.utcnow() + timedelta(seconds=ttl or self.default_ttl)
            
            # Calculate size
            size_bytes = len(pickle.dumps(value))
            
            # Create entry
            entry = CacheEntry(
                key=key,
                value=value,
                created_at=datetime.utcnow(),
                expires_at=expires_at,
                size_bytes=size_bytes
            )
            
            # Evict if necessary
            await self._evict_if_needed()
            
            # Store entry
            self._cache[key] = entry
            if key not in self._access_order:
                self._access_order.append(key)
            
            return True
        except Exception as e:
            self.logger.error("Failed to set cache entry", key=key, error=str(e))
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete entry from cache."""
        if key in self._cache:
            del self._cache[key]
            if key in self._access_order:
                self._access_order.remove(key)
            return True
        return False
    
    async def clear(self) -> bool:
        """Clear all cache entries."""
        self._cache.clear()
        self._access_order.clear()
        return True
    
    async def _evict_if_needed(self):
        """Evict least recently used entries if cache is full."""
        while len(self._cache) >= self.max_size and self._access_order:
            lru_key = self._access_order[0]
            await self.delete(lru_key)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total_size = sum(entry.size_bytes for entry in self._cache.values())
        return {
            "type": "in_memory",
            "entries": len(self._cache),
            "max_size": self.max_size,
            "total_size_bytes": total_size,
            "hit_rate": self._calculate_hit_rate()
        }
    
    def _calculate_hit_rate(self) -> float:
        """Calculate cache hit rate."""
        total_accesses = sum(entry.access_count for entry in self._cache.values())
        if total_accesses == 0:
            return 0.0
        return len(self._cache) / total_accesses


class RedisCache:
    """Redis-based distributed cache."""
    
    def __init__(self, redis_url: str, default_ttl: int = 3600):
        self.redis_url = redis_url
        self.default_ttl = default_ttl
        self.redis_client = None
        self.logger = structlog.get_logger(__name__)
    
    async def connect(self):
        """Connect to Redis."""
        if not REDIS_AVAILABLE:
            raise RuntimeError("Redis not available. Install with: pip install redis")
        
        try:
            self.redis_client = redis.from_url(self.redis_url)
            await self.redis_client.ping()
            self.logger.info("Connected to Redis", url=self.redis_url)
        except Exception as e:
            self.logger.error("Failed to connect to Redis", error=str(e))
            raise
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from Redis cache."""
        if not self.redis_client:
            await self.connect()
        
        try:
            data = await self.redis_client.get(key)
            if data:
                return pickle.loads(data)
            return None
        except Exception as e:
            self.logger.error("Failed to get from Redis cache", key=key, error=str(e))
            return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in Redis cache."""
        if not self.redis_client:
            await self.connect()
        
        try:
            data = pickle.dumps(value)
            await self.redis_client.set(key, data, ex=ttl or self.default_ttl)
            return True
        except Exception as e:
            self.logger.error("Failed to set Redis cache entry", key=key, error=str(e))
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete entry from Redis cache."""
        if not self.redis_client:
            await self.connect()
        
        try:
            result = await self.redis_client.delete(key)
            return result > 0
        except Exception as e:
            self.logger.error("Failed to delete from Redis cache", key=key, error=str(e))
            return False
    
    async def clear(self) -> bool:
        """Clear all cache entries."""
        if not self.redis_client:
            await self.connect()
        
        try:
            await self.redis_client.flushdb()
            return True
        except Exception as e:
            self.logger.error("Failed to clear Redis cache", error=str(e))
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get Redis cache statistics."""
        # This would require Redis INFO command
        return {
            "type": "redis",
            "connected": self.redis_client is not None,
            "url": self.redis_url
        }


class HybridCache:
    """Hybrid cache combining in-memory and Redis caching."""
    
    def __init__(self, memory_cache: InMemoryCache, redis_cache: Optional[RedisCache] = None):
        self.memory_cache = memory_cache
        self.redis_cache = redis_cache
        self.logger = structlog.get_logger(__name__)
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache (memory first, then Redis)."""
        # Try memory cache first
        value = await self.memory_cache.get(key)
        if value is not None:
            return value
        
        # Try Redis cache
        if self.redis_cache:
            value = await self.redis_cache.get(key)
            if value is not None:
                # Store in memory cache for faster access
                await self.memory_cache.set(key, value)
                return value
        
        return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in both caches."""
        memory_success = await self.memory_cache.set(key, value, ttl)
        redis_success = True
        
        if self.redis_cache:
            redis_success = await self.redis_cache.set(key, value, ttl)
        
        return memory_success and redis_success
    
    async def delete(self, key: str) -> bool:
        """Delete from both caches."""
        memory_success = await self.memory_cache.delete(key)
        redis_success = True
        
        if self.redis_cache:
            redis_success = await self.redis_cache.delete(key)
        
        return memory_success and redis_success
    
    async def clear(self) -> bool:
        """Clear both caches."""
        memory_success = await self.memory_cache.clear()
        redis_success = True
        
        if self.redis_cache:
            redis_success = await self.redis_cache.clear()
        
        return memory_success and redis_success
    
    def get_stats(self) -> Dict[str, Any]:
        """Get combined cache statistics."""
        stats = {
            "type": "hybrid",
            "memory": self.memory_cache.get_stats()
        }
        
        if self.redis_cache:
            stats["redis"] = self.redis_cache.get_stats()
        
        return stats


class CacheManager:
    """Main cache manager with intelligent caching strategies."""
    
    def __init__(self):
        self.logger = structlog.get_logger(__name__)
        self._cache = self._initialize_cache()
    
    def _initialize_cache(self):
        """Initialize the appropriate cache backend."""
        memory_cache = InMemoryCache(
            max_size=getattr(settings, 'cache_memory_max_size', 1000),
            default_ttl=getattr(settings, 'cache_default_ttl', 3600)
        )
        
        # Try to initialize Redis cache if configured
        redis_cache = None
        if hasattr(settings, 'redis') and settings.redis.url:
            try:
                redis_cache = RedisCache(settings.redis.url)
            except Exception as e:
                self.logger.warning("Failed to initialize Redis cache, using memory only", error=str(e))
        
        if redis_cache:
            return HybridCache(memory_cache, redis_cache)
        else:
            return memory_cache
    
    def _generate_cache_key(self, prefix: str, *args, **kwargs) -> str:
        """Generate a cache key from arguments."""
        # Create a deterministic key from arguments
        key_data = {
            'args': args,
            'kwargs': sorted(kwargs.items())
        }
        key_hash = hashlib.md5(json.dumps(key_data, sort_keys=True, default=str).encode()).hexdigest()
        return f"{prefix}:{key_hash}"
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        return await self._cache.get(key)
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache."""
        return await self._cache.set(key, value, ttl)
    
    async def delete(self, key: str) -> bool:
        """Delete value from cache."""
        return await self._cache.delete(key)
    
    async def clear(self) -> bool:
        """Clear all cache entries."""
        return await self._cache.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return self._cache.get_stats()
    
    # Specialized caching methods
    async def cache_prompt_analysis(self, prompt: str, analysis: Dict[str, Any], ttl: int = 3600) -> bool:
        """Cache prompt analysis results."""
        key = self._generate_cache_key("prompt_analysis", prompt)
        return await self.set(key, analysis, ttl)
    
    async def get_cached_prompt_analysis(self, prompt: str) -> Optional[Dict[str, Any]]:
        """Get cached prompt analysis."""
        key = self._generate_cache_key("prompt_analysis", prompt)
        return await self.get(key)
    
    async def cache_optimization_result(self, prompt: str, strategy: str, result: Dict[str, Any], ttl: int = 7200) -> bool:
        """Cache optimization results."""
        key = self._generate_cache_key("optimization", prompt, strategy)
        return await self.set(key, result, ttl)
    
    async def get_cached_optimization(self, prompt: str, strategy: str) -> Optional[Dict[str, Any]]:
        """Get cached optimization result."""
        key = self._generate_cache_key("optimization", prompt, strategy)
        return await self.get(key)
    
    async def cache_llm_response(self, prompt: str, provider: str, model: str, response: str, ttl: int = 1800) -> bool:
        """Cache LLM responses."""
        key = self._generate_cache_key("llm_response", prompt, provider, model)
        return await self.set(key, response, ttl)
    
    async def get_cached_llm_response(self, prompt: str, provider: str, model: str) -> Optional[str]:
        """Get cached LLM response."""
        key = self._generate_cache_key("llm_response", prompt, provider, model)
        return await self.get(key)


# Global cache manager instance
cache_manager = CacheManager()


# Decorators for automatic caching
def cache_result(prefix: str, ttl: int = 3600):
    """Decorator to automatically cache function results."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key
            key = cache_manager._generate_cache_key(prefix, *args, **kwargs)
            
            # Try to get from cache
            cached_result = await cache_manager.get(key)
            if cached_result is not None:
                return cached_result
            
            # Execute function and cache result
            result = await func(*args, **kwargs)
            await cache_manager.set(key, result, ttl)
            
            return result
        return wrapper
    return decorator
