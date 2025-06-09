# backend/tests/unit/repositories/test_repositories.py
"""
Repository Pattern Tests

Comprehensive tests for all repository implementations including base repository,
specific repositories, and the Unit of Work pattern.
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.database.models import (
    LockedPicklist,
    AllianceSelection,
    Alliance,
    TeamSelectionStatus,
    ArchivedEvent,
    SheetConfiguration,
)
from app.repositories import (
    BaseRepository,
    PicklistRepository,
    AllianceRepository,
    EventRepository,
    TeamRepository,
    UnitOfWork,
    get_unit_of_work,
)


class TestBaseRepository:
    """Test the base repository functionality."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        return Mock(spec=Session)

    @pytest.fixture
    def base_repo(self, mock_db):
        """Create a concrete implementation of BaseRepository for testing."""
        class TestRepository(BaseRepository[LockedPicklist]):
            def get_domain_specific_methods(self):
                return {}
        
        return TestRepository(LockedPicklist, mock_db)

    def test_get_by_id(self, base_repo, mock_db):
        """Test getting a record by ID."""
        # Setup
        mock_result = Mock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_result
        
        # Execute
        result = base_repo.get(1)
        
        # Verify
        assert result == mock_result
        mock_db.query.assert_called_once_with(LockedPicklist)

    def test_get_by_kwargs(self, base_repo, mock_db):
        """Test getting a record by arbitrary field values."""
        # Setup
        mock_result = Mock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_result
        
        # Execute
        result = base_repo.get_by(team_number=1234, event_key="2025demo")
        
        # Verify
        assert result == mock_result
        mock_db.query.assert_called_once_with(LockedPicklist)

    def test_get_all_with_filters(self, base_repo, mock_db):
        """Test getting all records with filters and pagination."""
        # Setup
        mock_results = [Mock(), Mock()]
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value.all.return_value = mock_results
        
        # Execute
        result = base_repo.get_all(skip=10, limit=20, team_number=1234)
        
        # Verify
        assert result == mock_results
        mock_query.offset.assert_called_once_with(10)
        mock_query.limit.assert_called_once_with(20)

    def test_count_with_filters(self, base_repo, mock_db):
        """Test counting records with filters."""
        # Setup
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 42
        
        # Execute
        result = base_repo.count(year=2025)
        
        # Verify
        assert result == 42
        mock_query.count.assert_called_once()

    def test_create_with_dict(self, base_repo, mock_db):
        """Test creating a record with dictionary data."""
        # Setup
        data = {"team_number": 1234, "event_key": "2025demo"}
        mock_obj = Mock()
        
        with patch.object(LockedPicklist, '__new__', return_value=mock_obj):
            # Execute
            result = base_repo.create(data)
            
            # Verify
            mock_db.add.assert_called_once_with(mock_obj)
            mock_db.flush.assert_called_once()
            mock_db.refresh.assert_called_once_with(mock_obj)

    def test_create_with_pydantic_model(self, base_repo, mock_db):
        """Test creating a record with Pydantic model."""
        # Setup
        mock_model = Mock()
        mock_model.model_dump.return_value = {"team_number": 1234}
        mock_obj = Mock()
        
        with patch.object(LockedPicklist, '__new__', return_value=mock_obj):
            # Execute
            result = base_repo.create(mock_model)
            
            # Verify
            mock_model.model_dump.assert_called_once_with(exclude_unset=True)
            mock_db.add.assert_called_once_with(mock_obj)

    def test_update_record(self, base_repo, mock_db):
        """Test updating an existing record."""
        # Setup
        db_obj = Mock()
        db_obj.team_number = 1234
        update_data = {"team_number": 5678}
        
        # Execute
        result = base_repo.update(db_obj, update_data)
        
        # Verify
        assert db_obj.team_number == 5678
        mock_db.flush.assert_called_once()
        mock_db.refresh.assert_called_once_with(db_obj)

    def test_delete_by_id(self, base_repo, mock_db):
        """Test deleting a record by ID."""
        # Setup
        mock_obj = Mock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_obj
        
        # Execute
        result = base_repo.delete(1)
        
        # Verify
        assert result is True
        mock_db.delete.assert_called_once_with(mock_obj)
        mock_db.flush.assert_called_once()

    def test_delete_by_id_not_found(self, base_repo, mock_db):
        """Test deleting a record that doesn't exist."""
        # Setup
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        # Execute
        result = base_repo.delete(1)
        
        # Verify
        assert result is False
        mock_db.delete.assert_not_called()

    def test_exists(self, base_repo, mock_db):
        """Test checking if a record exists."""
        # Setup
        mock_db.query.return_value.filter.return_value.first.return_value = Mock()
        
        # Execute
        result = base_repo.exists(team_number=1234)
        
        # Verify
        assert result is True

    def test_bulk_create(self, base_repo, mock_db):
        """Test bulk creation of records."""
        # Setup
        objects_data = [{"team_number": 1234}, {"team_number": 5678}]
        mock_objects = [Mock(), Mock()]
        
        with patch.object(LockedPicklist, '__new__', side_effect=mock_objects):
            # Execute
            result = base_repo.bulk_create(objects_data)
            
            # Verify
            assert len(result) == 2
            mock_db.add_all.assert_called_once()
            mock_db.flush.assert_called_once()

    def test_sqlalchemy_error_handling(self, base_repo, mock_db):
        """Test SQLAlchemy error handling."""
        # Setup
        mock_db.query.side_effect = SQLAlchemyError("Test error")
        
        # Execute & Verify
        with pytest.raises(SQLAlchemyError):
            base_repo.get(1)


