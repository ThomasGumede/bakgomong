from django.urls import path
from .views.checkout import checkout
from contributions.views.member_contr import add_member_contribution, my_member_contributions_list, member_contribution, delete_member_contribution, member_contributions_list, update_member_contribution
from .views.contributions import get_contribution, get_contributions, add_contribution, update_contribution, delete_contribution

app_name = "contributions"
urlpatterns = [
    path('contributions', get_contributions, name='get-contributions'),
    path('contributions/create', add_contribution, name='add-contribution'),
    path('contribution/<contribution_slug>', get_contribution, name='get-contribution'),
    path('contribution/update/<contribution_slug>', update_contribution, name='update-contribution'),
    path('contribution/delete/<contribution_slug>', delete_contribution, name='delete-contribution'),
    
    path('member-invoices/', member_contributions_list, name='member-contributions-list'),
    path('member-invoices/family=<family_slug>', member_contributions_list, name='member-contributions-list-by-slug'),
    path('my-invoices/@<username>', my_member_contributions_list, name='my-contributions'),
    path('member-invoice/<uuid:id>', member_contribution, name='member-contribution'),
    path('member-invoices/add/', add_member_contribution, name='add-member-contribution'),
    path('member-invoices/<uuid:id>/edit/', update_member_contribution, name='update-member-contribution'),
    path('member-invoices/<uuid:id>/delete/', delete_member_contribution, name='delete-member-contribution'),
    
    path('payment/checkout/<uuid:id>', checkout, name='checkout'),
]
