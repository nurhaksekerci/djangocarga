from django.urls import path
from . import views

app_name = 'tour'  # Namespace tanımı

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('password-reset/', views.password_reset_request, name='password_reset'),
    path('password-reset/confirm/<str:token>/', views.password_reset_verify, name='password_reset_confirm'),
    path('<str:model>/', views.generic_list_view, name='list'),
    path('<str:model>/<int:pk>/update/', views.generic_update_view, name='update'),
    path('<str:model>/<int:pk>/delete/', views.generic_delete_view, name='delete'),
    path('operation/create/', views.create_operation, name='create_operation'),
    path('operation/list/', views.operation_list, name='operation_list'),
    path('operation/<int:operation_id>/customer/create/', views.create_operation_customer, name='create_operation_customer'),
    path('operation/<int:operation_id>/sales-price/create/', views.create_operation_sales_price, name='create_operation_sales_price'),
    path('operation/<int:operation_id>/item/create/', views.create_operation_item, name='create_operation_item'),
    path('operation/<int:operation_id>/item/vehicle/create/', views.create_operation_item_vehicle, name='create_operation_item_vehicle'),
    path('operation/<int:operation_id>/item/no-vehicle/create/', views.create_operation_item_no_vehicle, name='create_operation_item_no_vehicle'),
    path('operation/<int:operation_id>/item/activity/create/', views.create_operation_item_activity, name='create_operation_item_activity'),
    path('operation/sub-item/other/create/', views.create_operation_sub_item_other_price, name='create_operation_sub_item_other_price'),
    path('operation/sub-item/guide/create/', views.create_operation_sub_item_guide, name='create_operation_sub_item_guide'),
    path('operation/sub-item/hotel/create/', views.create_operation_sub_item_hotel, name='create_operation_sub_item_hotel'),
    path('operation/sub-item/museum/create/', views.create_operation_sub_item_museum, name='create_operation_sub_item_museum'),
    path('operation/sub-item/tour/create/', views.create_operation_sub_item_tour, name='create_operation_sub_item_tour'),
    path('operation/sub-item/transfer/create/', views.create_operation_sub_item_transfer, name='create_operation_sub_item_transfer'),
    path('operation/sub-item/activity/create/', views.create_operation_sub_item_activity, name='create_operation_sub_item_activity'),
    path('sms/send/', views.send_sms, name='send_sms'),
    path('operation/jobs/', views.jobs, name='jobs'),
] 