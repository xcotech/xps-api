import pytest
import json

from django.test.client import Client, MULTIPART_CONTENT
from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status
from rest_framework_jwt.settings import api_settings

from apps.user.tests.factories import global_password


class XPSCloudAPIClient(APIClient):
    user = None

    def login(self, **credentials):
        """
        Returns True if login is possible; False if the provided credentials
        are incorrect, or the user is inactive.
        """
        response = self.post(reverse('login'), credentials, format='json')
        if response.status_code == status.HTTP_200_OK:
            self.credentials(
                HTTP_AUTHORIZATION="{0} {1}".format(api_settings.JWT_AUTH_HEADER_PREFIX, response.data['token']))

            return True
        else:
            return False


@pytest.fixture()
def anon_api_client():
    return XPSCloudAPIClient()


@pytest.fixture()
def loggedin_api_client(new_user):
    client = XPSCloudAPIClient()
    client.login(username=new_user.username, password=global_password)
    client.user = new_user
    return client


class XCOTestClient(Client):
    def post(self, path, data=None, content_type=MULTIPART_CONTENT, secure=False, **extra):
        return super(XCOTestClient, self).post(path, data, content_type, secure, HTTP_X_REQUESTED_WITH='XMLHttpRequest', **extra)

    def get(self, path, data=None, secure=False, **extra):
        return super(XCOTestClient, self).get(path, data, secure, content_type='application/json', HTTP_X_REQUESTED_WITH='XMLHttpRequest', **extra)


@pytest.fixture()
def anon_client():
    return XCOTestClient()


@pytest.fixture()
def loggedin_client(new_user):
    client = XCOTestClient()
    client.login(email=new_user.email, password=global_password)
    return client
