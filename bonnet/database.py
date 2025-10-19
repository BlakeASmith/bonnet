import sqlite3
import os
import uuid
from contextlib import contextmanager
from typing import List, Dict, Optional, Tuple, Callable
from ._record_types import TYPE_TO_TABLE

# Global database connection
_config_dir = os.path.expanduser("~/.config/bonnet")
os.makedirs(_config_dir, exist_ok=True)
_db_path = os.path.join(_config_dir, "bonnet.db")
_initialized = False

# Registry for searchable content builders
SEARCHABLE_BUILDERS: Dict[str, Callable[[Dict], str]] = {}

@contextmanager
def transaction(conn: sqlite3.Connection = None, rollback: bool = True):
    """Context manager for database transactions"""
    should_close = False
    if conn is None:
        conn = sqlite3.connect(_db_path)
        should_close = True
    try:
        yield conn.cursor()
        conn.commit()
    except Exception:
        if rollback:
            conn.rollback()
        raise
    finally:
        if should_close:
            conn.close()

def searchable_builder(table_name: str):
    """Decorator to register searchable content builders for tables."""
    def decorator(func):
        SEARCHABLE_BUILDERS[table_name] = func
        return func
    return decorator

def init_database():
    """Initialize the database with the new knowledge graph schema."""
    global _initialized
    if _initialized:
        return
        
    conn = sqlite3.connect(_db_path)
    try:
        with transaction(conn, rollback=False) as cursor:
            # Create entities table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS entities (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    short_name TEXT,
                    node_id TEXT NOT NULL,
                    FOREIGN KEY (node_id) REFERENCES nodes(id)
                )
            ''')
            
            # Create attributes table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS attributes (
                    id TEXT PRIMARY KEY,
                    type TEXT NOT NULL,
                    subject TEXT,
                    detail TEXT,
                    node_id TEXT NOT NULL,
                    FOREIGN KEY (node_id) REFERENCES nodes(id)
                )
            ''')
            
            # Create files table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS files (
                    id TEXT PRIMARY KEY,
                    file_path TEXT NOT NULL,
                    description TEXT,
                    content TEXT,
                    include_content BOOLEAN DEFAULT 0,
                    node_id TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (node_id) REFERENCES nodes(id)
                )
            ''')
            
            # Create nodes table for knowledge graph
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS nodes (
                    id TEXT PRIMARY KEY,
                    table_name TEXT NOT NULL,
                    record_id TEXT NOT NULL,
                    searchable_content TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create edges table for relationships
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS edges (
                    id TEXT PRIMARY KEY,
                    from_node_id TEXT NOT NULL,
                    to_node_id TEXT NOT NULL,
                    edge_type TEXT,
                    searchable_content TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (from_node_id) REFERENCES nodes(id),
                    FOREIGN KEY (to_node_id) REFERENCES nodes(id)
                )
            ''')
            
            # Create id_counters table to track ID numbers for each prefix
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS id_counters (
                    prefix TEXT PRIMARY KEY,
                    next_number INTEGER NOT NULL DEFAULT 1
                )
            ''')
            
            # Create indexes
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_entities_name ON entities(name)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_entities_node_id ON entities(node_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_attributes_type ON attributes(type)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_attributes_node_id ON attributes(node_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_files_path ON files(file_path)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_files_node_id ON files(node_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_nodes_table_record ON nodes(table_name, record_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_edges_from_node ON edges(from_node_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_edges_to_node ON edges(to_node_id)')
            
            # Create FTS5 virtual tables with porter tokenizer for stemming
            cursor.execute('''
                CREATE VIRTUAL TABLE IF NOT EXISTS nodes_fts USING fts5(
                    record_id,
                    searchable_content,
                    content='nodes',
                    content_rowid='rowid'
                )
            ''')
            
            cursor.execute('''
                CREATE VIRTUAL TABLE IF NOT EXISTS edges_fts USING fts5(
                    searchable_content,
                    content='edges',
                    content_rowid='rowid',
                    tokenize='porter unicode61'
                )
            ''')
            
            # Create triggers to keep FTS tables in sync
            # Nodes FTS triggers
            cursor.execute('''
                CREATE TRIGGER IF NOT EXISTS nodes_ai AFTER INSERT ON nodes BEGIN
                    INSERT INTO nodes_fts(rowid, record_id, searchable_content) VALUES (new.rowid, new.record_id, new.searchable_content);
                END
            ''')
            
            cursor.execute('''
                CREATE TRIGGER IF NOT EXISTS nodes_ad AFTER DELETE ON nodes BEGIN
                    INSERT INTO nodes_fts(nodes_fts, rowid, record_id, searchable_content) VALUES('delete', old.rowid, old.record_id, old.searchable_content);
                END
            ''')
            
            cursor.execute('''
                CREATE TRIGGER IF NOT EXISTS nodes_au AFTER UPDATE ON nodes BEGIN
                    INSERT INTO nodes_fts(nodes_fts, rowid, record_id, searchable_content) VALUES('delete', old.rowid, old.record_id, old.searchable_content);
                    INSERT INTO nodes_fts(rowid, record_id, searchable_content) VALUES (new.rowid, new.record_id, new.searchable_content);
                END
            ''')
            
            # Edges FTS triggers
            cursor.execute('''
                CREATE TRIGGER IF NOT EXISTS edges_ai AFTER INSERT ON edges BEGIN
                    INSERT INTO edges_fts(rowid, searchable_content) VALUES (new.rowid, new.searchable_content);
                END
            ''')
            
            cursor.execute('''
                CREATE TRIGGER IF NOT EXISTS edges_ad AFTER DELETE ON edges BEGIN
                    INSERT INTO edges_fts(edges_fts, rowid, searchable_content) VALUES('delete', old.rowid, old.searchable_content);
                END
            ''')
            
            cursor.execute('''
                CREATE TRIGGER IF NOT EXISTS edges_au AFTER UPDATE ON edges BEGIN
                    INSERT INTO edges_fts(edges_fts, rowid, searchable_content) VALUES('delete', old.rowid, old.searchable_content);
                    INSERT INTO edges_fts(rowid, searchable_content) VALUES (new.rowid, new.searchable_content);
                END
            ''')
    finally:
        conn.close()
    
    _initialized = True

@searchable_builder('entities')
def build_entity_searchable_content(record_data: dict) -> str:
    """Build searchable content for an entity node."""
    content_parts = [record_data.get('name', '')]
    if record_data.get('short_name'):
        content_parts.append(record_data['short_name'])
    return ' '.join(content_parts)

@searchable_builder('attributes')
def build_attribute_searchable_content(record_data: dict) -> str:
    """Build searchable content for an attribute node."""
    content_parts = [record_data.get('type', '')]
    if record_data.get('subject'):
        content_parts.append(record_data['subject'])
    if record_data.get('detail'):
        content_parts.append(record_data['detail'])
    return ' '.join(content_parts)

@searchable_builder('files')
def build_file_searchable_content(record_data: dict) -> str:
    """Build searchable content for a file node."""
    content_parts = [record_data.get('file_path', '')]
    if record_data.get('description'):
        content_parts.append(record_data['description'])
    return ' '.join(content_parts)

def create_node(table_name: str, record_id: str, record_data: dict) -> str:
    """Create a node for any table record using registered builder."""
    if table_name not in SEARCHABLE_BUILDERS:
        raise ValueError(f"No searchable builder registered for table: {table_name}")
    
    builder = SEARCHABLE_BUILDERS[table_name]
    searchable_content = builder(record_data)
    
    # Create node record
    node_id = f"N-{uuid.uuid4().hex[:8]}"
    
    with transaction() as cursor:
        cursor.execute('''
            INSERT INTO nodes (id, table_name, record_id, searchable_content)
            VALUES (?, ?, ?, ?)
        ''', (node_id, table_name, record_id, searchable_content))
    
    return node_id

def store_entity(e_id: str, entity_name: str, short_name: str = None) -> None:
    """Store a master ENTITY record."""
    init_database()
    
    # First create the node
    entity_data = {
        'name': entity_name,
        'short_name': short_name
    }
    node_id = create_node('entities', e_id, entity_data)
    
    with transaction() as cursor:
        # Check if entity already exists
        cursor.execute("SELECT id FROM entities WHERE id = ?", (e_id,))
        if cursor.fetchone():
            raise ValueError(f"Entity ID {e_id} already exists")
        
        # Insert entity record with node_id
        cursor.execute('''
            INSERT INTO entities (id, name, short_name, node_id)
            VALUES (?, ?, ?, ?)
        ''', (e_id, entity_name, short_name, node_id))

def entity_exists(e_id: str) -> bool:
    """Check if an entity with the given ID already exists."""
    init_database()
    
    with transaction() as cursor:
        cursor.execute("SELECT id FROM entities WHERE id = ?", (e_id,))
        return cursor.fetchone() is not None

def get_next_id_number(prefix: str) -> int:
    """Get the next available ID number for a given prefix."""
    init_database()
    
    with transaction() as cursor:
        # Get or create counter record for this prefix
        cursor.execute("SELECT next_number FROM id_counters WHERE prefix = ?", (prefix,))
        row = cursor.fetchone()
        
        if row:
            # Update existing counter
            next_number = row[0]
            cursor.execute("UPDATE id_counters SET next_number = ? WHERE prefix = ?", (next_number + 1, prefix))
        else:
            # Create new counter starting at 1
            next_number = 1
            cursor.execute("INSERT INTO id_counters (prefix, next_number) VALUES (?, ?)", (prefix, 2))
        
        return next_number

def store_attribute(attr_id: str, attr_type: str, subject: str, detail: str) -> bool:
    """Store an attribute (fact, task, rule, ref) and link it to the entity."""
    init_database()
    
    # Generate unique attribute ID
    unique_attr_id = f"{attr_id}-{uuid.uuid4().hex[:8]}"
    
    # First create the node
    attribute_data = {
        'type': attr_type,
        'subject': subject,
        'detail': detail
    }
    attribute_node_id = create_node('attributes', unique_attr_id, attribute_data)
    
    with transaction() as cursor:
        # Insert attribute record with node_id
        cursor.execute('''
            INSERT INTO attributes (id, type, subject, detail, node_id)
            VALUES (?, ?, ?, ?, ?)
        ''', (unique_attr_id, attr_type, subject, detail, attribute_node_id))
        
        # Find the entity node that this attribute is about
        cursor.execute('''
            SELECT node_id FROM entities WHERE id = ?
        ''', (attr_id,))
        
        entity_node_row = cursor.fetchone()
        if entity_node_row:
            entity_node_id = entity_node_row[0]
            # Create an edge from entity to attribute within the same transaction
            edge_id = f"E-{uuid.uuid4().hex[:8]}"
            cursor.execute('''
                INSERT INTO edges (id, from_node_id, to_node_id, edge_type, searchable_content)
                VALUES (?, ?, ?, ?, ?)
            ''', (edge_id, entity_node_id, attribute_node_id, "has_attribute", f"{attr_type}: {subject}"))
    
    return True

def search_nodes(query: str) -> List[Dict]:
    """Search for nodes using FTS across both nodes and edges."""
    init_database()
    conn = sqlite3.connect(_db_path)
    cursor = conn.cursor()
    
    results = []
    
    # Escape the query for FTS
    escaped_query = f'"{query}"'
    
    # Search nodes
    cursor.execute('''
        SELECT n.id, n.table_name, n.record_id, n.searchable_content
        FROM nodes n
        JOIN nodes_fts fts ON n.rowid = fts.rowid
        WHERE nodes_fts MATCH ?
    ''', (escaped_query,))
    
    for row in cursor.fetchall():
        results.append({
            'node_id': row[0],
            'table_name': row[1],
            'record_id': row[2],
            'searchable_content': row[3],
            'source': 'node'
        })
    
    # Search edges
    cursor.execute('''
        SELECT e.id, e.from_node_id, e.to_node_id, e.edge_type, e.searchable_content
        FROM edges e
        JOIN edges_fts fts ON e.rowid = fts.rowid
        WHERE edges_fts MATCH ?
    ''', (escaped_query,))
    
    for row in cursor.fetchall():
        results.append({
            'edge_id': row[0],
            'from_node_id': row[1],
            'to_node_id': row[2],
            'edge_type': row[3],
            'searchable_content': row[4],
            'source': 'edge'
        })
    
    conn.close()
    return results

def get_related_nodes(node_id: str, max_depth: int = 1) -> List[Dict]:
    """Get nodes related to the given node through graph traversal."""
    init_database()
    conn = sqlite3.connect(_db_path)
    cursor = conn.cursor()
    
    related_nodes = set()
    visited = set()
    current_level = {node_id}
    
    for depth in range(max_depth):
        next_level = set()
        
        for current_node in current_level:
            if current_node in visited:
                continue
            visited.add(current_node)
            
            # Find outgoing edges
            cursor.execute('''
                SELECT to_node_id FROM edges WHERE from_node_id = ?
            ''', (current_node,))
            
            for (to_node,) in cursor.fetchall():
                related_nodes.add(to_node)
                next_level.add(to_node)
            
            # Find incoming edges
            cursor.execute('''
                SELECT from_node_id FROM edges WHERE to_node_id = ?
            ''', (current_node,))
            
            for (from_node,) in cursor.fetchall():
                related_nodes.add(from_node)
                next_level.add(from_node)
        
        current_level = next_level
    
    # Get details for related nodes
    if not related_nodes:
        conn.close()
        return []
    
    placeholders = ','.join(['?' for _ in related_nodes])
    cursor.execute(f'''
        SELECT id, table_name, record_id, searchable_content
        FROM nodes
        WHERE id IN ({placeholders})
    ''', list(related_nodes))
    
    results = []
    for row in cursor.fetchall():
        results.append({
            'node_id': row[0],
            'table_name': row[1],
            'record_id': row[2],
            'searchable_content': row[3]
        })
    
    conn.close()
    return results

def create_edge(from_node_id: str, to_node_id: str, edge_type: str, searchable_content: str = "") -> str:
    """Create an edge between two nodes."""
    init_database()
    
    edge_id = f"E-{uuid.uuid4().hex[:8]}"
    
    with transaction() as cursor:
        cursor.execute('''
            INSERT INTO edges (id, from_node_id, to_node_id, edge_type, searchable_content)
            VALUES (?, ?, ?, ?, ?)
        ''', (edge_id, from_node_id, to_node_id, edge_type, searchable_content))
    
    return edge_id

def get_record_by_node(node_id: str) -> Dict:
    """Get the actual record for a given node."""
    init_database()
    conn = sqlite3.connect(_db_path)
    cursor = conn.cursor()
    
    # Get node info
    cursor.execute('''
        SELECT table_name, record_id FROM nodes WHERE id = ?
    ''', (node_id,))
    
    node_row = cursor.fetchone()
    if not node_row:
        conn.close()
        return None
    
    table_name, record_id = node_row
    
    # Get record from appropriate table
    if table_name == 'entities':
        cursor.execute('''
            SELECT id, name, short_name, node_id
            FROM entities WHERE id = ?
        ''', (record_id,))
        
        row = cursor.fetchone()
        if row:
            return {
                'type': 'entity',
                'id': row[0],
                'name': row[1],
                'short_name': row[2],
                'node_id': row[3]
            }
    
    elif table_name == 'attributes':
        cursor.execute('''
            SELECT id, type, subject, detail, node_id
            FROM attributes WHERE id = ?
        ''', (record_id,))
        
        row = cursor.fetchone()
        if row:
            return {
                'type': 'attribute',
                'id': row[0],
                'attr_type': row[1],
                'subject': row[2],
                'detail': row[3],
                'node_id': row[4]
            }
    
    elif table_name == 'files':
        cursor.execute('''
            SELECT id, file_path, description, content, include_content, node_id
            FROM files WHERE id = ?
        ''', (record_id,))
        
        row = cursor.fetchone()
        if row:
            return {
                'type': 'file',
                'id': row[0],
                'file_path': row[1],
                'description': row[2],
                'content': row[3],
                'include_content': row[4],
                'node_id': row[5]
            }
    
    conn.close()
    return None

def get_entity_context(e_id: str) -> Dict:
    """Get all linked records for an entity ID."""
    init_database()
    conn = sqlite3.connect(_db_path)
    cursor = conn.cursor()
    
    # Get entity info
    cursor.execute('''
        SELECT name, short_name, node_id FROM entities WHERE id = ?
    ''', (e_id,))
    entity_row = cursor.fetchone()
    
    if not entity_row:
        raise ValueError(f"Entity ID {e_id} not found")
    
    entity_name, entity_short_name, entity_node_id = entity_row
    
    # Get all attributes (relationships are now handled via graph edges)
    cursor.execute('''
        SELECT id, type, subject, detail, node_id FROM attributes 
        ORDER BY type, subject
    ''')
    
    attributes = []
    for row in cursor.fetchall():
        attr = {
            'id': row[0],
            'type': row[1],
            'subject': row[2],
            'detail': row[3],
            'node_id': row[4]
        }
        attributes.append(attr)
    
    conn.close()
    
    return {
        'e_id': e_id,
        'entity_name': entity_name,
        'entity_short_name': entity_short_name,
        'entity_node_id': entity_node_id,
        'attributes': attributes
    }

def search_knowledge_graph(query: str, include_related: bool = True, max_depth: int = 1) -> Dict:
    """Search the knowledge graph using FTS and optionally include related nodes."""
    # First, search for matching nodes and edges
    search_results = search_nodes(query)
    
    if not include_related:
        return {
            'search_results': search_results,
            'related_records': []
        }
    
    # Get related nodes for each found node
    all_related = set()
    for result in search_results:
        if result['source'] == 'node':
            related = get_related_nodes(result['node_id'], max_depth)
            for rel in related:
                all_related.add(rel['node_id'])
        elif result['source'] == 'edge':
            # For edges, get related nodes from both ends
            related_from = get_related_nodes(result['from_node_id'], max_depth)
            related_to = get_related_nodes(result['to_node_id'], max_depth)
            for rel in related_from + related_to:
                all_related.add(rel['node_id'])
    
    # Get details for all related nodes
    related_records = []
    for node_id in all_related:
        record = get_record_by_node(node_id)
        if record:
            related_records.append(record)
    
    return {
        'search_results': search_results,
        'related_records': related_records
    }


def get_graph_structure(query: str, include_related: bool = True, max_depth: int = 1) -> List[Dict]:
    """Get the knowledge graph structure starting from search results."""
    # First, search for matching nodes and edges
    search_results = search_nodes(query)
    
    if not search_results:
        return []
    
    # Build graph structure starting from search results
    graph_nodes = []
    processed_nodes = set()
    
    def build_node_tree(node_id: str, depth: int = 0) -> Dict:
        if depth > max_depth or node_id in processed_nodes:
            return None
            
        processed_nodes.add(node_id)
        
        # Get the node record
        node_data = get_node_by_id(node_id)
        if not node_data:
            return None
            
        # Get the actual record (entity or attribute)
        record_data = get_record_by_node(node_id)
        if not record_data:
            return None
            
        # Get edges from this node
        edges = get_edges_from_node(node_id)
        
        # Build the node structure
        node_structure = {
            'node': node_data,
            'record': record_data,
            'edges': edges,
            'children': []
        }
        
        # Recursively build children if we should include related nodes
        if include_related and depth < max_depth:
            for edge in edges:
                child_node_id = edge['to_node_id']
                child_node = build_node_tree(child_node_id, depth + 1)
                if child_node:
                    node_structure['children'].append(child_node)
        
        return node_structure
    
    # Build tree for each search result
    for result in search_results:
        if result['source'] == 'node':
            node_tree = build_node_tree(result['node_id'])
            if node_tree:
                graph_nodes.append(node_tree)
        elif result['source'] == 'edge':
            # For edges, start from both ends
            from_tree = build_node_tree(result['from_node_id'])
            to_tree = build_node_tree(result['to_node_id'])
            if from_tree:
                graph_nodes.append(from_tree)
            if to_tree and to_tree != from_tree:
                graph_nodes.append(to_tree)
    
    return graph_nodes


def get_connection():
    """Get a database connection."""
    return sqlite3.connect(_db_path)

def get_node_by_id(node_id: str) -> Optional[Dict]:
    """Get a node by its ID."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM nodes WHERE id = ?", (node_id,))
        row = cursor.fetchone()
        if row:
            return {
                'id': row[0],
                'table_name': row[1],
                'record_id': row[2],
                'searchable_content': row[3]
            }
        return None


def get_edges_from_node(node_id: str) -> List[Dict]:
    """Get all edges from a specific node."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM edges WHERE from_node_id = ?", (node_id,))
        rows = cursor.fetchall()
        return [{
            'id': row[0],
            'from_node_id': row[1],
            'to_node_id': row[2],
            'edge_type': row[3],
            'searchable_content': row[4]
        } for row in rows]


def get_edges_to_node(node_id: str) -> List[Dict]:
    """Get all edges to a specific node."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM edges WHERE to_node_id = ?", (node_id,))
        rows = cursor.fetchall()
        return [{
            'id': row[0],
            'from_node_id': row[1],
            'to_node_id': row[2],
            'edge_type': row[3],
            'searchable_content': row[4]
        } for row in rows]


def get_entity_node_id(entity_id: str) -> str:
    """Get the node ID for an entity."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT node_id FROM entities WHERE id = ?", (entity_id,))
        row = cursor.fetchone()
        return row[0] if row else None

def store_file(file_id: str, file_path: str, description: str = None, content: str = None, include_content: bool = False) -> bool:
    """Store a file record."""
    init_database()
    
    # First create the node
    file_data = {
        'file_path': file_path,
        'description': description or '',
        'content': content or '',
        'include_content': include_content
    }
    node_id = create_node('files', file_id, file_data)
    
    with transaction() as cursor:
        # Check if file already exists
        cursor.execute("SELECT id FROM files WHERE id = ?", (file_id,))
        if cursor.fetchone():
            raise ValueError(f"File ID {file_id} already exists")
        
        # Insert file record with node_id
        cursor.execute('''
            INSERT INTO files (id, file_path, description, content, include_content, node_id)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (file_id, file_path, description, content, include_content, node_id))
    
    return True

