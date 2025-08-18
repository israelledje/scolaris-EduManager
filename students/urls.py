from django.urls import path
from django.conf import settings
from django.conf.urls.static import static

from .views import (
    StudentListView, StudentDetailView,
    StudentCreateHtmxView, StudentUpdateHtmxView, StudentDeleteHtmxView,
    StudentHistoryCreateHtmxView, StudentHistoryUpdateHtmxView, StudentHistoryDeleteHtmxView,
    GuardianCreateHtmxView, GuardianUpdateHtmxView, GuardianDeleteHtmxView,
    DocumentCreateHtmxView, DocumentUpdateHtmxView, DocumentDeleteHtmxView,
    TranchePaymentCreateHtmxView, TranchePaymentUpdateHtmxView, TranchePaymentDeleteHtmxView,
    FeeDiscountCreateHtmxView, FeeDiscountUpdateHtmxView, FeeDiscountDeleteHtmxView,
    ScholarshipCreateHtmxView, ScholarshipUpdateHtmxView, ScholarshipDeleteHtmxView,
    EvaluationCreateHtmxView, EvaluationUpdateHtmxView, EvaluationDeleteHtmxView,
    AttendanceCreateHtmxView, AttendanceUpdateHtmxView, AttendanceDeleteHtmxView,
    SanctionCreateHtmxView, SanctionUpdateHtmxView, SanctionDeleteHtmxView,
)

app_name = 'students'

urlpatterns = [
    path('', StudentListView.as_view(), name='student_list'),
    path('create/', StudentCreateHtmxView.as_view(), name='student_create_htmx'),
    path('<int:pk>/', StudentDetailView.as_view(), name='student_detail'),
    path('<int:pk>/update/', StudentUpdateHtmxView.as_view(), name='student_update_htmx'),
    path('<int:pk>/delete/', StudentDeleteHtmxView.as_view(), name='student_delete_htmx'),
    # Historique des classes (HTMX)
    path('<int:student_id>/history/create/', StudentHistoryCreateHtmxView.as_view(), name='student_history_create'),
    path('history/<int:pk>/update/', StudentHistoryUpdateHtmxView.as_view(), name='student_history_update'),
    path('history/<int:pk>/delete/', StudentHistoryDeleteHtmxView.as_view(), name='student_history_delete'),
    # Responsables (HTMX)
    path('<int:student_id>/guardian/create/', GuardianCreateHtmxView.as_view(), name='guardian_create_htmx'),
    path('guardian/<int:pk>/update/', GuardianUpdateHtmxView.as_view(), name='guardian_update_htmx'),
    path('guardian/<int:pk>/delete/', GuardianDeleteHtmxView.as_view(), name='guardian_delete_htmx'),
    # Documents (HTMX)
    path('<int:student_id>/document/create/', DocumentCreateHtmxView.as_view(), name='document_create'),
    path('document/<int:pk>/update/', DocumentUpdateHtmxView.as_view(), name='document_update'),
    path('document/<int:pk>/delete/', DocumentDeleteHtmxView.as_view(), name='document_delete'),
    # Paiements (HTMX)
    path('<int:student_id>/tranchepayment/create/', TranchePaymentCreateHtmxView.as_view(), name='tranchepayment_create'),
    path('tranchepayment/<int:pk>/update/', TranchePaymentUpdateHtmxView.as_view(), name='tranchepayment_update'),
    path('tranchepayment/<int:pk>/delete/', TranchePaymentDeleteHtmxView.as_view(), name='tranchepayment_delete'),
    # Remises (HTMX)
    path('<int:student_id>/feediscount/create/', FeeDiscountCreateHtmxView.as_view(), name='feediscount_create'),
    path('feediscount/<int:pk>/update/', FeeDiscountUpdateHtmxView.as_view(), name='feediscount_update'),
    path('feediscount/<int:pk>/delete/', FeeDiscountDeleteHtmxView.as_view(), name='feediscount_delete'),
    # Bourses (HTMX)
    path('<int:student_id>/scholarship/create/', ScholarshipCreateHtmxView.as_view(), name='scholarship_create'),
    path('scholarship/<int:pk>/update/', ScholarshipUpdateHtmxView.as_view(), name='scholarship_update'),
    path('scholarship/<int:pk>/delete/', ScholarshipDeleteHtmxView.as_view(), name='scholarship_delete'),
    # Évaluations/notes (HTMX)
    path('<int:student_id>/evaluation/create/', EvaluationCreateHtmxView.as_view(), name='evaluation_create'),
    path('evaluation/<int:pk>/update/', EvaluationUpdateHtmxView.as_view(), name='evaluation_update'),
    path('evaluation/<int:pk>/delete/', EvaluationDeleteHtmxView.as_view(), name='evaluation_delete'),
    # Présences (HTMX)
    path('<int:student_id>/attendance/create/', AttendanceCreateHtmxView.as_view(), name='attendance_create'),
    path('attendance/<int:pk>/update/', AttendanceUpdateHtmxView.as_view(), name='attendance_update'),
    path('attendance/<int:pk>/delete/', AttendanceDeleteHtmxView.as_view(), name='attendance_delete'),
    # Sanctions (HTMX)
    path('<int:student_id>/sanction/create/', SanctionCreateHtmxView.as_view(), name='sanction_create'),
    path('sanction/<int:pk>/update/', SanctionUpdateHtmxView.as_view(), name='sanction_update'),
    path('sanction/<int:pk>/delete/', SanctionDeleteHtmxView.as_view(), name='sanction_delete'),
]
if settings.DEBUG:
         urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)