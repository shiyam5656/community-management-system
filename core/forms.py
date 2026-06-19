from django import forms
from .models import Property, Announcement
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Property, Announcement, ResidentProfile, Fee, Payment, MaintenanceRequest, Message, ChatMessage
from .models import Friendship, PrivateConversation
from django.db import models  # if not already imported at top
from .models import Friendship
# ---------- Existing forms (keep as they are) ----------
class PropertyForm(forms.ModelForm):
    class Meta:
        model = Property
        fields = ['unit_number', 'owner_name', 'monthly_fee', 'status']
        widgets = {
            'unit_number': forms.TextInput(attrs={'class': 'form-control'}),
            'owner_name': forms.TextInput(attrs={'class': 'form-control'}),
            'monthly_fee': forms.NumberInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }

class AnnouncementForm(forms.ModelForm):
    class Meta:
        model = Announcement
        fields = ['title', 'content', 'category', 'is_emergency']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'is_emergency': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class FeeForm(forms.ModelForm):
    class Meta:
        model = Fee
        fields = ['property', 'amount', 'due_date', 'description']
        widgets = {
            'property': forms.Select(attrs={'class': 'form-select'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'due_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'description': forms.TextInput(attrs={'class': 'form-control'}),
        }

class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ['amount', 'method', 'notes']
        widgets = {
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'method': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

class MaintenanceRequestForm(forms.ModelForm):
    class Meta:
        model = MaintenanceRequest
        fields = ['property', 'resident_name', 'title', 'description']
        widgets = {
            'property': forms.Select(attrs={'class': 'form-select'}),
            'resident_name': forms.TextInput(attrs={'class': 'form-control'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class MaintenanceStatusForm(forms.ModelForm):
    class Meta:
        model = MaintenanceRequest
        fields = ['status', 'assigned_to']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-select'}),
            'assigned_to': forms.TextInput(attrs={'class': 'form-control'}),
        }

class ResidentRegistrationForm(UserCreationForm):
    phone = forms.CharField(max_length=15, required=True, label="Phone Number")
    move_in_date = forms.DateField(required=False, label="Move-in Date",
                                   widget=forms.DateInput(attrs={'type': 'date'}))
    property = forms.ModelChoiceField(queryset=Property.objects.all(), required=False, label="Assign Property")

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password1', 'password2']

    def save(self, commit=True):
        user = super().save(commit=commit)
        profile = ResidentProfile(
            user=user,
            phone=self.cleaned_data['phone'],
            move_in_date=self.cleaned_data['move_in_date'],
            property=self.cleaned_data['property']
        )
        if commit:
            profile.save()
        return user

class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ['subject', 'body']

class ChatMessageForm(forms.ModelForm):
    class Meta:
        model = ChatMessage
        fields = ['message']
        widgets = {
            'message': forms.Textarea(attrs={'rows': 3, 'class': 'form-control', 'placeholder': 'Type your reply...'})
        }

# ---------- NEW SOCIAL FORMS ----------
from .models import UserProfile, Friendship, PrivateMessage

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['bio', 'profile_picture']
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 4, 'class': 'form-control', 'placeholder': 'Tell something about yourself...'}),
            'profile_picture': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }

class FriendshipActionForm(forms.Form):
    action = forms.ChoiceField(choices=[('accept', 'Accept'), ('reject', 'Reject')], widget=forms.RadioSelect)

class PrivateMessageForm(forms.ModelForm):
    class Meta:
        model = PrivateMessage
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 2, 'class': 'form-control', 'placeholder': 'Type your message...'})
        }
class StartConversationForm(forms.Form):
    recipient = forms.ModelChoiceField(queryset=User.objects.none(), label="To", empty_label="Select recipient")
    subject = forms.CharField(max_length=200)
    message = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}))

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Get all accepted friends (both directions)
        friends = Friendship.objects.filter(
            models.Q(from_user=user, status='accepted') | models.Q(to_user=user, status='accepted')
        ).select_related('from_user', 'to_user')
        friend_users = set()
        for f in friends:
            if f.from_user == user:
                friend_users.add(f.to_user)
            else:
                friend_users.add(f.from_user)
        self.fields['recipient'].queryset = User.objects.filter(id__in=[u.id for u in friend_users])