def get_node_id_by_record_id(table_name: str, record_id: str) -> str:
    """Get the node ID for any record by table name and record ID."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(f"SELECT node_id FROM {table_name} WHERE id = ?", (record_id,))
        row = cursor.fetchone()
        return row[0] if row else None

def link_nodes(from_table: str, from_record_id: str, to_table: str, to_record_id: str, edge_type: str = "references", searchable_content: str = None) -> str:
    """Link any node type to any other node type."""
    init_database()
    
    # Get source node ID
    from_node_id = get_node_id_by_record_id(from_table, from_record_id)
    if not from_node_id:
        raise ValueError(f"Record {from_record_id} not found in table {from_table}")
    
    # Get target node ID
    to_node_id = get_node_id_by_record_id(to_table, to_record_id)
    if not to_node_id:
        raise ValueError(f"Record {to_record_id} not found in table {to_table}")
    
    # Create searchable content if not provided
    if not searchable_content:
        searchable_content = f"{from_table} {from_record_id} {edge_type} {to_table} {to_record_id}"
    
    # Create edge between nodes
    edge_id = create_edge(from_node_id, to_node_id, edge_type, searchable_content)
    
    return edge_id


def get_file_node_id(file_id: str) -> str:
    """Get the node ID for a file."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT node_id FROM files WHERE id = ?", (file_id,))
        row = cursor.fetchone()
        return row[0] if row else None


