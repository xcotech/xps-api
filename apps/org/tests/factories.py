import factory
from apps.org.models import *
from apps.user.tests.factories import *
from apps.system.tests.factories import *

class OrgFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Org

    owner = factory.SubFactory(UserFactory)
    name = factory.Sequence(lambda n: f'Test Org {n}')


class OrgSystemFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = OrgSystem

    org = factory.SubFactory(OrgFactory)
    system = factory.SubFactory(SystemFactory)
    name = factory.Sequence(lambda n: f'Test Org System {n}')


class OrgMemberFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = OrgMember

    org = factory.SubFactory(OrgFactory)
    user = factory.SubFactory(UserFactory)


class TeamFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Team

    org = factory.SubFactory(OrgFactory)
    name = factory.Sequence(lambda n: f'Test Team {n}')