class TestPicklistRepository:
    """Test the picklist repository."""

    @pytest.fixture
    def mock_db(self):
        return Mock(spec=Session)

    @pytest.fixture
    def picklist_repo(self, mock_db):
        return PicklistRepository(mock_db)

    def test_get_by_team_and_event(self, picklist_repo, mock_db):
        """Test getting picklist by team and event."""
        # Setup
        mock_result = Mock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_result
        
        # Execute
        result = picklist_repo.get_by_team_and_event(1234, "2025demo")
        
        # Verify
        assert result == mock_result
        mock_db.query.assert_called_once_with(LockedPicklist)

    def test_get_latest_for_team(self, picklist_repo, mock_db):
        """Test getting latest picklist for a team."""
        # Setup
        mock_result = Mock()
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value.first.return_value = mock_result
        
        # Execute
        result = picklist_repo.get_latest_for_team(1234)
        
        # Verify
        assert result == mock_result

    def test_get_by_event(self, picklist_repo, mock_db):
        """Test getting picklists by event."""
        # Setup
        mock_results = [Mock(), Mock()]
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value.all.return_value = mock_results
        
        # Execute
        result = picklist_repo.get_by_event("2025demo")
        
        # Verify
        assert result == mock_results

    def test_has_picklist_for_event(self, picklist_repo, mock_db):
        """Test checking if team has picklist for event."""
        # Setup
        mock_db.query.return_value.filter.return_value.first.return_value = Mock()
        
        # Execute
        result = picklist_repo.has_picklist_for_event(1234, "2025demo")
        
        # Verify
        assert result is True

    def test_delete_old_picklists(self, picklist_repo, mock_db):
        """Test deleting old picklists."""
        # Setup
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 5
        mock_query.delete.return_value = 5
        
        # Execute
        result = picklist_repo.delete_old_picklists(30)
        
        # Verify
        assert result == 5
        mock_db.flush.assert_called_once()

    def test_get_picklist_stats(self, picklist_repo, mock_db):
        """Test getting picklist statistics."""
        # Setup
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 10
        mock_query.with_entities.return_value.all.return_value = [(1234,), (5678,), (9012,)]
        mock_query.order_by.return_value.first.return_value = Mock(created_at=datetime.now())
        
        # Execute
        result = picklist_repo.get_picklist_stats(2025)
        
        # Verify
        assert result['total_picklists'] == 10
        assert result['unique_teams'] == 3
        assert result['year_filter'] == 2025