def get_file_by_id(file_id: str) -> Optional[Dict]:
    """
    Get a file record by its ID.
    
    Args:
        file_id: The file ID
        
    Returns:
        Dictionary containing file data (id, file_path, description) or None if not found
    """
    init_database()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, file_path, description, node_id, created_at
            FROM files WHERE id = ?
        ''', (file_id,))
        row = cursor.fetchone()
        if row:
            return {
                'id': row[0],
                'file_path': row[1],
                'description': row[2],
                'node_id': row[3],
                'created_at': row[4]
            }
        return None




def search_records(query: str) -> List[Dict]:
    """
    Search for records by content or ID. Returns all matches.
    
    Args:
        query: Search query string or record ID
        
    Returns:
        List of matching records
    """
    init_database()
    conn = sqlite3.connect(_db_path)
    cursor = conn.cursor()
    
    results = []
    
    # Handle empty query - return recent records instead
    if not query or not query.strip():
        conn.close()
        return get_recent_records(10)
    
    # Escape FTS5 special characters to prevent syntax errors
    # FTS5 special characters: " * : ( ) [ ] { } ^ $ . + ? | \ /
    fts_query = query.replace('"', '""')  # Escape quotes
    
    try:
        # Search using FTS on nodes table - this will match both IDs and content
        cursor.execute('''
            SELECT n.id, n.table_name, n.record_id, n.searchable_content
            FROM nodes n
            JOIN nodes_fts fts ON n.rowid = fts.rowid
            WHERE nodes_fts MATCH ?
        ''', (fts_query,))
        
        for row in cursor.fetchall():
            node_id, table_name, record_id, searchable_content = row
            results.extend(_get_record_data(cursor, table_name, record_id, searchable_content))
    except sqlite3.OperationalError:
        # If FTS5 query fails, fall back to LIKE search
        cursor.execute('''
            SELECT id, table_name, record_id, searchable_content
            FROM nodes
            WHERE searchable_content LIKE ? OR record_id LIKE ?
            LIMIT 20
        ''', (f'%{query}%', f'%{query}%'))
        
        for row in cursor.fetchall():
            node_id, table_name, record_id, searchable_content = row
            results.extend(_get_record_data(cursor, table_name, record_id, searchable_content))
    
    conn.close()
    return results


def get_distinct_attribute_types() -> List[str]:
    """
    Get all distinct attribute types from the database.
    
    Returns:
        List of distinct attribute types
    """
    init_database()
    conn = sqlite3.connect(_db_path)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT DISTINCT attr_type FROM attributes 
        WHERE attr_type IS NOT NULL AND attr_type != ''
        ORDER BY attr_type
    ''')
    
    results = [row[0] for row in cursor.fetchall()]
    conn.close()
    return results


