import pytest

from apps.user.tests.factories import *


@pytest.fixture()
@pytest.mark.django_db
def new_user():
    return UserFactory()


@pytest.fixture()
@pytest.mark.django_db
def new_user_image(new_user):
    return UserImageFactory(user=new_user)
