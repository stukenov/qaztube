import os
import subprocess
import threading
import logging
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, CreateView
from django.urls import reverse_lazy
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.decorators import method_decorator
from django.conf import settings
from .models import Video

# Get logger for this module
logger = logging.getLogger('videos')

# Create your views here.

class VideoListView(ListView):
    model = Video
    template_name = 'videos/video_list.html'
    context_object_name = 'videos'
    paginate_by = 12

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Добавляем featured video если есть
        try:
            context['featured_video'] = Video.objects.filter(
                transcoding_status='completed'
            ).order_by('-views').first()
        except:
            context['featured_video'] = None
        return context

class VideoDetailView(DetailView):
    model = Video
    template_name = 'videos/video_detail.html'
    context_object_name = 'video'
    slug_field = 'uid'
    slug_url_kwarg = 'uid'

    def get_object(self):
        video = super().get_object()
        video.views += 1
        video.save()
        return video

@method_decorator(staff_member_required, name='dispatch')
class VideoUploadView(CreateView):
    model = Video
    template_name = 'videos/video_upload.html'
    fields = []  # Пустой список, так как это теперь информационная страница

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name)
