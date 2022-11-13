import pytest

from apps.tracking.tests.factories import *

@pytest.fixture()
@pytest.mark.django_db
def new_session(new_user):
    org = OrgFactory(owner=new_user)
    return SessionFactory(org=org)

@pytest.fixture()
@pytest.mark.django_db
def new_activity(new_user):
    return ActivityFactory(user=new_user)

@pytest.fixture()
@pytest.mark.django_db
def new_activity_data(new_user):
    return ActivityDataFactory(activity=activity)

