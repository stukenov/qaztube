from django.urls import path
from . import views

app_name = 'videos'

urlpatterns = [
    path('', views.VideoListView.as_view(), name='video_list'),
    path('video/<str:uid>/', views.VideoDetailView.as_view(), name='video_detail'),
    path('upload/', views.VideoUploadView.as_view(), name='video_upload'),
] 