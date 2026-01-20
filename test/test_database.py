"""Tests pour le module database.py"""
import pytest
from app.database import wait_for_db, init_db, get_db


def test_wait_for_db_success():
    """Teste que wait_for_db se connecte correctement."""
    result = wait_for_db(max_retries=5, delay=0.1)
    assert result is True


def test_init_db():
    """Teste l'initialisation de la base de données."""
    # Ne devrait pas lever d'exception
    init_db()


def test_get_db():
    """Teste le générateur get_db."""
    db_gen = get_db()
    db = next(db_gen)
    assert db is not None
    
    # Fermer proprement
    try:
        next(db_gen)
    except StopIteration:
        pass  # Comportement attendu