class TestAllianceRepository:
    """Test the alliance repository."""

    @pytest.fixture
    def mock_db(self):
        return Mock(spec=Session)

    @pytest.fixture
    def alliance_repo(self, mock_db):
        return AllianceRepository(mock_db)

    def test_get_by_event(self, alliance_repo, mock_db):
        """Test getting alliance selections by event."""
        # Setup
        mock_results = [Mock(), Mock()]
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.options.return_value = mock_query
        mock_query.order_by.return_value.all.return_value = mock_results
        
        # Execute
        result = alliance_repo.get_by_event("2025demo")
        
        # Verify
        assert result == mock_results

    def test_get_active_selection(self, alliance_repo, mock_db):
        """Test getting active alliance selection."""
        # Setup
        mock_result = Mock()
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.options.return_value = mock_query
        mock_query.first.return_value = mock_result
        
        # Execute
        result = alliance_repo.get_active_selection("2025demo")
        
        # Verify
        assert result == mock_result

    def test_update_team_status_new(self, alliance_repo, mock_db):
        """Test updating team status for new team."""
        # Setup
        mock_db.query.return_value.filter.return_value.first.return_value = None
        mock_status = Mock()
        
        with patch.object(TeamSelectionStatus, '__new__', return_value=mock_status):
            # Execute
            result = alliance_repo.update_team_status(1, 1234, is_captain=True)
            
            # Verify
            mock_db.add.assert_called_once_with(mock_status)
            mock_db.flush.assert_called_once()

    def test_update_team_status_existing(self, alliance_repo, mock_db):
        """Test updating existing team status."""
        # Setup
        mock_status = Mock()
        mock_status.is_captain = False
        mock_db.query.return_value.filter.return_value.first.return_value = mock_status
        
        # Execute
        result = alliance_repo.update_team_status(1, 1234, is_captain=True)
        
        # Verify
        assert mock_status.is_captain is True
        mock_db.flush.assert_called_once()

    def test_get_available_teams(self, alliance_repo, mock_db):
        """Test getting available teams."""
        # Setup
        mock_db.query.return_value.filter.return_value.all.return_value = [(1111,), (2222,)]
        
        # Mock second query for all teams
        def side_effect(*args):
            if args[0] == TeamSelectionStatus.team_number:
                mock_query = Mock()
                mock_query.filter.return_value.all.return_value = [(1111,), (2222,), (3333,)]
                return mock_query
            return Mock()
        
        mock_db.query.side_effect = side_effect
        
        # Execute
        result = alliance_repo.get_available_teams(1)
        
        # Verify
        assert 3333 in result  # Available team not in unavailable list

    def test_complete_selection(self, alliance_repo, mock_db):
        """Test completing alliance selection."""
        # Setup
        mock_selection = Mock()
        mock_selection.is_completed = False
        
        with patch.object(alliance_repo, 'get', return_value=mock_selection):
            # Execute
            result = alliance_repo.complete_selection(1)
            
            # Verify
            assert mock_selection.is_completed is True
            mock_db.flush.assert_called_once()

    def test_reset_selection(self, alliance_repo, mock_db):
        """Test resetting alliance selection."""
        # Setup
        mock_selection = Mock()
        mock_selection.is_completed = True
        mock_selection.current_round = 5
        
        with patch.object(alliance_repo, 'get', return_value=mock_selection):
            # Execute
            result = alliance_repo.reset_selection(1)
            
            # Verify
            assert result is True
            assert mock_selection.is_completed is False
            assert mock_selection.current_round == 1


class TestEventRepository:
    """Test the event repository."""

    @pytest.fixture
    def mock_db(self):
        return Mock(spec=Session)

    @pytest.fixture
    def event_repo(self, mock_db):
        return EventRepository(mock_db)

    def test_get_archived_events_by_year(self, event_repo, mock_db):
        """Test getting archived events by year."""
        # Setup
        mock_results = [Mock(), Mock()]
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value.all.return_value = mock_results
        
        # Execute
        result = event_repo.get_archived_events_by_year(2025)
        
        # Verify
        assert result == mock_results

    def test_set_active_archive(self, event_repo, mock_db):
        """Test setting active archive."""
        # Setup
        mock_archive = Mock()
        mock_archive.is_active = False
        
        with patch.object(event_repo, 'get', return_value=mock_archive):
            # Execute
            result = event_repo.set_active_archive(1)
            
            # Verify
            assert mock_archive.is_active is True
            mock_db.flush.assert_called_once()

    def test_create_sheet_configuration(self, event_repo, mock_db):
        """Test creating sheet configuration."""
        # Setup
        config_data = {
            'name': 'Test Config',
            'spreadsheet_id': 'test123',
            'event_key': '2025demo',
            'year': 2025
        }
        mock_config = Mock()
        
        with patch.object(SheetConfiguration, '__new__', return_value=mock_config):
            # Execute
            result = event_repo.create_sheet_configuration(config_data)
            
            # Verify
            mock_db.add.assert_called_once_with(mock_config)
            mock_db.flush.assert_called_once()

    def test_get_active_sheet_config(self, event_repo, mock_db):
        """Test getting active sheet configuration."""
        # Setup
        mock_config = Mock()
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value.first.return_value = mock_config
        
        # Execute
        result = event_repo.get_active_sheet_config("2025demo", 2025)
        
        # Verify
        assert result == mock_config


