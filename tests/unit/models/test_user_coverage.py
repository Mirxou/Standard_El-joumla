from datetime import datetime
from unittest.mock import ANY, MagicMock, patch

import pytest

from src.models.user import User, UserManager, UserRole


class TestUserCoverage:
    @pytest.fixture
    def mock_db(self):
        return MagicMock()

    @pytest.fixture
    def user_manager(self, mock_db):
        return UserManager(db_manager=mock_db, logger=MagicMock())

    def test_user_initialization_defaults(self):
        u = User(username="test")
        assert u.permissions == set()
        assert u.is_active is True
        assert u.is_locked is False

    def test_row_to_user_conversion(self, user_manager):
        # row indices from _row_to_user:
        # 0:id, 1:username, 2:email, 3:full_name, 4:phone, 5:role, 6:hash, 7:salt,
        # 8:is_active, 9:is_locked, 10:failed, 11:last_login, 12:last_change,
        # 13:expires_at, 14:notes, 15:created_by, 16:created_at, 17:updated_at

        row = (
            1,
            "user1",
            "email@test.com",
            "Full Name",
            "123456",
            "admin",
            "hash",
            "salt",
            1,
            0,
            0,
            datetime.now().isoformat(),
            datetime.now().isoformat(),
            datetime.now().isoformat(),
            "notes",
            1,
            datetime.now().isoformat(),
            datetime.now().isoformat(),
        )

        user = user_manager._row_to_user(row)
        assert user.id == 1
        assert user.username == "user1"
        assert user.is_active is True
        assert user.is_locked is False
        assert isinstance(user.created_at, datetime)

    def test_row_to_user_none_timestamps(self, user_manager):
        # Test handling of None for timestamp fields
        row = (
            2,
            "user2",
            None,
            "Name 2",
            None,
            "user",
            "hash",
            "salt",
            1,
            0,
            0,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
        )
        user = user_manager._row_to_user(row)
        assert user.last_login is None
        assert user.created_at is None

    def test_create_user_existing_username(self, user_manager, mock_db):
        # Mock get_user_by_username to return something
        with patch.object(user_manager, "get_user_by_username", return_value=User(username="exists")):
            res = user_manager.create_user(User(username="exists"), "pass")
            assert res is None
            user_manager.logger.warning.assert_called()

    def test_create_user_success(self, user_manager, mock_db):
        with patch.object(user_manager, "get_user_by_username", return_value=None):
            mock_db.execute_non_query.return_value = 1
            mock_db.get_last_insert_id.return_value = 55

            new_user = User(username="new", role=UserRole.CASHIER.value)
            user_id = user_manager.create_user(new_user, "pass")

            assert user_id == 55
            # Verify permissions saved
            mock_db.execute_query.assert_called()  # _save_user_permissions calls execute_query

            # Verify default permissions set
            assert len(new_user.permissions) > 0

    def test_create_user_db_failure(self, user_manager, mock_db):
        with patch.object(user_manager, "get_user_by_username", return_value=None):
            # Simulate DB failure (0 rows affected)
            mock_db.execute_non_query.return_value = 0

            user_id = user_manager.create_user(User(username="fail"), "pass")
            assert user_id is None
            user_manager.logger.error.assert_called()

    def test_create_user_exception(self, user_manager, mock_db):
        mock_db.execute_non_query.side_effect = Exception("DB Error")
        user_id = user_manager.create_user(User(username="error"), "pass")
        assert user_id is None
        user_manager.logger.error.assert_called()

    def test_authenticate_user_inactive(self, user_manager):
        user = User(username="inactive", is_active=False)
        with patch.object(user_manager, "get_user_by_username", return_value=user):
            assert user_manager.authenticate_user("inactive", "pass") is None
            user_manager.logger.warning.assert_called_with(ANY)

    def test_authenticate_user_locked_early_check(self, user_manager):
        user = User(username="locked", is_active=True, is_locked=True)
        with patch.object(user_manager, "get_user_by_username", return_value=user):
            assert user_manager.authenticate_user("locked", "pass") is None

    def test_authenticate_user_wrong_password_lockout(self, user_manager):
        user = User(username="fail_auth", id=1, failed_login_attempts=4)
        with patch.object(user_manager, "get_user_by_username", return_value=user), patch.object(
            user_manager, "_verify_password", return_value=False
        ):

            # 5th failure should lock
            assert user_manager.authenticate_user("fail_auth", "wrong") is None
            assert user.is_locked is True
            user_manager.logger.warning.assert_called()

    def test_authenticate_user_exception(self, user_manager):
        # We need to patch the method on the instance or class, not set attribute on bound method
        with patch.object(user_manager, "get_user_by_username", side_effect=Exception("Boom")):
            assert user_manager.authenticate_user("u", "p") is None

    def test_get_user_by_id_error(self, user_manager, mock_db):
        mock_db.fetch_one.side_effect = Exception("DB Error")
        assert user_manager.get_user_by_id(1) is None

    def test_get_user_by_username_error(self, user_manager, mock_db):
        mock_db.fetch_one.side_effect = Exception("DB Error")
        assert user_manager.get_user_by_username("u") is None

    def test_get_all_users_error(self, user_manager, mock_db):
        mock_db.fetch_all.side_effect = Exception("DB Error")
        assert user_manager.get_all_users() == []

    def test_update_user_error(self, user_manager, mock_db):
        mock_db.execute_query.side_effect = Exception("DB Error")
        assert user_manager.update_user(User(id=1)) is False

    def test_update_user_permissions(self, user_manager, mock_db):
        # Verify update calls permissions save
        mock_db.execute_query.return_value.rowcount = 1
        u = User(id=1, username="u")
        u.add_permission("NEW_PERM")

        assert user_manager.update_user(u) is True
        # Check that permissions delete/insert happened
        # _save_user_permissions calls delete (non_query) then insert (query)
        mock_db.execute_non_query.assert_called_with("DELETE FROM user_permissions WHERE user_id = ?", (1,))
        mock_db.execute_query.assert_called()

    def test_change_password_not_found(self, user_manager):
        with patch.object(user_manager, "get_user_by_id", return_value=None):
            assert user_manager.change_password(999, "old", "new") is False

    def test_change_password_wrong_old(self, user_manager):
        user = User(id=1, password_hash="h", salt="s")
        with patch.object(user_manager, "get_user_by_id", return_value=user), patch.object(
            user_manager, "_verify_password", return_value=False
        ):
            assert user_manager.change_password(1, "wrong", "new") is False

    def test_change_password_success(self, user_manager, mock_db):
        user = User(id=1)
        with patch.object(user_manager, "get_user_by_id", return_value=user), patch.object(
            user_manager, "_verify_password", return_value=True
        ):

            mock_db.execute_query.return_value.rowcount = 1
            assert user_manager.change_password(1, "old", "new") is True
            assert user_manager.logger.info.called

    def test_change_password_exception(self, user_manager):
        with patch.object(user_manager, "get_user_by_id", side_effect=Exception("Error")):
            assert user_manager.change_password(1, "o", "n") is False

    def test_reset_password_exception(self, user_manager, mock_db):
        mock_db.execute_query.side_effect = Exception("Error")
        assert user_manager.reset_password(1, "new") is False

    def test_unlock_user_exception(self, user_manager, mock_db):
        mock_db.execute_query.side_effect = Exception("Error")
        assert user_manager.unlock_user(1) is False

    def test_delete_user_exception(self, user_manager, mock_db):
        mock_db.execute_non_query.side_effect = Exception("Error")
        assert user_manager.delete_user(1) is False

    def test_create_default_admin_exists(self, user_manager, mock_db):
        mock_db.fetch_one.return_value = (1,)
        # Reset mock to ensure we don't count previous calls
        user_manager.logger.info.reset_mock()
        assert user_manager.create_default_admin() is True
        # Should not create new one, so "تم إنشاء المدير" should NOT be logged
        # Check call args safely
        logged_messages = [call[0][0] for call in user_manager.logger.info.call_args_list]
        assert not any(msg.startswith("تم إنشاء المدير") for msg in logged_messages)

    def test_create_default_admin_exception(self, user_manager, mock_db):
        mock_db.fetch_one.side_effect = Exception("Error")
        assert user_manager.create_default_admin() is False

    def test_save_user_permissions_exception(self, user_manager, mock_db):
        mock_db.execute_non_query.side_effect = Exception("Error")
        # Should catch exception and log error, not crash
        user_manager._save_user_permissions(1, {"PERM"})
        user_manager.logger.error.assert_called()

    def test_load_user_permissions_exception(self, user_manager, mock_db):
        mock_db.fetch_all.side_effect = Exception("Error")
        perms = user_manager._load_user_permissions(1)
        assert perms == set()
        user_manager.logger.error.assert_called()

    def test_update_failed_attempts_exception(self, user_manager, mock_db):
        mock_db.execute_query.side_effect = Exception("Error")
        user_manager._update_failed_attempts(1, 1, False)
        user_manager.logger.error.assert_called()

    def test_update_last_login_exception(self, user_manager, mock_db):
        mock_db.execute_query.side_effect = Exception("Error")
        user_manager._update_last_login(1, datetime.now())
        user_manager.logger.error.assert_called()
