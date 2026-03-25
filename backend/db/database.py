"""
SQLite Database Layer for Calendar Agent
Provides caching and memory storage
"""

import sqlite3
import os
from datetime import datetime
from typing import Optional, List, Dict, Any
from contextlib import contextmanager

# Database path
DB_PATH = os.getenv("DB_PATH", "calendar_agent.db")

def get_connection():
    """Get SQLite connection with UTF-8 encoding"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    # Enable UTF-8 support
    conn.execute("PRAGMA encoding = 'UTF-8'")
    return conn

@contextmanager
def get_db():
    """Context manager for database operations"""
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def init_db():
    """Initialize database tables"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Events cache table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS events_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                event_id TEXT NOT NULL,
                title TEXT,
                description TEXT,
                start_time TEXT NOT NULL,
                end_time TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                UNIQUE(user_id, event_id)
            )
        """)
        
        # User memory table (for medium-term memory)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_memory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                key TEXT NOT NULL,
                value TEXT,
                timestamp TEXT NOT NULL,
                UNIQUE(user_id, key)
            )
        """)
        
        # Agent behavior table (for long-term memory)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS agent_behavior (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                pattern_type TEXT NOT NULL,
                pattern_data TEXT,
                confidence REAL DEFAULT 0.0,
                updated_at TEXT NOT NULL,
                UNIQUE(user_id, pattern_type)
            )
        """)
        
        # Create indexes
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_events_user 
            ON events_cache(user_id)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_memory_user 
            ON user_memory(user_id)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_behavior_user 
            ON agent_behavior(user_id)
        """)
        
        # Users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                email TEXT NOT NULL,
                name TEXT,
                timezone TEXT DEFAULT 'UTC',
                preferences TEXT DEFAULT '{}',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)

# ============== Events Cache Operations ==============

def cache_event(user_id: str, event_id: str, title: str, description: Optional[str],
                start_time: str, end_time: str) -> None:
    """Cache an event"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO events_cache 
            (user_id, event_id, title, description, start_time, end_time, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (user_id, event_id, title, description, start_time, end_time, datetime.utcnow().isoformat()))

def get_cached_events(user_id: str, min_updated_at: Optional[str] = None) -> List[Dict[str, Any]]:
    """Get cached events for user"""
    with get_db() as conn:
        cursor = conn.cursor()
        if min_updated_at:
            cursor.execute("""
                SELECT * FROM events_cache 
                WHERE user_id = ? AND updated_at > ?
                ORDER BY start_time
            """, (user_id, min_updated_at))
        else:
            cursor.execute("""
                SELECT * FROM events_cache 
                WHERE user_id = ?
                ORDER BY start_time
            """, (user_id,))
        
        return [dict(row) for row in cursor.fetchall()]

def invalidate_user_cache(user_id: str) -> None:
    """Invalidate all cache for a user"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM events_cache WHERE user_id = ?", (user_id,))

def delete_cached_event(user_id: str, event_id: str) -> None:
    """Delete a specific cached event"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM events_cache WHERE user_id = ? AND event_id = ?", 
                      (user_id, event_id))

# ============== User Memory Operations ==============

def set_user_memory(user_id: str, key: str, value: str) -> None:
    """Set user memory (medium-term)"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO user_memory 
            (user_id, key, value, timestamp)
            VALUES (?, ?, ?, ?)
        """, (user_id, key, value, datetime.utcnow().isoformat()))

def get_user_memory(user_id: str, key: Optional[str] = None) -> Dict[str, Any]:
    """Get user memory"""
    with get_db() as conn:
        cursor = conn.cursor()
        if key:
            cursor.execute("""
                SELECT * FROM user_memory 
                WHERE user_id = ? AND key = ?
            """, (user_id, key))
            row = cursor.fetchone()
            return dict(row) if row else {}
        else:
            cursor.execute("""
                SELECT * FROM user_memory 
                WHERE user_id = ?
            """, (user_id,))
            return {row['key']: row['value'] for row in cursor.fetchall()}

# ============== Agent Behavior Operations ==============

def update_behavior_pattern(user_id: str, pattern_type: str, 
                           pattern_data: str, confidence: float = 0.5) -> None:
    """Update behavior pattern (long-term memory)"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO agent_behavior 
            (user_id, pattern_type, pattern_data, confidence, updated_at)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, pattern_type, pattern_data, confidence, datetime.utcnow().isoformat()))

def get_behavior_patterns(user_id: str) -> List[Dict[str, Any]]:
    """Get all behavior patterns for user"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM agent_behavior 
            WHERE user_id = ?
            ORDER BY confidence DESC
        """, (user_id,))
        return [dict(row) for row in cursor.fetchall()]

# ============== Undo Operations ==============

def store_action_for_undo(user_id: str, action_type: str, event_data: dict) -> str:
    """Store an action that can be undone within 30 seconds"""
    import json
    import uuid
    
    undo_token = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()
    
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO user_memory (user_id, key, value, timestamp)
            VALUES (?, ?, ?, ?)
        """, (user_id, f"undo_{undo_token}", json.dumps({
            "action_type": action_type,
            "event_data": event_data,
            "timestamp": now
        }), now))
    
    return undo_token

def get_undo_action(user_id: str, undo_token: str) -> Optional[Dict]:
    """Get undo action if within 30 second window"""
    import json
    
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT value, timestamp FROM user_memory 
            WHERE user_id = ? AND key = ?
        """, (user_id, f"undo_{undo_token}"))
        row = cursor.fetchone()
        
        if not row:
            return None
        
        # Check if within 30 seconds
        action_time = datetime.fromisoformat(row['timestamp'])
        if (datetime.utcnow() - action_time).total_seconds() > 30:
            return None
        
        return json.loads(row['value'])

def clear_undo_token(user_id: str, undo_token: str) -> None:
    """Clear undo token after use"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM user_memory WHERE user_id = ? AND key = ?",
                      (user_id, f"undo_{undo_token}"))

# ============== User Operations ==============

def create_or_update_user(user_id: str, email: str, name: str = None, 
                          timezone: str = "UTC", preferences: dict = None) -> None:
    """Create or update user profile"""
    now = datetime.utcnow().isoformat()
    prefs_json = json.dumps(preferences) if preferences else "{}"
    
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO users (user_id, email, name, timezone, preferences, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                email = excluded.email,
                name = excluded.name,
                timezone = excluded.timezone,
                preferences = excluded.preferences,
                updated_at = excluded.updated_at
        """, (user_id, email, name, timezone, prefs_json, now, now))

def get_user(user_id: str) -> Optional[Dict[str, Any]]:
    """Get user by ID"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

def update_user_timezone(user_id: str, timezone: str) -> None:
    """Update user timezone"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE users 
            SET timezone = ?, updated_at = ?
            WHERE user_id = ?
        """, (timezone, datetime.utcnow().isoformat(), user_id))

def update_user_preferences(user_id: str, preferences: dict) -> None:
    """Update user preferences"""
    import json
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE users 
            SET preferences = ?, updated_at = ?
            WHERE user_id = ?
        """, (json.dumps(preferences), datetime.utcnow().isoformat(), user_id))

# Initialize on import
import json
init_db()
