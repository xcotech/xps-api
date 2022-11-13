import factory

from apps.user.tests.factories import *

from apps.system.models import *


class SystemFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = System

    serial_num = factory.Sequence(lambda n: f'System {n}')


class HubFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Hub

    system = factory.SubFactory(SystemFactory)
    serial_num = factory.Sequence(lambda n: f'Hub {n}')


class TagFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Tag

    system = factory.SubFactory(SystemFactory)
    serial_num = factory.Sequence(lambda n: f'Tag {n}')