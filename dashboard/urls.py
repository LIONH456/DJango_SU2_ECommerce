from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.index, name='dashboard'),
    path('sliders/', views.sliders_list, name='sliders_list'),
    path('sliders/create/', views.slider_create, name='slider_create'),
    path('sliders/<int:slider_id>/edit/', views.slider_edit, name='slider_edit'),
    path('sliders/<int:slider_id>/delete/', views.slider_delete, name='slider_delete'),
    path('sliders/<int:slider_id>/toggle-status/', views.slider_toggle_status, name='slider_toggle_status'),
    path('sliders/reorder/', views.slider_reorder, name='slider_reorder'),
]