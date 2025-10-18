import sqlite3
import os
from contextlib import contextmanager
from typing import List, Dict, Optional, Tuple

# Global database connection
_db_path = "bonnet.db"
_initialized = False

@contextmanager
def transaction(conn: sqlite3.Connection = None, rollback: bool = True):
    """Context manager for database transactions"""
    if conn is None:
        conn = sqlite3.connect(_db_path)
    try:
        yield conn.cursor()
        conn.commit()
    except Exception:
        if rollback:
            conn.rollback()
        raise
    finally:
        conn.close()

def init_database():
    """Initialize the database with the memories table and FTS5 index."""
    global _initialized
    if _initialized:
        return
        
    conn = sqlite3.connect(_db_path)
    with transaction(conn, rollback=False) as cursor:
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
        
        # Create groups table for entity groupings
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS groups (
                group_id TEXT PRIMARY KEY,
                group_name TEXT NOT NULL,
                description TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create group_entities table for many-to-many relationship between groups and entities
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS group_entities (
                group_id TEXT,
                e_id TEXT,
                relationship_type TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (group_id, e_id),
                FOREIGN KEY (group_id) REFERENCES groups(group_id),
                FOREIGN KEY (e_id) REFERENCES memories(e_id)
            )
        ''')
        
        # Create index on e_id
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_e_id ON memories(e_id)
        ''')
        
        # Create index on group_id
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_group_id ON group_entities(group_id)
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
    
    _initialized = True
    return conn

def store_entity(e_id: str, entity_name: str, memo_search: str) -> bool:
    """Store a master ENTITY record."""
    conn = init_database()
    
    with transaction(conn) as cursor:
        
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
        
        return True

def store_attribute(e_id: str, attr_type: str, subject: str, detail: str) -> bool:
    """Store a linked attribute (fact, task, rule, ref)."""
    init_database()
    
    with transaction() as cursor:
        # Check if E_ID exists
        cursor.execute("SELECT id FROM memories WHERE e_id = ? AND type = 'ENTITY'", (e_id,))
        if not cursor.fetchone():
            raise ValueError(f"Entity ID {e_id} does not exist")
        
        # Generate memory ID
        cursor.execute("SELECT MAX(CAST(SUBSTR(id, 3) AS INTEGER)) FROM memories WHERE id LIKE 'M-%'")
        result = cursor.fetchone()[0]
        count = result if result is not None else 0
        memory_id = f"M-{count + 1:03d}"
        
        # Create memo_search content
        memo_search = f"{attr_type}:{subject}:{detail}"
        
        cursor.execute('''
            INSERT INTO memories (id, e_id, type, date, subject, detail, memo_search)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (memory_id, e_id, attr_type, None, subject, detail, memo_search))
        
        return True

def search_entities(query: str) -> List[Dict]:
    """Search for entities using FTS or exact E_ID match."""
    init_database()
    conn = sqlite3.connect(_db_path)
    cursor = conn.cursor()
    
    results = []

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


def store_group(group_id: str, group_name: str, description: str = None) -> bool:
    """Store a group record."""
    init_database()
    
    with transaction() as cursor:
        # Check if group_id already exists
        cursor.execute("SELECT group_id FROM groups WHERE group_id = ?", (group_id,))
        if cursor.fetchone():
            raise ValueError(f"Group ID {group_id} already exists")
        
        cursor.execute('''
            INSERT INTO groups (group_id, group_name, description)
            VALUES (?, ?, ?)
        ''', (group_id, group_name, description))
        
        return True


def add_entity_to_group(group_id: str, e_id: str, relationship_type: str = None) -> bool:
    """Add an entity to a group with an optional relationship type."""
    init_database()
    
    with transaction() as cursor:
        # Check if group exists
        cursor.execute("SELECT group_id FROM groups WHERE group_id = ?", (group_id,))
        if not cursor.fetchone():
            raise ValueError(f"Group ID {group_id} does not exist")
        
        # Check if entity exists
        cursor.execute("SELECT e_id FROM memories WHERE e_id = ? AND type = 'ENTITY'", (e_id,))
        if not cursor.fetchone():
            raise ValueError(f"Entity ID {e_id} does not exist")
        
        # Check if relationship already exists
        cursor.execute("SELECT group_id FROM group_entities WHERE group_id = ? AND e_id = ?", (group_id, e_id))
        if cursor.fetchone():
            raise ValueError(f"Entity {e_id} is already in group {group_id}")
        
        cursor.execute('''
            INSERT INTO group_entities (group_id, e_id, relationship_type)
            VALUES (?, ?, ?)
        ''', (group_id, e_id, relationship_type))
        
        return True


def get_group_context(group_id: str) -> Dict:
    """Get all entities and nested groups for a group ID."""
    init_database()
    conn = sqlite3.connect(_db_path)
    cursor = conn.cursor()
    
    # Get group info
    cursor.execute('''
        SELECT group_name, description FROM groups 
        WHERE group_id = ?
    ''', (group_id,))
    group_row = cursor.fetchone()
    
    if not group_row:
        raise ValueError(f"Group ID {group_id} not found")
    
    group_name, description = group_row
    
    # Get all entities in this group
    cursor.execute('''
        SELECT ge.e_id, ge.relationship_type, m.subject, m.detail
        FROM group_entities ge
        JOIN memories m ON ge.e_id = m.e_id
        WHERE ge.group_id = ? AND m.type = 'ENTITY'
        ORDER BY ge.relationship_type, m.subject
    ''', (group_id,))
    
    entities = []
    entity_references = []
    
    for row in cursor.fetchall():
        e_id, relationship_type, entity_name, detail = row
        
        # Get attributes for this entity
        cursor.execute('''
            SELECT type, subject, detail, date FROM memories 
            WHERE e_id = ? AND type != 'ENTITY'
            ORDER BY type, subject
        ''', (e_id,))
        
        attributes = []
        for attr_row in cursor.fetchall():
            attr = {
                'type': attr_row[0],
                'subject': attr_row[1],
                'detail': attr_row[2],
                'date': attr_row[3]
            }
            attributes.append(attr)
        
        entity = {
            'e_id': e_id,
            'entity_name': entity_name,
            'attributes': attributes
        }
        entities.append(entity)
        
        entity_ref = {
            'e_id': e_id,
            'relationship_type': relationship_type
        }
        entity_references.append(entity_ref)
    
    conn.close()
    
    return {
        'group_id': group_id,
        'group_name': group_name,
        'description': description,
        'entities': entities,
        'entity_references': entity_references
    }


def search_groups(query: str) -> List[Dict]:
    """Search for groups by name or description."""
    init_database()
    conn = sqlite3.connect(_db_path)
    cursor = conn.cursor()
    
    results = []
    
    cursor.execute('''
        SELECT group_id, group_name, description
        FROM groups
        WHERE group_name LIKE ? OR description LIKE ?
        ORDER BY group_name
    ''', (f'%{query}%', f'%{query}%'))
    
    for row in cursor.fetchall():
        results.append({
            'group_id': row[0],
            'group_name': row[1],
            'description': row[2]
        })
    
    conn.close()
    return results