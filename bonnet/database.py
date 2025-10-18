import sqlite3
import os
import uuid
from contextlib import contextmanager
from typing import List, Dict, Optional, Tuple, Callable

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
            
            # Create indexes
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_entities_name ON entities(name)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_entities_node_id ON entities(node_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_attributes_type ON attributes(type)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_attributes_node_id ON attributes(node_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_nodes_table_record ON nodes(table_name, record_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_edges_from_node ON edges(from_node_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_edges_to_node ON edges(to_node_id)')
            
            # Create FTS5 virtual tables with porter tokenizer for stemming
            cursor.execute('''
                CREATE VIRTUAL TABLE IF NOT EXISTS nodes_fts USING fts5(
                    searchable_content,
                    content='nodes',
                    content_rowid='rowid',
                    tokenize='porter unicode61'
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
                    INSERT INTO nodes_fts(rowid, searchable_content) VALUES (new.rowid, new.searchable_content);
                END
            ''')
            
            cursor.execute('''
                CREATE TRIGGER IF NOT EXISTS nodes_ad AFTER DELETE ON nodes BEGIN
                    INSERT INTO nodes_fts(nodes_fts, rowid, searchable_content) VALUES('delete', old.rowid, old.searchable_content);
                END
            ''')
            
            cursor.execute('''
                CREATE TRIGGER IF NOT EXISTS nodes_au AFTER UPDATE ON nodes BEGIN
                    INSERT INTO nodes_fts(nodes_fts, rowid, searchable_content) VALUES('delete', old.rowid, old.searchable_content);
                    INSERT INTO nodes_fts(rowid, searchable_content) VALUES (new.rowid, new.searchable_content);
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
    return record_data.get('name', '')

@searchable_builder('attributes')
def build_attribute_searchable_content(record_data: dict) -> str:
    """Build searchable content for an attribute node."""
    content_parts = [record_data.get('type', '')]
    if record_data.get('subject'):
        content_parts.append(record_data['subject'])
    if record_data.get('detail'):
        content_parts.append(record_data['detail'])
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

def store_entity(e_id: str, entity_name: str) -> bool:
    """Store a master ENTITY record."""
    init_database()
    
    # First create the node
    entity_data = {
        'name': entity_name
    }
    node_id = create_node('entities', e_id, entity_data)
    
    with transaction() as cursor:
        # Check if entity already exists
        cursor.execute("SELECT id FROM entities WHERE id = ?", (e_id,))
        if cursor.fetchone():
            raise ValueError(f"Entity ID {e_id} already exists")
        
        # Insert entity record with node_id
        cursor.execute('''
            INSERT INTO entities (id, name, node_id)
            VALUES (?, ?, ?)
        ''', (e_id, entity_name, node_id))
    
    return True

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
    
    # Search nodes
    cursor.execute('''
        SELECT n.id, n.table_name, n.record_id, n.searchable_content
        FROM nodes n
        JOIN nodes_fts fts ON n.rowid = fts.rowid
        WHERE nodes_fts MATCH ?
    ''', (query,))
    
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
    ''', (query,))
    
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
            SELECT id, name, node_id
            FROM entities WHERE id = ?
        ''', (record_id,))
        
        row = cursor.fetchone()
        if row:
            return {
                'type': 'entity',
                'id': row[0],
                'name': row[1],
                'node_id': row[2]
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
    
    conn.close()
    return None

def get_entity_context(e_id: str) -> Dict:
    """Get all linked records for an entity ID."""
    init_database()
    conn = sqlite3.connect(_db_path)
    cursor = conn.cursor()
    
    # Get entity info
    cursor.execute('''
        SELECT name, node_id FROM entities WHERE id = ?
    ''', (e_id,))
    entity_row = cursor.fetchone()
    
    if not entity_row:
        raise ValueError(f"Entity ID {e_id} not found")
    
    entity_name, entity_node_id = entity_row
    
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


def get_entity_node_id(entity_id: str) -> str:
    """Get the node ID for an entity."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT node_id FROM entities WHERE id = ?", (entity_id,))
        row = cursor.fetchone()
        return row[0] if row else None