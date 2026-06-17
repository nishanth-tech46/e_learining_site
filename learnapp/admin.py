from django.contrib import admin
from .models import Category, Course, Video, CourseFile, Enrollment, VideoProgress, Test


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_at']
    search_fields = ['name']


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ['title', 'instructor', 'category', 'price', 'is_published', 'created_at']
    list_filter = ['is_published', 'category', 'created_at']
    search_fields = ['title', 'description', 'instructor__username']
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(instructor=request.user)


@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    list_display = ['title', 'course', 'duration', 'is_live', 'allow_download', 'allow_streaming', 'order', 'created_at']
    list_filter = ['is_live', 'allow_download', 'allow_streaming', 'course', 'created_at']
    search_fields = ['title', 'course__title']
    fieldsets = (
        (None, {
            'fields': ('course', 'title', 'description', 'video_file', 'thumbnail')
        }),
        ('Video Settings', {
            'fields': ('duration', 'order', 'day', 'is_live', 'live_stream_key')
        }),
        ('Permissions', {
            'fields': ('allow_download', 'allow_streaming')
        }),
    )


@admin.register(CourseFile)
class CourseFileAdmin(admin.ModelAdmin):
    list_display = ['title', 'course', 'file_type', 'download_permission', 'allow_download', 'allow_streaming', 'order', 'created_at']
    list_filter = ['file_type', 'download_permission', 'allow_download', 'allow_streaming', 'course', 'created_at']
    search_fields = ['title', 'course__title']
    fieldsets = (
        (None, {
            'fields': ('course', 'title', 'file', 'file_type', 'description')
        }),
        ('File Settings', {
            'fields': ('order', 'day')
        }),
        ('Permissions', {
            'fields': ('download_permission', 'allow_download', 'allow_streaming')
        }),
    )


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ['user', 'course', 'enrolled_at', 'is_completed', 'progress']
    list_filter = ['is_completed', 'enrolled_at', 'course']
    search_fields = ['user__username', 'course__title']
    filter_horizontal = []


@admin.register(VideoProgress)
class VideoProgressAdmin(admin.ModelAdmin):
    list_display = ['user', 'video', 'watched_duration', 'is_completed', 'last_watched_at']
    list_filter = ['is_completed', 'last_watched_at']
    search_fields = ['user__username', 'video__title']


@admin.register(Test)
class TestAdmin(admin.ModelAdmin):
    list_display = ['title', 'course', 'duration', 'passing_score', 'allow_download', 'allow_streaming', 'day', 'created_at']
    list_filter = ['allow_download', 'allow_streaming', 'course', 'created_at']
    search_fields = ['title', 'course__title']
    fieldsets = (
        (None, {
            'fields': ('course', 'title', 'description')
        }),
        ('Test Settings', {
            'fields': ('duration', 'passing_score', 'day', 'max_attempts', 'time_per_question')
        }),
        ('Permissions', {
            'fields': ('allow_download', 'allow_streaming')
        }),
    )
