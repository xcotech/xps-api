import factory

from django.contrib.auth import get_user_model

from apps.user.models import *

global_password = 'asdfasdf'


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = get_user_model()

    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    username = factory.Sequence(lambda x: f'username{x}')
    email = factory.Sequence(lambda n: f'person{n}@example.com')

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        manager = cls._get_manager(model_class)
        user = manager.create_user(*args, **kwargs)
        user.set_password(global_password)
        user.is_active = True
        user.save()
        return user


class UserImageFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = UserImage

    user = factory.SubFactory(UserFactory)
    public_id = 'some_id'
