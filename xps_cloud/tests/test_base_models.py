import pytest
import mock

from django.db.models import Model
from xps_cloud.models import *
from apps.user.models import *
from apps.tracking.models import *
from apps.org.models import Org, Team

@mock.patch.object(XPSModel, 'invalidate')
@mock.patch.object(Model, 'save')
def test_xpsmodel_save(save_mock, invalidate_mock):
    xps = XPSModel()
    xps.save()
    assert save_mock.call_count == 1
    assert invalidate_mock.call_count == 1


@mock.patch.object(XPSModel, 'invalidate')
@mock.patch.object(Model, 'delete')
def test_xpsmodel_delete(delete_mock, invalidate_mock):
    xps = XPSModel()
    xps.delete()
    assert delete_mock.call_count == 1
    assert invalidate_mock.call_count == 1


def test_can_admin_with_user():
    user = User()
    # can't test with XMSModel because it doesn't have a user, use Org
    org_member = Org(owner=user)
    assert org_member.can_admin(user) is True


def test_can_admin_with_different_user():
    user = User()
    user2 = User()
    # can't test with XMSModel because it doesn't have a user, use Org
    org_member = Org(owner=user)
    assert org_member.can_admin(user2) is False


def test_can_admin_without_user():
    user = User()
    xps = XPSModel()
    assert xps.can_admin(user) is False