def get_distinct_attribute_subjects() -> List[str]:
    """
    Get all distinct attribute subjects from the database.
    
    Returns:
        List of distinct attribute subjects
    """
    init_database()
    conn = sqlite3.connect(_db_path)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT DISTINCT subject FROM attributes 
        WHERE subject IS NOT NULL AND subject != ''
        ORDER BY subject
    ''')
    
    results = [row[0] for row in cursor.fetchall()]
    conn.close()
    return results


def get_distinct_edge_types() -> List[str]:
    """
    Get all distinct edge types from the database.
    
    Returns:
        List of distinct edge types
    """
    init_database()
    conn = sqlite3.connect(_db_path)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT DISTINCT edge_type FROM edges 
        WHERE edge_type IS NOT NULL AND edge_type != ''
        ORDER BY edge_type
    ''')
    
    results = [row[0] for row in cursor.fetchall()]
    conn.close()
    return results


def get_recent_records(limit: int = 10) -> List[Dict]:
    """
    Get recent records for completion suggestions.
    
    Args:
        limit: Maximum number of records to return
        
    Returns:
        List of recent records
    """
    init_database()
    conn = sqlite3.connect(_db_path)
    cursor = conn.cursor()
    
    # Get recent records from all tables
    cursor.execute('''
        SELECT n.table_name, n.record_id, n.searchable_content, n.created_at
        FROM nodes n
        ORDER BY n.created_at DESC
        LIMIT ?
    ''', (limit,))
    
    results = []
    for row in cursor.fetchall():
        table_name, record_id, searchable_content, created_at = row
        results.extend(_get_record_data(cursor, table_name, record_id, searchable_content))
    
    conn.close()
    return results


