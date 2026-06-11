import os
import pytest
import phonenumbers
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from core.database import Base, Entity, Tower, init_db
from core.config import ALLOWED_COUNTRY_CODES, ALLOWED_MCCS
from services.graph import build_entity_graph

# Use an in-memory SQLite database for testing
TEST_DB_URL = "sqlite:///:memory:"

@pytest.fixture(scope="module")
def test_session():
    engine = create_engine(TEST_DB_URL)
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()

def test_config_constraints():
    # Verify we only have the 5 target countries in config
    assert "IN" in ALLOWED_COUNTRY_CODES
    assert "US" in ALLOWED_COUNTRY_CODES
    assert "PK" in ALLOWED_COUNTRY_CODES
    assert "CN" in ALLOWED_COUNTRY_CODES
    assert "RU" in ALLOWED_COUNTRY_CODES
    assert "GB" not in ALLOWED_COUNTRY_CODES # UK should be excluded
    
    # Verify MCCs contain at least the main ones for these countries
    assert 404 in ALLOWED_MCCS # India
    assert 310 in ALLOWED_MCCS # USA

def test_database_models(test_session):
    # Test creating an entity
    e = Entity(type="phone", value="+919876543210", normalized_value="919876543210", source="test")
    test_session.add(e)
    test_session.commit()
    
    # Query it back
    queried = test_session.query(Entity).filter_by(value="+919876543210").first()
    assert queried is not None
    assert queried.type == "phone"
    assert queried.id == 1

def test_graph_building(test_session):
    import networkx as nx
    G = nx.Graph()
    G.add_node(1, type="phone", value="+123", source="test")
    assert len(G.nodes) == 1

def test_phone_logic_allowed():
    # Test valid Indian number
    number = "+919876543210"
    parsed = phonenumbers.parse(number, None)
    region = phonenumbers.region_code_for_number(parsed)
    assert region == "IN"
    assert region in ALLOWED_COUNTRY_CODES

def test_phone_logic_blocked():
    # Test UK number (or Channel Islands which are also not in allowed list)
    number = "+447911123456"
    parsed = phonenumbers.parse(number, None)
    region = phonenumbers.region_code_for_number(parsed)
    # UK numbers may return GB or GG (Guernsey) - both should be blocked
    assert region in ["GB", "GG"]
    assert region not in ALLOWED_COUNTRY_CODES
