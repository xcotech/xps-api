import pytest
import mock

from cloudinary import CloudinaryImage

from xps_cloud.models import XPSModel
from apps.user.models import *


@pytest.mark.django_db
def test_user_manager_create_user():
    user = User.objects.create_user('username', 'test@test.com', 'asdfasdf')
    assert user.username == 'username'

def test_user_manager_create_user_no_username():
    with pytest.raises(ValueError) as err:
        user = User.objects.create_user('', 'test@test.com', 'asdfasdf')
        assert user is None

def test_user_str():
    user = User(first_name='Test', last_name='User')
    user.__str__() == 'Test User'


def test_user_can_admin():
    user = User(first_name='Test', last_name='User')
    assert user.can_admin(user) is True


def test_user_can_admin_other():
    user = User(first_name='Test', last_name='User')
    user2 = User(first_name='Test', last_name='User2')
    assert user.can_admin(user2) is False


def test_user_image_str():
    user = User(first_name='Test', last_name='User')
    user_image = UserImage(user=user, pk=1)
    assert user_image.__str__() == 'Test User: Image(primary: True) 1'


@mock.patch.object(User, 'can_admin')
def test_org_system_can_admin(admin_mock):
    admin_mock.return_value = True
    user = User()
    user_image = UserImage(user=user, pk=1)
    assert user_image.can_admin(user) is True
    assert admin_mock.call_count == 1
