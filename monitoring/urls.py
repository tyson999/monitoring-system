from django.urls import path
from . import views

urlpatterns = [
    path('', views.welcome, name='welcome'),
    path('select-source/',views.select_source, name='select_source'),
    path('upload-excel/', views.upload_excel, name='upload_excel'),
    path('results/', views.results_page, name='results_page'),
    path("download-active/-", views.download_excel, name="download_active"),
    path("status/",views.status_page, name="status_page"),
    path("google-sheet/", views.google_sheet_input, name="google_sheet_input"),
    path("check-url/", views.check_single_url, name="check_single_url"),
    path("download-inactive/", views.download_inactive, name="download_inactive"),
    path("processing/", views.processing_page, name="processing_page"),
    path("run-processing/-", views.run_processing, name="run_processing"),



]
