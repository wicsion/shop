from django.urls import path

from .views import SilhouetteEditView
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
    path('admin/designer/template/<int:template_id>/edit-mask/',
         views.edit_mask,
         name='edit-mask'),



    path('admin/designer/silhouette/<int:pk>/edit/',
         SilhouetteEditView.as_view(),
         name='silhouette-edit'),

    path('add-custom-color/', views.add_custom_color, name='add_custom_color'),
    path('save-order/', views.save_custom_design_order, name='save_custom_design_order'),
    path('update-item/<int:item_id>/', views.update_custom_item, name='update_custom_item'),
    path('remove-item/<int:item_id>/', views.remove_custom_item, name='remove_custom_item'),
]