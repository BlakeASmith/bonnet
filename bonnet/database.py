import sqlite3
import os
from typing import List, Dict, Optional, Tuple

# Global database connection
_db_path = "bonnet.db"
_initialized = False

def init_database():
    """Initialize the database with the memories table and FTS5 index."""
    global _initialized
    if _initialized:
        return
        
    conn = sqlite3.connect(_db_path)
    cursor = conn.cursor()
    
    # Create memories table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS memories (
            id TEXT PRIMARY KEY,
            e_id TEXT,
            type TEXT,
            date TEXT,
            subject TEXT,
            detail TEXT,
            memo_search TEXT
        )
    ''')
    
    # Create index on e_id
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_e_id ON memories(e_id)
    ''')
    
    # Create FTS5 virtual table for search
    cursor.execute('''
        CREATE VIRTUAL TABLE IF NOT EXISTS memories_fts USING fts5(
            memo_search,
            content='memories',
            content_rowid='rowid'
        )
    ''')
    
    # Create trigger to keep FTS in sync
    cursor.execute('''
        CREATE TRIGGER IF NOT EXISTS memories_ai AFTER INSERT ON memories BEGIN
            INSERT INTO memories_fts(rowid, memo_search) VALUES (new.rowid, new.memo_search);
        END
    ''')
    
    cursor.execute('''
        CREATE TRIGGER IF NOT EXISTS memories_ad AFTER DELETE ON memories BEGIN
            INSERT INTO memories_fts(memories_fts, rowid, memo_search) VALUES('delete', old.rowid, old.memo_search);
        END
    ''')
    
    cursor.execute('''
        CREATE TRIGGER IF NOT EXISTS memories_au AFTER UPDATE ON memories BEGIN
            INSERT INTO memories_fts(memories_fts, rowid, memo_search) VALUES('delete', old.rowid, old.memo_search);
            INSERT INTO memories_fts(rowid, memo_search) VALUES (new.rowid, new.memo_search);
        END
    ''')
    
    conn.commit()
    conn.close()
    _initialized = True

def store_entity(e_id: str, entity_name: str, memo_search: str) -> bool:
    """Store a master ENTITY record."""
    init_database()
    conn = sqlite3.connect(_db_path)
    cursor = conn.cursor()
    
    try:
        # Check if E_ID already exists
        cursor.execute("SELECT id FROM memories WHERE e_id = ? AND type = 'ENTITY'", (e_id,))
        if cursor.fetchone():
            raise ValueError(f"Entity ID {e_id} already exists")
        
        # Generate memory ID
        cursor.execute("SELECT MAX(CAST(SUBSTR(id, 3) AS INTEGER)) FROM memories WHERE id LIKE 'M-%'")
        result = cursor.fetchone()[0]
        count = result if result is not None else 0
        memory_id = f"M-{count + 1:03d}"
        
        cursor.execute('''
            INSERT INTO memories (id, e_id, type, subject, detail, memo_search)
            VALUES (?, ?, 'ENTITY', ?, ?, ?)
        ''', (memory_id, e_id, entity_name, entity_name, memo_search))
        
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def store_attribute(e_id: str, attr_type: str, subject: str, detail: str, date: str = None) -> bool:
    """Store a linked attribute (fact, task, rule, ref)."""
    init_database()
    conn = sqlite3.connect(_db_path)
    cursor = conn.cursor()
    
    try:
        # Check if E_ID exists
        cursor.execute("SELECT id FROM memories WHERE e_id = ? AND type = 'ENTITY'", (e_id,))
        if not cursor.fetchone():
            raise ValueError(f"Entity ID {e_id} does not exist")
        
        # Validate date for TASK type
        if attr_type == 'TASK' and not date:
            raise ValueError("TASK type requires --date parameter")
        
        # Generate memory ID
        cursor.execute("SELECT MAX(CAST(SUBSTR(id, 3) AS INTEGER)) FROM memories WHERE id LIKE 'M-%'")
        result = cursor.fetchone()[0]
        count = result if result is not None else 0
        memory_id = f"M-{count + 1:03d}"
        
        # Create memo_search content
        memo_search = f"{attr_type}:{subject}:{detail}"
        if date:
            memo_search += f":{date}"
        
        cursor.execute('''
            INSERT INTO memories (id, e_id, type, date, subject, detail, memo_search)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (memory_id, e_id, attr_type, date, subject, detail, memo_search))
        
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def search_entities(query: str) -> List[Dict]:
    """Search for entities using FTS or exact E_ID match."""
    init_database()
    conn = sqlite3.connect(_db_path)
    cursor = conn.cursor()
    
    # First try exact E_ID match
    cursor.execute('''
        SELECT e_id, subject, detail
        FROM memories
        WHERE type = 'ENTITY' AND e_id = ?
    ''', (query,))
    
    results = []
    for row in cursor.fetchall():
        results.append({
            'e_id': row[0],
            'subject': row[1],
            'detail': row[2]
        })
    
    # If no exact match, try FTS search
    if not results:
        cursor.execute('''
            SELECT DISTINCT e_id, subject, detail
            FROM memories m
            JOIN memories_fts fts ON m.rowid = fts.rowid
            WHERE m.type = 'ENTITY' AND memories_fts MATCH ?
        ''', (query,))
        
        for row in cursor.fetchall():
            results.append({
                'e_id': row[0],
                'subject': row[1],
                'detail': row[2]
            })
    
    conn.close()
    return results

def get_entity_context(e_id: str) -> Dict:
    """Get all linked records for an entity ID."""
    init_database()
    conn = sqlite3.connect(_db_path)
    cursor = conn.cursor()
    
    # Get entity info
    cursor.execute('''
        SELECT subject, detail FROM memories 
        WHERE e_id = ? AND type = 'ENTITY'
    ''', (e_id,))
    entity_row = cursor.fetchone()
    
    if not entity_row:
        raise ValueError(f"Entity ID {e_id} not found")
    
    entity_name = entity_row[0]
    
    # Get all linked attributes
    cursor.execute('''
        SELECT type, subject, detail, date FROM memories 
        WHERE e_id = ? AND type != 'ENTITY'
        ORDER BY type, subject
    ''', (e_id,))
    
    attributes = []
    for row in cursor.fetchall():
        attr = {
            'type': row[0],
            'subject': row[1],
            'detail': row[2],
            'date': row[3]
        }
        attributes.append(attr)
    
    conn.close()
    
    return {
        'e_id': e_id,
        'entity_name': entity_name,
        'attributes': attributes
    }