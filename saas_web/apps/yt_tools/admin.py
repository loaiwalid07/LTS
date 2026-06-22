from django.contrib import admin

from .models import ClipJob, ClipSegment


class ClipSegmentInline(admin.TabularInline):
    model = ClipSegment
    fields = ('title', 'start_time', 'end_time', 'duration', 'is_downloaded')
    readonly_fields = ('duration',)
    extra = 0


@admin.register(ClipJob)
class ClipJobAdmin(admin.ModelAdmin):
    list_display = ('video_title', 'user', 'status', 'n_clips', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('video_title', 'youtube_url', 'user__username')
    inlines = [ClipSegmentInline]


@admin.register(ClipSegment)
class ClipSegmentAdmin(admin.ModelAdmin):
    list_display = ('title', 'job', 'start_time', 'end_time', 'duration', 'is_downloaded')
    list_filter = ('is_downloaded',)
