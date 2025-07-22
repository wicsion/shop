from django.urls import path
from . import views

app_name = 'designer'

urlpatterns = [
    path('start/', views.custom_designer_start, name='custom_designer_start'),
    path('custom/', views.custom_designer_start, name='custom_designer'),  # Добавьте эту строку
    path('edit/<int:design_id>/', views.custom_designer_edit, name='custom_designer_edit'),
    path('save-element/', views.save_custom_element, name='save_custom_element'),
    path('delete-element/', views.delete_custom_element, name='delete_custom_element'),
    path('preview/<int:design_id>/', views.preview_custom_design, name='preview_custom_design'),
    path('save-order/', views.save_custom_design_order, name='save_custom_design_order'),
    path('save-color/', views.save_selected_color, name='save_selected_color'),

    path('add-custom-color/', views.add_custom_color, name='add_custom_color'),
]