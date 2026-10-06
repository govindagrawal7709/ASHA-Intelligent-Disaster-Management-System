from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Profile, ReliefRequest


class CustomUserCreationForm(UserCreationForm):
    ROLE_CHOICES = (
        ('victim', 'I need help'),
        ('volunteer', 'I want to volunteer'),
    )

    role = forms.ChoiceField(choices=ROLE_CHOICES, widget=forms.RadioSelect, required=True)
    phone_number = forms.CharField(max_length=20, required=True)

    # Volunteer-only fields
    full_name = forms.CharField(max_length=100, required=False)
    skills_bio = forms.CharField(widget=forms.Textarea, required=False)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = UserCreationForm.Meta.fields + (
            'phone_number', 'role', 'full_name', 'skills_bio',
        )

    def save(self, commit=True):
        user = super().save(commit=False)

        if commit:
            user.save()

            # Create profile
            profile = Profile.objects.create(
                user=user,
                role=self.cleaned_data["role"],
                phone_number=self.cleaned_data["phone_number"],
                full_name=self.cleaned_data.get("full_name", "") if self.cleaned_data["role"] == "volunteer" else "",
                skills_bio=self.cleaned_data.get("skills_bio", "") if self.cleaned_data["role"] == "volunteer" else "",
            )

        return user


class ReliefRequestForm(forms.ModelForm):
    class Meta:
        model = ReliefRequest
        fields = ['request_type', 'description', 'latitude', 'longitude']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }


class ReliefStatusUpdateForm(forms.ModelForm):
    class Meta:
        model = ReliefRequest
        fields = ['status']


class AlertForm(forms.Form):
    message = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3, 'placeholder': 'Enter alert message...'}),
        max_length=500,
        help_text='Critical safety information or general announcements.'
    )
    severity = forms.ChoiceField(choices=[
        ('Low', 'Low'),
        ('Medium', 'Medium'),
        ('High', 'High'),
        ('Critical', 'Critical'),
    ], initial='Medium')
    is_active = forms.BooleanField(label='Active Alert', initial=True, required=False)