class TestTeamRepository:
    """Test the team repository."""

    @pytest.fixture
    def mock_db(self):
        return Mock(spec=Session)

    @pytest.fixture
    def team_repo(self, mock_db):
        return TeamRepository(mock_db)

    def test_cache_functionality(self, team_repo):
        """Test team data caching."""
        # Test cache miss
        result = team_repo.get_cached_team_data("nonexistent")
        assert result is None
        
        # Test cache set and hit
        team_repo._cache_team_data("test_key", {"data": "value"})
        result = team_repo.get_cached_team_data("test_key")
        assert result == {"data": "value"}
        
        # Test cache clear
        team_repo.clear_team_cache()
        result = team_repo.get_cached_team_data("test_key")
        assert result is None

    def test_get_team_performance_summary(self, team_repo, mock_db):
        """Test getting team performance summary."""
        # Setup
        mock_history = {
            'team_number': 1234,
            'summary': {
                'total_selections': 10,
                'times_captain': 3,
                'times_picked': 5,
                'times_declined': 1,
                'alliances_joined': 8,
                'picklists_created': 2
            }
        }
        
        with patch.object(team_repo, 'get_team_history', return_value=mock_history):
            # Execute
            result = team_repo.get_team_performance_summary(1234)
            
            # Verify
            assert result['team_number'] == 1234
            assert result['performance_metrics']['success_rate'] == 0.8  # (3+5)/10
            assert result['ratings']['reliability'] == 0.9  # 1 - 0.1 decline rate

    def test_get_teams_by_status(self, team_repo, mock_db):
        """Test getting teams by status."""
        # Setup
        mock_results = [Mock(), Mock()]
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = mock_results
        
        # Execute
        result = team_repo.get_teams_by_status(1, is_captain=True)
        
        # Verify
        assert result == mock_results


class TestUnitOfWork:
    """Test the Unit of Work pattern."""

    @pytest.fixture
    def mock_db(self):
        return Mock(spec=Session)

    @pytest.fixture
    def uow(self, mock_db):
        return UnitOfWork(mock_db)

    def test_repository_creation(self, uow):
        """Test repository creation and caching."""
        # Test repository creation
        picklist_repo1 = uow.picklist_repository
        picklist_repo2 = uow.picklist_repository
        
        # Verify same instance returned (cached)
        assert picklist_repo1 is picklist_repo2
        assert isinstance(picklist_repo1, PicklistRepository)

    def test_commit(self, uow, mock_db):
        """Test transaction commit."""
        # Execute
        uow.commit()
        
        # Verify
        mock_db.commit.assert_called_once()
        assert uow._committed is True

    def test_rollback(self, uow, mock_db):
        """Test transaction rollback."""
        # Execute
        uow.rollback()
        
        # Verify
        mock_db.rollback.assert_called_once()

    def test_context_manager_success(self, mock_db):
        """Test context manager with successful operation."""
        # Execute
        with UnitOfWork(mock_db) as uow:
            uow.picklist_repository.get(1)
        
        # Verify
        mock_db.commit.assert_called_once()

    def test_context_manager_exception(self, mock_db):
        """Test context manager with exception."""
        # Execute
        try:
            with UnitOfWork(mock_db) as uow:
                raise ValueError("Test error")
        except ValueError:
            pass
        
        # Verify
        mock_db.rollback.assert_called_once()
        mock_db.commit.assert_not_called()

    def test_execute_in_transaction(self, uow, mock_db):
        """Test executing operation in transaction."""
        # Setup
        def test_operation(uow_instance):
            return "success"
        
        # Execute
        result = uow.execute_in_transaction(test_operation)
        
        # Verify
        assert result == "success"
        mock_db.commit.assert_called_once()

    def test_bulk_operations(self, uow, mock_db):
        """Test bulk operations helper."""
        # Setup
        bulk_ops = uow.bulk_operations()
        
        # Verify
        assert isinstance(bulk_ops, type(uow.bulk_operations()))
        assert bulk_ops.uow is uow

    def test_get_transaction_info(self, uow, mock_db):
        """Test getting transaction information."""
        # Execute
        info = uow.get_transaction_info()
        
        # Verify
        assert info['has_session'] is True
        assert info['external_session'] is True
        assert info['committed'] is False
        assert isinstance(info['repositories_loaded'], list)


