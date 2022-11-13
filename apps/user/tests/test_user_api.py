import pytest
import mock
import json

from django.urls import reverse

from rest_framework import status

from apps.user.tests.factories import *
from apps.user.models import *


pytestmark = pytest.mark.django_db

""" User Resource API """

# def test_create_user(loggedin_api_client):
#     url = reverse('user-list')
#     data = {
#         'first_name': 'Test',
#         'last_name': 'User',
#         'email': ''
#      }
#     response = loggedin_api_client.post(url, data)
#     assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


def test_get_user_anon(anon_api_client, new_user):
    url = reverse('user-detail', args=[new_user.pk])
    response = anon_api_client.get(url)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_get_user_logged_in(loggedin_api_client, new_user):
    url = reverse('user-detail', args=[new_user.pk])
    response = loggedin_api_client.get(url)
    assert response.status_code == status.HTTP_200_OK


def test_get_user_anon(anon_api_client, new_user):
    url = reverse('user-list')
    response = anon_api_client.get(url)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_get_user_logged_in(loggedin_api_client, new_user):
    url = reverse('user-list')
    response = loggedin_api_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert response.data['count'] == 1


def test_put_user_anon(anon_api_client, new_user):
    url = reverse('user-detail', args=[new_user.id])
    response = anon_api_client.put(url, {})
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@mock.patch.object(User, 'can_admin')
def test_user_put_ok(can_admin_mock, loggedin_api_client, new_user):
    can_admin_mock.return_value = True
    url = reverse('user-detail', args=[new_user.id])
    data = {
        'first_name': 'Test',
        'last_name': 'User',
        'email': new_user.email,
        'bio': 'New Bio',
    }
    response = loggedin_api_client.put(url, data)
    assert response.status_code == status.HTTP_200_OK
    assert response.data['bio'] == data['bio']


@mock.patch.object(User, 'can_admin')
def test_user_put_cant_admin(can_admin_mock, loggedin_api_client, new_user):
    can_admin_mock.return_value = False
    url = reverse('user-detail', args=[new_user.id])
    data = {
        'first_name': 'Test',
        'last_name': 'User',
        'email': new_user.email,
        'bio': 'New Bio',
    }
    response = loggedin_api_client.put(url, data)
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_patch_user_anon(anon_api_client, new_user):
    url = reverse('user-detail', args=[new_user.id])
    response = anon_api_client.patch(url, {})
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@mock.patch.object(User, 'can_admin')
def test_patch_user_self_ok(can_admin_mock, loggedin_api_client, new_user):
    can_admin_mock.return_value = True
    url = reverse('user-detail', args=[new_user.id])
    data = {'bio': 'New Bio'}
    response = loggedin_api_client.patch(url, data)
    assert response.status_code == status.HTTP_200_OK
    assert response.data['bio'] == data['bio']


@mock.patch.object(User, 'can_admin')
def test_patch_user_self_cant_admin(can_admin_mock, loggedin_api_client, new_user):
    can_admin_mock.return_value = False
    url = reverse('user-detail', args=[new_user.id])
    data = {'bio': 'New Bio'}
    response = loggedin_api_client.patch(url, data)
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_delete_user_anon(anon_api_client, new_user):
    url = reverse('user-detail', args=[new_user.id])
    response = anon_api_client.delete(url)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@mock.patch.object(User, 'can_admin')
def test_delete_user_self(can_admin_mock, loggedin_api_client, new_user):
    can_admin_mock.return_value = True
    url = reverse('user-detail', args=[new_user.id])
    response = loggedin_api_client.delete(url)
    assert response.status_code == status.HTTP_204_NO_CONTENT


@mock.patch.object(User, 'can_admin')
def test_delete_user_cant_admin(can_admin_mock, loggedin_api_client, new_user):
    can_admin_mock.return_value = False
    url = reverse('user-detail', args=[new_user.id])
    response = loggedin_api_client.delete(url)
    assert response.status_code == status.HTTP_403_FORBIDDEN


""" UserImage Resource API """

def test_create_user_image_anon(anon_api_client):
    url = reverse('user_image-list')
    response = anon_api_client.post(url, {})
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_create_user_image(loggedin_api_client, new_user):
    url = reverse('user_image-list')
    data = {
        'user': new_user.pk,
        'public_id': 'someid',
        'primary': True,
    }
    response = loggedin_api_client.post(url, data)
    assert response.status_code == status.HTTP_201_CREATED
    user_image = UserImage.objects.first()
    assert user_image.primary is True
    assert user_image.user == new_user


