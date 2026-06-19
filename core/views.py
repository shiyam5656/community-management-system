from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.urls import reverse
from django.db.models import Sum, Q
from django.utils import timezone
from datetime import date

from .models import (
    Property, Announcement, Fee, Payment, ResidentProfile,
    MaintenanceRequest, ParkingSpot, Conversation, ChatMessage,
    UserProfile, Friendship, PrivateConversation, PrivateMessage
)
from .forms import (
    PropertyForm, AnnouncementForm, FeeForm, PaymentForm,
    ResidentRegistrationForm, MaintenanceRequestForm,
    MaintenanceStatusForm, ChatMessageForm, UserProfileForm,
    FriendshipActionForm, PrivateMessageForm, StartConversationForm
)

# ---------- Helper ----------
def is_manager(user):
    return user.is_staff

# ---------- Home & Property ----------
def home(request):
    properties = Property.objects.all()
    total_pending = Fee.objects.filter(status='unpaid').aggregate(Sum('amount'))['amount__sum'] or 0
    return render(request, 'core/home.html', {'properties': properties, 'total_pending': total_pending})

@login_required
@user_passes_test(is_manager)
def add_property(request):
    if request.method == 'POST':
        form = PropertyForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Property added!')
            return redirect('home')
    else:
        form = PropertyForm()
    return render(request, 'core/add_property.html', {'form': form})

# ---------- Announcements ----------
def announcement_list(request):
    announcements = Announcement.objects.all().order_by('-created_at')
    return render(request, 'core/announcement_list.html', {'announcements': announcements})

@login_required
@user_passes_test(is_manager)
def announcement_create(request):
    if request.method == 'POST':
        form = AnnouncementForm(request.POST)
        if form.is_valid():
            announcement = form.save(commit=False)
            announcement.created_by = request.user.username
            announcement.save()
            messages.success(request, 'Announcement posted!')
            return redirect('announcement_list')
    else:
        form = AnnouncementForm()
    return render(request, 'core/announcement_form.html', {'form': form})

@login_required
@user_passes_test(is_manager)
def announcement_delete(request, pk):
    announcement = get_object_or_404(Announcement, pk=pk)
    if request.method == 'POST':
        announcement.delete()
        messages.success(request, 'Announcement deleted.')
        return redirect('announcement_list')
    return render(request, 'core/announcement_confirm_delete.html', {'announcement': announcement})

# ---------- Fees & Payments ----------
@login_required
@user_passes_test(is_manager)
def fee_list(request):
    fees = Fee.objects.all().order_by('-due_date')
    return render(request, 'core/fee_list.html', {'fees': fees})

@login_required
@user_passes_test(is_manager)
def fee_create(request):
    if request.method == 'POST':
        form = FeeForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Fee added successfully!')
            return redirect('fee_list')
    else:
        form = FeeForm()
    return render(request, 'core/fee_form.html', {'form': form, 'title': 'Create Fee'})

@login_required
@user_passes_test(is_manager)
def record_payment(request, fee_id):
    fee = get_object_or_404(Fee, id=fee_id)
    if request.method == 'POST':
        form = PaymentForm(request.POST)
        if form.is_valid():
            payment = form.save(commit=False)
            payment.fee = fee
            payment.save()
            messages.success(request, f'Payment recorded! Receipt: {payment.receipt_number}')
            return redirect('fee_list')
    else:
        paid = fee.payments.aggregate(total=Sum('amount'))['total'] or 0
        remaining = fee.amount - paid
        form = PaymentForm(initial={'amount': remaining})
    return render(request, 'core/payment_form.html', {'form': form, 'fee': fee})

@login_required
def resident_fees(request):
    if is_manager(request.user):
        return fee_list(request)
    else:
        return render(request, 'core/resident_fees.html', {'fees': Fee.objects.all()})

# ---------- Maintenance ----------
def maintenance_list(request):
    requests = MaintenanceRequest.objects.all().order_by('-created_at')
    return render(request, 'core/maintenance_list.html', {'requests': requests})

@login_required
@user_passes_test(is_manager)
def maintenance_update(request, pk):
    req = get_object_or_404(MaintenanceRequest, pk=pk)
    if request.method == 'POST':
        form = MaintenanceStatusForm(request.POST, instance=req)
        if form.is_valid():
            form.save()
            messages.success(request, 'Request updated.')
            return redirect('maintenance_list')
    else:
        form = MaintenanceStatusForm(instance=req)
    return render(request, 'core/maintenance_form.html', {'form': form, 'req': req})

def maintenance_create(request):
    if request.method == 'POST':
        form = MaintenanceRequestForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Maintenance request submitted.')
            return redirect('maintenance_list')
    else:
        form = MaintenanceRequestForm()
    return render(request, 'core/maintenance_create.html', {'form': form})

# ---------- Resident Portal ----------
def register_resident(request):
    if request.method == 'POST':
        form = ResidentRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Registration successful! Welcome!")
            return redirect('resident_dashboard')
    else:
        form = ResidentRegistrationForm()
    return render(request, 'core/register.html', {'form': form})

