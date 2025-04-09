from django.urls import path
from . import views

app_name = 'tour'  # Namespace tanımı

urlpatterns = [
    # Kullanıcı İşlemleri
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('password-reset/', views.password_reset_request, name='password_reset_request'),
    path('password-reset/verify/<str:uidb64>/<str:token>/', views.password_reset_verify, name='password_reset_verify'),
    # Generic Views
    path('list/<str:model>/', views.generic_list_view, name='list'),
    path('create/<str:model>/', views.generic_create_view, name='create'),
    path('detail/<str:model>/<int:pk>/', views.generic_detail_view, name='detail'),
    path('update/<str:model>/<int:pk>/', views.generic_update_view, name='update'),
    path('delete/<str:model>/<int:pk>/', views.generic_delete_view, name='delete'),
    path('export/<str:model>/', views.generic_export_view, name='export'),
    
    #Operation
    path('operation/<int:operation_id>/', views.operation, name='operation'),
    path('operation/update/<int:operation_id>/', views.operation_update, name='operation_update'),
    path('operation/toggle/<int:operation_id>/', views.toggle_operation, name='toggle_operation'),
    path('operation/customer/toggle/<int:operation_customer_id>/', views.toggle_operation_customer, name='toggle_operation_customer'),
    path('operation/sales_price/toggle/<int:operation_sales_price_id>/', views.toggle_operation_sales_price, name='toggle_operation_sales_price'),
    path('operation/day/toggle/<int:operation_day_id>/', views.toggle_operation_day, name='toggle_operation_day'),
    path('operation/item/toggle/<int:operation_item_id>/', views.toggle_operation_item, name='toggle_operation_item'),
    path('operation/sub_item/toggle/<int:operation_sub_item_id>/', views.toggle_operation_sub_item, name='toggle_operation_sub_item'),
    path('operation/customer/update/<int:operation_customer_id>/', views.operation_customer_update, name='operation_customer_update'),
    path('operation/sales_price/update/<int:operation_sales_price_id>/', views.operation_sales_price_update, name='operation_sales_price_update'),

    #Operation Item
    path('operation/day/<int:operation_day_id>/no_vehicle_activity_item_create/', views.no_vehicle_activity_item_create, name='no_vehicle_activity_item_create'),
    path('operation/day/<int:operation_day_id>/no_vehicle_tour_item_create/', views.no_vehicle_tour_item_create, name='no_vehicle_tour_item_create'),
    path('operation/day/<int:operation_day_id>/no_vehicle_guide_item_create/', views.no_vehicle_guide_item_create, name='no_vehicle_guide_item_create'),
    path('operation/day/<int:operation_day_id>/vehicle_item_create/', views.vehicle_item_create, name='vehicle_item_create'),

    #Operation Item Update
    path('operation/item/no_vehicle_activity_item_update/<int:operation_item_id>/', views.no_vehicle_activity_item_update, name='no_vehicle_activity_item_update'),
    path('operation/item/no_vehicle_tour_item_update/<int:operation_item_id>/', views.no_vehicle_tour_item_update, name='no_vehicle_tour_item_update'),
    path('operation/item/no_vehicle_guide_item_update/<int:operation_item_id>/', views.no_vehicle_guide_item_update, name='no_vehicle_guide_item_update'),
    path('operation/item/vehicle_item_update/<int:operation_item_id>/', views.vehicle_item_update, name='vehicle_item_update'),

    #Operation Sub Item
    path('operation/sub_item/tour_create/<int:operation_item_id>/', views.sub_item_tour_create, name='sub_item_tour_create'),
    path('operation/sub_item/transfer_create/<int:operation_item_id>/', views.sub_item_transfer_create, name='sub_item_transfer_create'),
    path('operation/sub_item/hotel_create/<int:operation_item_id>/', views.sub_item_hotel_create, name='sub_item_hotel_create'),
    path('operation/sub_item/activity_create/<int:operation_item_id>/', views.sub_item_activity_create, name='sub_item_activity_create'),
    path('operation/sub_item/museum_create/<int:operation_item_id>/', views.sub_item_museum_create, name='sub_item_museum_create'),
    path('operation/sub_item/guide_create/<int:operation_item_id>/', views.sub_item_guide_create, name='sub_item_guide_create'),
    path('operation/sub_item/other_price_create/<int:operation_item_id>/', views.sub_item_other_price_create, name='sub_item_other_price_create'),

    #Operation Sub Item Update
    path('operation/sub_item/tour_update/<int:operation_sub_item_id>/', views.sub_item_tour_update, name='sub_item_tour_update'),
    path('operation/sub_item/transfer_update/<int:operation_sub_item_id>/', views.sub_item_transfer_update, name='sub_item_transfer_update'),
    path('operation/sub_item/hotel_update/<int:operation_sub_item_id>/', views.sub_item_hotel_update, name='sub_item_hotel_update'),
    path('operation/sub_item/activity_update/<int:operation_sub_item_id>/', views.sub_item_activity_update, name='sub_item_activity_update'),
    path('operation/sub_item/museum_update/<int:operation_sub_item_id>/', views.sub_item_museum_update, name='sub_item_museum_update'),
    path('operation/sub_item/guide_update/<int:operation_sub_item_id>/', views.sub_item_guide_update, name='sub_item_guide_update'),
    path('operation/sub_item/other_price_update/<int:operation_sub_item_id>/', views.sub_item_other_price_update, name='sub_item_other_price_update'),

    #Operation Customer
    path('operation/<int:operation_id>/customer/create', views.operation_customer_create, name='operation_customer_create'),
    path('operation/<int:operation_id>/sales_price/create', views.operation_sales_price_create, name='operation_sales_price_create'),

    #Operation Create
    path('operation/create', views.operation_create, name='operation_create'),
    path('operation/list', views.operation_list, name='operation_list'),

    #Operation Jobs
    path('operation/jobs', views.operation_jobs, name='operation_jobs'),
    path('operation/jobs/vehicle_item_update/<int:operation_item_id>/', views.jobs_vehicle_item_update, name='jobs_vehicle_item_update'),
    path('operation/jobs/no_vehicle_tour_item_update/<int:operation_item_id>/', views.jobs_no_vehicle_tour_item_update, name='jobs_no_vehicle_tour_item_update'),
    path('operation/jobs/no_vehicle_activity_item_update/<int:operation_item_id>/', views.jobs_no_vehicle_activity_item_update, name='jobs_no_vehicle_activity_item_update'),
    path('operation/jobs/no_vehicle_guide_item_update/<int:operation_item_id>/', views.jobs_no_vehicle_guide_item_update, name='jobs_no_vehicle_guide_item_update'),
    path('operation/jobs/sub_item/hotel_update/<int:operation_sub_item_id>/', views.jobs_sub_item_hotel_update, name='jobs_sub_item_hotel_update'),
    path('operation/jobs/sub_item/activity_update/<int:operation_sub_item_id>/', views.jobs_sub_item_activity_update, name='jobs_sub_item_activity_update'),
    path('operation/jobs/sub_item/museum_update/<int:operation_sub_item_id>/', views.jobs_sub_item_museum_update, name='jobs_sub_item_museum_update'),
    path('operation/jobs/sub_item/guide_update/<int:operation_sub_item_id>/', views.jobs_sub_item_guide_update, name='jobs_sub_item_guide_update'),
    path('operation/jobs/sub_item/other_price_update/<int:operation_sub_item_id>/', views.jobs_sub_item_other_price_update, name='jobs_sub_item_other_price_update'),
    path('operation/jobs/sub_item/transfer_update/<int:operation_sub_item_id>/', views.jobs_sub_item_transfer_update, name='jobs_sub_item_transfer_update'),
    path('operation/jobs/sub_item/tour_update/<int:operation_sub_item_id>/', views.jobs_sub_item_tour_update, name='jobs_sub_item_tour_update'),
    path('operation/jobs/my', views.my_operation_jobs, name='my_operation_jobs'),
]   