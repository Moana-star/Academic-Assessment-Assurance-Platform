from django import forms
from django.contrib.auth import get_user_model
from .models import Examination, Student

class RegistrationForm(forms.Form):
    username = forms.CharField(max_length=150, label='Username')
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput, min_length=8)
    password_confirm = forms.CharField(widget=forms.PasswordInput, label='Confirm password')
    admission_number = forms.CharField(max_length=40)
    full_name = forms.CharField(max_length=160)
    course = forms.CharField(max_length=160)
    department = forms.CharField(max_length=160)
    def clean_username(self):
        value = self.cleaned_data['username']
        if get_user_model().objects.filter(username__iexact=value).exists(): raise forms.ValidationError('That username is already in use.')
        return value
    def clean(self):
        cleaned = super().clean()
        if cleaned.get('password') != cleaned.get('password_confirm'): self.add_error('password_confirm', 'Passwords do not match.')
        if Student.objects.filter(admission_number=cleaned.get('admission_number')).exists(): self.add_error('admission_number', 'That admission number is already registered.')
        return cleaned

class StudentForm(forms.ModelForm):
    username = forms.CharField(max_length=150); temporary_password = forms.CharField(widget=forms.PasswordInput, min_length=8)
    class Meta: model = Student; fields = ['admission_number','full_name','course','department','profile_photo']
    def save(self, commit=True):
        data = self.cleaned_data; user = get_user_model().objects.create_user(username=data['username'], password=data['temporary_password'], role='student'); student = super().save(commit=False); student.user = user
        if commit: student.save()
        return student

class ExaminationForm(forms.ModelForm):
    class Meta:
        model = Examination; fields = ['title','code','course','examination_date','start_time','end_time','venue','status']
        widgets = {'examination_date': forms.DateInput(attrs={'type':'date'}), 'start_time': forms.TimeInput(attrs={'type':'time'}), 'end_time': forms.TimeInput(attrs={'type':'time'})}
