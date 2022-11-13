import pytest

from apps.user.tests.factories import *
from apps.user.forms import *

pytestmark = pytest.mark.django_db


form_data = {
    'first_name': 'Test',
    'last_name': 'User',
    'email': 'test@test.com',
}

def test_user_create_form():
    form = UserCreateForm(data=form_data)
    assert form.is_valid() is True


def test_user_create_form_no_email():
    form_data['email'] = ''
    form = UserCreateForm(data=form_data)
    assert form.is_valid() is True


def test_user_create_form_slugify():
    UserFactory(
        first_name=form_data['first_name'],
        last_name=form_data['last_name'],
        username='test-user',
    )
    form = UserCreateForm(data=form_data)
    assert form.is_valid() is True
    assert form.cleaned_data['username'] == 'test-user-1'