def search_records_by_type(record_type: str, query: str = "", limit: int = 10) -> List[Dict]:
    """
    Search for records of a specific type.
    
    Args:
        record_type: Type of record to search for ('entity', 'attribute', 'file')
        query: Search query string (optional)
        limit: Maximum number of results
        
    Returns:
        List of matching records
    """
    init_database()
    conn = sqlite3.connect(_db_path)
    cursor = conn.cursor()
    
    table_name = TYPE_TO_TABLE.get(record_type)
    
    if not table_name:
        return []
    
    if query:
        # Search with query
        cursor.execute(f'''
            SELECT n.id, n.table_name, n.record_id, n.searchable_content
            FROM nodes n
            JOIN nodes_fts fts ON n.rowid = fts.rowid
            WHERE n.table_name = ? AND nodes_fts MATCH ?
            ORDER BY n.created_at DESC
            LIMIT ?
        ''', (table_name, query, limit))
    else:
        # Get recent records of this type
        cursor.execute(f'''
            SELECT n.id, n.table_name, n.record_id, n.searchable_content
            FROM nodes n
            WHERE n.table_name = ?
            ORDER BY n.created_at DESC
            LIMIT ?
        ''', (table_name, limit))
    
    results = []
    for row in cursor.fetchall():
        node_id, table_name, record_id, searchable_content = row
        results.extend(_get_record_data(cursor, table_name, record_id, searchable_content))
    
    conn.close()
    return results

