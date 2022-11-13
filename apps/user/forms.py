from django import forms
from django.contrib.auth import get_user_model
from django.utils.text import slugify


class UserCreateForm(forms.ModelForm):
    username = forms.CharField(max_length=255, required=False)

    class Meta:
        model = get_user_model()
        fields = [
            'email',
            'first_name',
            'last_name',
        ]

    def clean(self):
        cleaned_data = super(UserCreateForm, self).clean()

        first_name = cleaned_data.get('first_name')
        last_name = cleaned_data.get('last_name')

        username = slugify(f'{first_name} {last_name}')
        unique = False
        counter = 1
        while not unique:
            try:
                get_user_model()._default_manager.get(username__iexact=username)
            except get_user_model().DoesNotExist:
                unique = True
            else:
                username = f'{username}-{counter}'
                counter += 1

        cleaned_data['username'] = username
        return cleaned_data
