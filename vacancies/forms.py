from django import forms

class JobSearchForm(forms.Form):
    profession = forms.CharField(
        label='Профессия',
        max_length=100,
        widget=forms.TextInput(attrs={'placeholder': 'Введите профессию'})
    )
    salary = forms.IntegerField(
        label='Зарплата',
        required=False,
        widget=forms.NumberInput(attrs={'placeholder': 'Минимальная зарплата'})
    )
    region = forms.CharField(
        label='Регион',
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Введите регион'})
    )