def _get_record_data(cursor, table_name: str, record_id: str, searchable_content: str) -> List[Dict]:
    """Helper function to get record data based on table name."""
    results = []
    
    if table_name == 'entities':
        cursor.execute('''
            SELECT id, name, short_name FROM entities WHERE id = ?
        ''', (record_id,))
        record_row = cursor.fetchone()
        if record_row:
            display = record_row[1]  # name
            if record_row[2]:  # short_name
                display += f" ({record_row[2]})"
            results.append({
                'type': 'entity',
                'id': record_row[0],
                'name': record_row[1],
                'short_name': record_row[2],
                'display': display,
                'searchable_content': searchable_content
            })
    
    elif table_name == 'attributes':
        cursor.execute('''
            SELECT id, type, subject, detail FROM attributes WHERE id = ?
        ''', (record_id,))
        record_row = cursor.fetchone()
        if record_row:
            display = f"{record_row[1]}: {record_row[2]}" if record_row[2] else record_row[1]
            if record_row[3]:  # detail
                display += f" - {record_row[3]}"
            
            results.append({
                'type': 'attribute',
                'id': record_row[0],
                'name': display,
                'display': display,
                'searchable_content': searchable_content
            })
    
    elif table_name == 'files':
        cursor.execute('''
            SELECT id, file_path, description, content, include_content FROM files WHERE id = ?
        ''', (record_id,))
        record_row = cursor.fetchone()
        if record_row:
            display = record_row[1]  # file_path
            if record_row[2]:  # description
                display += f" ({record_row[2]})"
            
            results.append({
                'type': 'file',
                'id': record_row[0],
                'name': display,
                'display': display,
                'searchable_content': searchable_content
            })
    
    return results