def custom_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            if user.is_staff:
                return redirect('/admin/')
            elif hasattr(user, 'resident_profile'):
                return redirect('resident_dashboard')
            else:
                return redirect('/')
        else:
            messages.error(request, 'Invalid username or password.')
    return render(request, 'registration/login.html')

# ---------- FIX 2: Updated logout with success message ----------
def custom_logout(request):
    logout(request)
    messages.success(request, "You have been logged out successfully.")
    return redirect('/')

@login_required
def resident_dashboard(request):
    if not hasattr(request.user, 'resident_profile'):
        messages.error(request, "Resident profile not found.")
        return redirect('home')
    profile = request.user.resident_profile
    property_obj = profile.property
    fees = Fee.objects.filter(property=property_obj).order_by('-due_date') if property_obj else []
    total_due = sum(fee.amount for fee in fees if fee.status != 'paid')
    announcements = Announcement.objects.all().order_by('-created_at')[:5]
    maintenance_requests = MaintenanceRequest.objects.filter(property=property_obj).order_by('-created_at') if property_obj else []
    context = {
        'profile': profile,
        'property': property_obj,
        'fees': fees,
        'total_due': total_due,
        'announcements': announcements,
        'maintenance_requests': maintenance_requests,
    }
    return render(request, 'core/resident_dashboard.html', context)

# ---------- Parking ----------
@login_required
@user_passes_test(is_manager)
def parking_list(request):
    spots = ParkingSpot.objects.all().order_by('spot_number')
    properties = Property.objects.filter(status='occupied')
    return render(request, 'core/parking_list.html', {'spots': spots, 'properties': properties})

@login_required
@user_passes_test(is_manager)
def assign_parking(request, spot_id):
    spot = get_object_or_404(ParkingSpot, id=spot_id)
    if request.method == 'POST':
        property_id = request.POST.get('property')
        if property_id:
            spot.property_id = property_id
        else:
            spot.property = None
        spot.save()
        messages.success(request, f'Parking spot {spot.spot_number} updated.')
        return redirect('parking_list')
    return render(request, 'core/assign_parking.html', {'spot': spot, 'properties': Property.objects.filter(status='occupied')})

# ---------- Resident views for Fees & Parking Map ----------
@login_required
def my_fees(request):
    fees = []
    if hasattr(request.user, 'resident_profile') and request.user.resident_profile.property:
        property_obj = request.user.resident_profile.property
        fees = Fee.objects.filter(property=property_obj).order_by('-due_date')
    return render(request, 'core/my_fees.html', {'fees': fees})

@login_required
def parking_map(request):
    spots = ParkingSpot.objects.all().order_by('spot_number')
    return render(request, 'core/parking_map.html', {'spots': spots})

# ---------- Two‑way Chat (Conversations) ----------
@login_required
def conversations_list(request):
    if is_manager(request.user):
        convos = Conversation.objects.all().order_by('-updated_at')
    else:
        convos = Conversation.objects.filter(resident=request.user).order_by('-updated_at')
    return render(request, 'core/conversations_list.html', {'conversations': convos})

@login_required
def conversation_detail(request, convo_id):
    conv = get_object_or_404(Conversation, id=convo_id)
    if not (is_manager(request.user) or conv.resident == request.user):
        messages.error(request, "Access denied.")
        return redirect('conversations_list')

    if request.method == 'POST':
        form = ChatMessageForm(request.POST)
        if form.is_valid():
            msg = form.save(commit=False)
            msg.conversation = conv
            msg.sender = request.user
            msg.save()
            conv.updated_at = timezone.now()
            conv.save()
            messages.success(request, "Message sent.")
            return redirect('conversation_detail', convo_id=conv.id)
    else:
        form = ChatMessageForm()

    messages_list = conv.messages.all().order_by('created_at')
    return render(request, 'core/conversation_detail.html', {
        'conversation': conv,
        'messages': messages_list,
        'form': form
    })

@login_required
def start_conversation(request):
    if request.method == 'POST':
        form = StartConversationForm(request.user, request.POST)
        if form.is_valid():
            to_user = form.cleaned_data['recipient']
            subject = form.cleaned_data['subject']
            message = form.cleaned_data['message']
            # Get or create private conversation
            conv = PrivateConversation.objects.filter(participants=request.user).filter(participants=to_user).first()
            if not conv:
                conv = PrivateConversation.objects.create()
                conv.participants.add(request.user, to_user)
            PrivateMessage.objects.create(
                conversation=conv,
                sender=request.user,
                content=message
            )
            messages.success(request, f"Message sent to {to_user.username}.")
            return redirect('private_chat', username=to_user.username)
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = StartConversationForm(request.user)
    return render(request, 'core/start_conversation.html', {'form': form})

