from django.urls import path
from . import views

app_name = 'documents'

urlpatterns = [
    path('student/<int:student_id>/', views.document_list, name='document_list'),
    path('student/<int:student_id>/create/', views.document_create, name='document_create'),
    path('<int:pk>/update/', views.document_update, name='document_update'),
    path('<int:pk>/delete/', views.document_delete, name='document_delete'),
    path('<int:pk>/download/', views.document_download, name='document_download'),
    path('student/<int:student_id>/search/', views.document_search, name='document_search'),
] 