def _get_short_name_tables() -> List[str]:
    """Helper function to get tables that have a `short_name` field."""
    init_database()
    conn = sqlite3.connect(_db_path)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT name FROM sqlite_master WHERE type = 'table' AND sql LIKE '%short_name%'
    ''')
    return [row[0] for row in cursor.fetchall()]

def get_short_names(table: str) -> List[str]:
    """Helper function to get short names from a table."""
    init_database()
    conn = sqlite3.connect(_db_path)
    cursor = conn.cursor()
    
    # Validate table name to prevent SQL injection (whitelist approach)
    valid_tables = ['entities', 'attributes', 'files']
    if table not in valid_tables:
        conn.close()
        return []
    
    # Use string formatting for table name (safe after validation)
    cursor.execute(f'''
        SELECT DISTINCT short_name FROM {table}
        WHERE short_name IS NOT NULL AND short_name != ''
    ''')
    
    results = [row[0] for row in cursor.fetchall()]
    conn.close()
    return results

def get_all_short_names() -> List[str]:
    """Helper function to get all short names from all tables."""
    tables = _get_short_name_tables()
    all_short_names = []
    
    for table in tables:
        short_names = get_short_names(table)
        all_short_names.extend(short_names)
    
    # Return unique short names
    return list(set(all_short_names))
