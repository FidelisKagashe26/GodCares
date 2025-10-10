from django import forms
from django.contrib.auth.models import User
from .models import PrayerRequest, LessonComment

class PrayerRequestForm(forms.ModelForm):
    class Meta:
        model = PrayerRequest
        fields = ['name', 'email', 'phone', 'category', 'request', 'is_anonymous', 'is_urgent']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 rounded-lg border border-gray-300 focus:outline-none focus:ring-2 focus:ring-red-500',
                'placeholder': 'Jina lako kamili'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'w-full px-4 py-3 rounded-lg border border-gray-300 focus:outline-none focus:ring-2 focus:ring-red-500',
                'placeholder': 'email@example.com'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 rounded-lg border border-gray-300 focus:outline-none focus:ring-2 focus:ring-red-500',
                'placeholder': '+255 xxx xxx xxx'
            }),
            'category': forms.Select(attrs={
                'class': 'w-full px-4 py-3 rounded-lg border border-gray-300 focus:outline-none focus:ring-2 focus:ring-red-500'
            }),
            'request': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 rounded-lg border border-gray-300 focus:outline-none focus:ring-2 focus:ring-red-500',
                'rows': 6,
                'placeholder': 'Andika ombi lako hapa... Mungu anasikia kila neno la moyo wako.'
            }),
            'is_anonymous': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 text-red-600 bg-gray-100 border-gray-300 rounded focus:ring-red-500'
            }),
            'is_urgent': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 text-red-600 bg-gray-100 border-gray-300 rounded focus:ring-red-500'
            }),
        }
        labels = {
            'name': 'Jina Lako',
            'email': 'Barua Pepe',
            'phone': 'Nambari ya Simu',
            'category': 'Aina ya Ombi',
            'request': 'Ombi Lako',
            'is_anonymous': 'Tuma bila kutaja jina (Anonymous)',
            'is_urgent': 'Ombi la haraka (Urgent)',
        }

    def clean(self):
        cleaned_data = super().clean()
        is_anonymous = cleaned_data.get('is_anonymous')
        name = cleaned_data.get('name')
        
        # If not anonymous, name is required
        if not is_anonymous and not name:
            raise forms.ValidationError('Jina ni lazima ikiwa hutaki kutuma bila kutaja jina.')
        
        # If anonymous, clear personal information
        if is_anonymous:
            cleaned_data['name'] = ''
            cleaned_data['email'] = ''
            cleaned_data['phone'] = ''
        
        return cleaned_data

class SignUpForm(forms.ModelForm):
    password1 = forms.CharField(widget=forms.PasswordInput, label="Password")
    password2 = forms.CharField(widget=forms.PasswordInput, label="Confirm Password")
    phone_number = forms.CharField(max_length=20, required=True, label="Phone Number")

    class Meta:
        model = User
        fields = ["username", "email"]

    def clean_email(self):
        email = self.cleaned_data.get("email", "").strip().lower()
        if not email:
            raise forms.ValidationError("Email is required.")
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Email already in use.")
        return email

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get("password1")
        p2 = cleaned.get("password2")
        if p1 and p2 and p1 != p2:
            self.add_error("password2", "Passwords do not match.")
        return cleaned

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
            # save phone to profile
            user.profile.phone_number = self.cleaned_data["phone_number"]
            user.profile.save()
        return user


class LessonCommentForm(forms.ModelForm):
    class Meta:
        model = LessonComment
        fields = ["body"]
        widgets = {
            "body": forms.Textarea(attrs={"rows": 4, "placeholder": "Andika maoni yako hapa..."}),
        }
        labels = {
            "body": "Maoni",
        }