def test_create_user_image_other_user(loggedin_api_client):
    new_user = UserFactory()
    url = reverse('user_image-list')
    data = {
        'user': new_user.pk,
        'public_id': 'someid',
        'primary': False,
    }
    response = loggedin_api_client.post(url, data)
    assert response.status_code == status.HTTP_201_CREATED
    user_image = UserImage.objects.first()
    assert user_image.primary is False
    assert user_image.user == new_user


def test_get_user_image_anon(anon_api_client, new_user_image):
    url = reverse('user_image-detail', args=[new_user_image.pk])
    response = anon_api_client.get(url)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_get_user_image_logged_in(loggedin_api_client, new_user_image):
    url = reverse('user_image-detail', args=[new_user_image.pk])
    response = loggedin_api_client.get(url)
    assert response.status_code == status.HTTP_200_OK


def test_get_user_images_anon(anon_api_client, new_user_image):
    url = reverse('user_image-list')
    response = anon_api_client.get(url)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_get_user_images_logged_in(loggedin_api_client, new_user_image):
    url = reverse('user_image-list')
    response = loggedin_api_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert response.data['count'] == 1


def test_put_user_image_anon(anon_api_client, new_user_image):
    url = reverse('user_image-detail', args=[new_user_image.id])
    response = anon_api_client.put(url, {})
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@mock.patch.object(UserImage, 'can_admin')
def test_user_image_put_ok(can_admin_mock, loggedin_api_client, new_user_image):
    can_admin_mock.return_value = True
    url = reverse('user_image-detail', args=[new_user_image.id])
    data = {
        'id': new_user_image.id,
        'user': new_user_image.user.pk,
        'public_id': new_user_image.public_id,
        'primary': True
    }
    response = loggedin_api_client.put(url, data)
    assert response.status_code == status.HTTP_200_OK
    assert response.data['primary'] is True


@mock.patch.object(UserImage, 'can_admin')
def test_user_image_put_cant_admin(can_admin_mock, loggedin_api_client, new_user_image):
    can_admin_mock.return_value = False
    url = reverse('user_image-detail', args=[new_user_image.id])
    data = {
        'id': new_user_image.id,
        'user': new_user_image.user.pk,
        'public_id,': new_user_image.public_id,
        'primary': True
    }
    response = loggedin_api_client.put(url, data)
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_patch_user_image_anon(anon_api_client, new_user_image):
    url = reverse('user_image-detail', args=[new_user_image.id])
    response = anon_api_client.patch(url, {})
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@mock.patch.object(UserImage, 'can_admin')
def test_patch_user_image_self_ok(can_admin_mock, loggedin_api_client, new_user_image):
    can_admin_mock.return_value = True
    url = reverse('user_image-detail', args=[new_user_image.id])
    data = {'primary': False}
    response = loggedin_api_client.patch(url, data)
    assert response.status_code == status.HTTP_200_OK
    assert response.data['primary'] is False


@mock.patch.object(UserImage, 'can_admin')
def test_patch_user_image_self_cant_admin(can_admin_mock, loggedin_api_client, new_user_image):
    can_admin_mock.return_value = False
    url = reverse('user_image-detail', args=[new_user_image.id])
    data = {'primary': True}
    response = loggedin_api_client.patch(url, data)
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_delete_user_image_anon(anon_api_client, new_user_image):
    url = reverse('user_image-detail', args=[new_user_image.id])
    response = anon_api_client.delete(url)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@mock.patch.object(UserImage, 'can_admin')
def test_delete_user_image_self(can_admin_mock, loggedin_api_client, new_user_image):
    can_admin_mock.return_value = True
    url = reverse('user_image-detail', args=[new_user_image.id])
    response = loggedin_api_client.delete(url)
    assert response.status_code == status.HTTP_204_NO_CONTENT


@mock.patch.object(UserImage, 'can_admin')
def test_delete_user_image_cant_admin(can_admin_mock, loggedin_api_client, new_user_image):
    can_admin_mock.return_value = False
    url = reverse('user_image-detail', args=[new_user_image.id])
    response = loggedin_api_client.delete(url)
    assert response.status_code == status.HTTP_403_FORBIDDEN
