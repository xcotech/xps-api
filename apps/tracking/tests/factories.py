import factory

from apps.user.tests.factories import *
from apps.system.tests.factories import *
from apps.org.tests.factories import *

from apps.tracking.models import *

class SessionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Session

    org = factory.SubFactory(OrgFactory)
    name = factory.Sequence(lambda n: f'Test Session {n}')


class ActivityFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Activity

    session = factory.SubFactory(SessionFactory)

class ActivityDataFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ActivityData

    activity = factory.SubFactory(ActivityFactory)
    data = {
        'test': 'value'
    }