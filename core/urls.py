from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    # Home & Property
    path('', views.home, name='home'),
    path('add-property/', views.add_property, name='add-property'),

    # Announcements
    path('announcements/', views.announcement_list, name='announcement_list'),
    path('announcement/create/', views.announcement_create, name='announcement_create'),
    path('announcement/delete/<int:pk>/', views.announcement_delete, name='announcement_delete'),

    # Fees & Payments (Manager)
    path('fees/', views.fee_list, name='fee_list'),
    path('fees/create/', views.fee_create, name='fee_create'),
    path('fees/payment/<int:fee_id>/', views.record_payment, name='record_payment'),

    # Resident views
    path('my-fees/', views.my_fees, name='my_fees'),
    path('parking-map/', views.parking_map, name='parking_map'),

    # Maintenance
    path('maintenance/', views.maintenance_list, name='maintenance_list'),
    path('maintenance/create/', views.maintenance_create, name='maintenance_create'),
    path('maintenance/update/<int:pk>/', views.maintenance_update, name='maintenance_update'),

    # Parking Management (Manager only)
    path('parking/', views.parking_list, name='parking_list'),
    path('parking/assign/<int:spot_id>/', views.assign_parking, name='assign_parking'),

    # Resident Portal
    path('register/', views.register_resident, name='register_resident'),
    path('login/', views.custom_login, name='custom_login'),
    path('logout/', views.custom_logout, name='logout'),
    path('resident-dashboard/', views.resident_dashboard, name='resident_dashboard'),

    # Chat System (Conversations)
    path('conversations/', views.conversations_list, name='conversations_list'),
    path('conversation/<int:convo_id>/', views.conversation_detail, name='conversation_detail'),
    path('start-conversation/', views.start_conversation, name='start_conversation'),

    # Social & Messaging
    path('profile/<str:username>/', views.profile_view, name='profile_view'),
    path('profile/', views.profile_view, name='my_profile'),
    path('edit-profile/', views.edit_profile, name='edit_profile'),
    path('send-friend-request/<str:username>/', views.send_friend_request, name='send_friend_request'),
    path('friend-requests/', views.friend_requests, name='friend_requests'),
    path('respond-friend-request/<int:request_id>/<str:action>/', views.respond_friend_request, name='respond_friend_request'),
    path('friends/', views.friend_list, name='friend_list'),
    path('chat/<str:username>/', views.private_chat, name='private_chat'),
    path('search-users/', views.search_users, name='search_users'),
]

# Password reset URLs (use your custom templates)
urlpatterns += [
    path('password-reset/',
         auth_views.PasswordResetView.as_view(template_name='registration/password_reset_form.html'),
         name='password_reset'),
    path('password-reset/done/',
         auth_views.PasswordResetDoneView.as_view(template_name='registration/password_reset_done.html'),
         name='password_reset_done'),
    path('reset/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(template_name='registration/password_reset_confirm.html'),
         name='password_reset_confirm'),
    path('reset/done/',
         auth_views.PasswordResetCompleteView.as_view(template_name='registration/password_reset_complete.html'),
         name='password_reset_complete'),
]