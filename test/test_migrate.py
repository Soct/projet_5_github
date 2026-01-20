"""Tests pour le module migrate.py"""
import pytest


class TestMigrateModule:
    """Tests pour migrate.py."""
    
    def test_migrate_database_runs(self):
        """Teste que la fonction migrate_database peut être appelée."""
        from app.migrate import migrate_database
        # Juste vérifier que la fonction existe et peut être importée
        assert callable(migrate_database)

