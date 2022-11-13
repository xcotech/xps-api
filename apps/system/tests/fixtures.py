import pytest

from apps.system.tests.factories import *


@pytest.fixture()
@pytest.mark.django_db
def new_system():
    return SystemFactory()


@pytest.fixture()
@pytest.mark.django_db
def new_hub():
    return HubFactory()


@pytest.fixture()
@pytest.mark.django_db
def new_tag():
    return TagFactory()
