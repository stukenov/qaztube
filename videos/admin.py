from django.contrib import admin
from .models import Video

@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    list_display = ('title', 'transcoding_status', 'transcoding_progress', 'created_at', 'views')
    list_filter = ('transcoding_status', 'created_at')
    search_fields = ('title', 'description')
    readonly_fields = ('transcoding_status', 'transcoding_progress', 'transcoding_error')
    
    def get_readonly_fields(self, request, obj=None):
        if obj and obj.transcoding_status == 'processing':
            return self.readonly_fields + ('video_file',)
        return self.readonly_fields
