"""Tests pour le module seed.py"""
import pytest


class TestEmployeeSeeder:
    """Tests pour EmployeeSeeder."""
    
    def test_seeder_can_be_imported(self):
        """Teste que EmployeeSeeder peut être importé."""
        from app.seed import EmployeeSeeder
        assert EmployeeSeeder is not None
    
    def test_seeder_initialization_with_url(self):
        """Teste l'initialisation du seeder avec une URL."""
        from app.seed import EmployeeSeeder
        seeder = EmployeeSeeder(database_url="postgresql://test:test@localhost:5432/test")
        assert seeder is not None
        assert hasattr(seeder, 'database_url')
    
    def test_csv_path_attribute_exists(self):
        """Teste que l'attribut database_url existe."""
        from app.seed import EmployeeSeeder
        seeder = EmployeeSeeder(database_url="postgresql://test:test@localhost:5432/test")
        assert hasattr(seeder, 'database_url')
        assert seeder.database_url == "postgresql://test:test@localhost:5432/test"
    
    def test_batch_size_attribute_exists(self):
        """Teste que l'attribut batch_size existe."""
        from app.seed import EmployeeSeeder
        seeder = EmployeeSeeder(database_url="postgresql://test:test@localhost:5432/test")
        assert hasattr(seeder, 'batch_size')
        assert seeder.batch_size > 0