class TestUnitOfWorkContext:
    """Test the Unit of Work context manager function."""

    @patch('app.repositories.unit_of_work.UnitOfWork')
    def test_get_unit_of_work_context(self, mock_uow_class):
        """Test the get_unit_of_work context manager."""
        # Setup
        mock_uow = Mock()
        mock_uow_class.return_value = mock_uow
        
        # Execute
        with get_unit_of_work() as uow:
            assert uow is mock_uow
        
        # Verify UnitOfWork was created
        mock_uow_class.assert_called_once_with(None)


# Integration test fixtures and helpers
@pytest.fixture
def real_db_session():
    """Create a real database session for integration tests."""
    from app.database.db import SessionLocal
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.mark.integration
class TestRepositoryIntegration:
    """Integration tests with real database."""

    def test_picklist_repository_integration(self, real_db_session):
        """Test picklist repository with real database."""
        repo = PicklistRepository(real_db_session)
        
        # Test creating a picklist
        picklist_data = {
            'team_number': 9999,
            'event_key': 'test_event',
            'year': 2025,
            'first_pick_data': [{'team_number': 1234, 'score': 95.0}],
            'second_pick_data': [{'team_number': 5678, 'score': 90.0}],
        }
        
        try:
            # Create
            created = repo.create(picklist_data)
            real_db_session.commit()
            
            assert created.team_number == 9999
            assert created.id is not None
            
            # Get by team and event
            found = repo.get_by_team_and_event(9999, 'test_event')
            assert found is not None
            assert found.id == created.id
            
            # Check existence
            exists = repo.has_picklist_for_event(9999, 'test_event')
            assert exists is True
            
            # Get stats
            stats = repo.get_picklist_stats(2025)
            assert stats['total_picklists'] >= 1
            
        finally:
            # Cleanup
            repo.delete_by(team_number=9999, event_key='test_event')
            real_db_session.commit()

    def test_unit_of_work_integration(self, real_db_session):
        """Test Unit of Work with real database."""
        
        with UnitOfWork(real_db_session) as uow:
            # Test cross-repository operations
            picklist_data = {
                'team_number': 8888,
                'event_key': 'test_uow',
                'year': 2025,
                'first_pick_data': [],
                'second_pick_data': [],
            }
            
            try:
                # Create picklist
                picklist = uow.picklist_repository.create(picklist_data)
                
                # Create alliance selection
                selection_data = {
                    'picklist_id': picklist.id,
                    'event_key': 'test_uow',
                    'year': 2025,
                }
                
                selection = uow.alliance_repository.create(selection_data)
                
                # Verify relationships work
                assert selection.picklist_id == picklist.id
                
                # Test bulk operations
                bulk_ops = uow.bulk_operations()
                team_statuses = [
                    {'selection_id': selection.id, 'team_number': 1111},
                    {'selection_id': selection.id, 'team_number': 2222},
                ]
                
                # This would test bulk operations if implemented
                # bulk_ops.update_team_statuses(team_statuses)
                
            finally:
                # Cleanup
                uow.alliance_repository.delete_by(event_key='test_uow')
                uow.picklist_repository.delete_by(team_number=8888)
                # Transaction will be committed by context manager


if __name__ == "__main__":
    pytest.main([__file__])