import networkx as nx
from typing import List, Dict, Any
from core.database import SessionLocal, Entity, Link, Observation
from collections import defaultdict
import math

def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0 # km
    dLat = math.radians(lat2 - lat1)
    dLon = math.radians(lon2 - lon1)
    a = math.sin(dLat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dLon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def build_entity_graph() -> nx.Graph:
    session = SessionLocal()
    G = nx.Graph()
    try:
        # 1. Add Nodes
        entities = session.query(Entity).all()
        for e in entities:
            # Use value as the visual label, instead of just the ID
            G.add_node(e.id, type=e.type, value=e.value, source=e.source)
            
        # 2. Add Explicit SQL Links
        links = session.query(Link).all()
        for l in links:
            G.add_edge(l.left_entity_id, l.right_entity_id, type=l.link_type, confidence=l.confidence)

        # 3. Dynamic Automated Correlation (Heuristics Engine)
        observations = session.query(Observation).filter(Observation.latitude != None).all()
        obs_by_entity = defaultdict(list)
        for o in observations:
            if o.entity_id:
                obs_by_entity[o.entity_id].append(o)
                
        entity_ids = list(obs_by_entity.keys())
        for i in range(len(entity_ids)):
            for j in range(i + 1, len(entity_ids)):
                e1 = entity_ids[i]
                e2 = entity_ids[j]
                
                # Check for co-location (within 2 km)
                co_located = False
                for o1 in obs_by_entity[e1]:
                    for o2 in obs_by_entity[e2]:
                        dist = haversine(o1.latitude, o1.longitude, o2.latitude, o2.longitude)
                        if dist < 2.0:
                            G.add_edge(e1, e2, type="CO_LOCATED", confidence=round(1.0 - (dist/2.0), 2))
                            co_located = True
                            break
                    if co_located:
                        break
    finally:
        session.close()
    return G

def get_cytoscape_data(G: nx.Graph) -> List[Dict[str, Any]]:
    elements = []
    for node, data in G.nodes(data=True):
        elements.append({
            "data": {
                "id": str(node),
                "type": data.get("type", "unknown"),
                "value": data.get("value", ""),
                "source": data.get("source", "")
            }
        })
    for source, target, data in G.edges(data=True):
        elements.append({
            "data": {
                "source": str(source),
                "target": str(target),
                "type": data.get("type", "link"),
                "confidence": data.get("confidence", 1.0)
            }
        })
    return elements