# ---------- New Social Features (Profile, Friends, Private Chat) ----------
@login_required
def profile_view(request, username=None):
    if username:
        target_user = get_object_or_404(User, username=username)
    else:
        target_user = request.user
    profile, created = UserProfile.objects.get_or_create(user=target_user)
    is_friend = Friendship.objects.filter(
        Q(from_user=request.user, to_user=target_user, status='accepted') |
        Q(from_user=target_user, to_user=request.user, status='accepted')
    ).exists()
    friend_request_sent = Friendship.objects.filter(from_user=request.user, to_user=target_user, status='pending').exists()
    friend_request_received = Friendship.objects.filter(from_user=target_user, to_user=request.user, status='pending').exists()
    context = {
        'target_user': target_user,
        'profile': profile,
        'is_friend': is_friend,
        'friend_request_sent': friend_request_sent,
        'friend_request_received': friend_request_received,
    }
    return render(request, 'core/profile.html', context)

@login_required
def edit_profile(request):
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated.')
            return redirect('profile_view', username=request.user.username)
    else:
        form = UserProfileForm(instance=profile)
    return render(request, 'core/edit_profile.html', {'form': form})

@login_required
def send_friend_request(request, username):
    to_user = get_object_or_404(User, username=username)
    if to_user == request.user:
        messages.error(request, "You cannot send a friend request to yourself.")
        return redirect('profile_view', username=username)
    Friendship.objects.get_or_create(from_user=request.user, to_user=to_user, defaults={'status': 'pending'})
    messages.success(request, f"Friend request sent to {to_user.username}.")
    return redirect('profile_view', username=username)

@login_required
def friend_requests(request):
    received = Friendship.objects.filter(to_user=request.user, status='pending').select_related('from_user')
    sent = Friendship.objects.filter(from_user=request.user, status='pending').select_related('to_user')
    return render(request, 'core/friend_requests.html', {'received': received, 'sent': sent})

@login_required
def respond_friend_request(request, request_id, action):
    friendship = get_object_or_404(Friendship, id=request_id, to_user=request.user, status='pending')
    if action == 'accept':
        friendship.status = 'accepted'
        friendship.save()
        # Create a private conversation between these two users if none exists
        conv = PrivateConversation.objects.filter(participants=request.user).filter(participants=friendship.from_user)
        if not conv.exists():
            conv = PrivateConversation.objects.create()
            conv.participants.add(request.user, friendship.from_user)
        messages.success(request, f"You are now friends with {friendship.from_user.username}.")
    elif action == 'reject':
        friendship.delete()
        messages.info(request, f"Friend request from {friendship.from_user.username} rejected.")
    return redirect('friend_requests')

@login_required
def friend_list(request):
    # Get accepted friends
    friends = Friendship.objects.filter(
        Q(from_user=request.user, status='accepted') | Q(to_user=request.user, status='accepted')
    ).select_related('from_user', 'to_user')
    friend_users = set()
    for f in friends:
        if f.from_user == request.user:
            friend_users.add(f.to_user)
        else:
            friend_users.add(f.from_user)
    # Suggestions: all users except self and existing friends
    suggestions = User.objects.exclude(id=request.user.id).exclude(id__in=[u.id for u in friend_users])
    return render(request, 'core/friend_list.html', {
        'friends': friend_users,
        'suggestions': suggestions
    })

@login_required
def private_chat(request, username):
    other_user = get_object_or_404(User, username=username)
    # Ensure they are friends (or allow admin to chat with anyone)
    is_friend = Friendship.objects.filter(
        Q(from_user=request.user, to_user=other_user, status='accepted') |
        Q(from_user=other_user, to_user=request.user, status='accepted')
    ).exists()
    if not is_friend and not request.user.is_staff:
        messages.error(request, "You can only chat with your friends.")
        return redirect('profile_view', username=username)
    # Get or create private conversation
    conv = PrivateConversation.objects.filter(participants=request.user).filter(participants=other_user).first()
    if not conv:
        conv = PrivateConversation.objects.create()
        conv.participants.add(request.user, other_user)
    if request.method == 'POST':
        form = PrivateMessageForm(request.POST)
        if form.is_valid():
            msg = form.save(commit=False)
            msg.conversation = conv
            msg.sender = request.user
            msg.save()
            conv.updated_at = timezone.now()
            conv.save()
            return redirect('private_chat', username=other_user.username)
    else:
        form = PrivateMessageForm()
    messages_list = conv.messages.all().order_by('timestamp')
    return render(request, 'core/private_chat.html', {
        'other_user': other_user,
        'messages': messages_list,
        'form': form,
        'conversation': conv,
    })

@login_required
def search_users(request):
    query = request.GET.get('q', '')
    users = User.objects.exclude(id=request.user.id)
    if query:
        users = users.filter(
            Q(username__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query)
        )
    # Mark which ones are already friends
    friend_ids = Friendship.objects.filter(
        Q(from_user=request.user, status='accepted') | Q(to_user=request.user, status='accepted')
    ).values_list('from_user_id', 'to_user_id')
    friend_set = set()
    for f_id, t_id in friend_ids:
        friend_set.add(f_id)
        friend_set.add(t_id)
    for u in users:
        u.is_friend = u.id in friend_set
    return render(request, 'core/search_users.html', {'users': users, 'query': query})