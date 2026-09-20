from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=50, required=False, label='Имя')

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'password1', 'password2']

    def clean_email(self):
        email = self.cleaned_data['email'].lower().strip()
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('Пользователь с такой почтой уже существует.')
        return email

    def clean_username(self):
        username = self.cleaned_data['username'].strip()
        if len(username) < 3:
            raise forms.ValidationError('Логин должен содержать минимум 3 символа.')
        return username
