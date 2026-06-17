from django.db import models
from django.contrib.auth import get_user_model
from django.db.models.signals import pre_delete, post_delete
from django.dispatch import receiver

User = get_user_model()


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Course(models.Model):
    LEVEL_CHOICES = (
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
    )
    
    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    instructor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='courses')
    thumbnail = models.ImageField(upload_to='course_thumbnails/', blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    duration = models.CharField(max_length=100, help_text='e.g., "8 weeks" or "40 hours"', blank=True)
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES, default='beginner')
    lessons_count = models.PositiveIntegerField(default=0, help_text='Number of lessons/lessons')
    learning_outcomes = models.TextField(blank=True, help_text='What students will learn (one per line)')
    requirements = models.TextField(blank=True, help_text='Prerequisites (one per line)')
    is_published = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title


class Video(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='videos')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    video_file = models.FileField(upload_to='videos/')
    thumbnail = models.ImageField(upload_to='video_thumbnails/', blank=True, null=True)
    duration = models.PositiveIntegerField(help_text='Duration in seconds', blank=True, null=True)
    order = models.PositiveIntegerField(default=0)
    day = models.PositiveIntegerField(default=1, help_text='Day number for this content')
    is_live = models.BooleanField(default=False)
    live_stream_key = models.CharField(max_length=200, blank=True, null=True)
    allow_download = models.BooleanField(default=False, help_text='Allow users to download this video')
    allow_streaming = models.BooleanField(default=True, help_text='Allow users to stream this video')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['day', 'order']

    def __str__(self):
        return self.title


class CourseFile(models.Model):
    FILE_TYPE_CHOICES = (
        ('pdf', 'PDF'),
        ('doc', 'Document'),
        ('image', 'Image'),
        ('other', 'Other'),
    )
    
    DOWNLOAD_PERMISSION_CHOICES = (
        ('download', 'Download Allowed'),
        ('view_only', 'View Only'),
    )
    
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='files')
    title = models.CharField(max_length=200)
    file = models.FileField(upload_to='course_files/')
    file_type = models.CharField(max_length=10, choices=FILE_TYPE_CHOICES, default='other')
    description = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=0)
    day = models.PositiveIntegerField(default=1, help_text='Day number for this content')
    download_permission = models.CharField(max_length=10, choices=DOWNLOAD_PERMISSION_CHOICES, default='view_only')
    allow_download = models.BooleanField(default=False, help_text='Allow users to download this file')
    allow_streaming = models.BooleanField(default=True, help_text='Allow users to view this file')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['day', 'order']

    def __str__(self):
        return self.title


class Enrollment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='enrollments')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrollments')
    enrolled_at = models.DateTimeField(auto_now_add=True)
    is_completed = models.BooleanField(default=False)
    progress = models.PositiveIntegerField(default=0, help_text='Progress percentage')

    class Meta:
        unique_together = ['user', 'course']

    def __str__(self):
        return f"{self.user.username} - {self.course.title}"


class VideoProgress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    video = models.ForeignKey(Video, on_delete=models.CASCADE)
    watched_duration = models.PositiveIntegerField(default=0, help_text='Watched duration in seconds')
    is_completed = models.BooleanField(default=False)
    last_watched_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['user', 'video']

    def __str__(self):
        return f"{self.user.username} - {self.video.title}"


class Test(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='tests')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    duration = models.PositiveIntegerField(help_text='Duration in minutes', default=30)
    passing_score = models.PositiveIntegerField(default=60, help_text='Passing score percentage')
    day = models.PositiveIntegerField(default=1, help_text='Day number for this test')
    max_attempts = models.PositiveIntegerField(default=1, help_text='Maximum number of attempts allowed')
    time_per_question = models.PositiveIntegerField(default=60, help_text='Time per question in seconds')
    allow_download = models.BooleanField(default=False, help_text='Allow users to download test questions')
    allow_streaming = models.BooleanField(default=True, help_text='Allow users to take this test')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['day']

    def __str__(self):
        return self.title


class Question(models.Model):
    QUESTION_TYPE_CHOICES = (
        ('mcq', 'Multiple Choice'),
        ('true_false', 'True/False'),
    )
    
    test = models.ForeignKey(Test, on_delete=models.CASCADE, related_name='questions')
    question_text = models.TextField()
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPE_CHOICES, default='mcq')
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.question_text[:50]


class Answer(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='answers')
    answer_text = models.CharField(max_length=500)
    is_correct = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.answer_text


class TestAttempt(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='test_attempts')
    test = models.ForeignKey(Test, on_delete=models.CASCADE, related_name='attempts')
    score = models.PositiveIntegerField(default=0)
    total_questions = models.PositiveIntegerField(default=0)
    correct_answers = models.PositiveIntegerField(default=0)
    is_passed = models.BooleanField(default=False)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ['user', 'test']

    def __str__(self):
        return f"{self.user.username} - {self.test.title}"


class UserAnswer(models.Model):
    attempt = models.ForeignKey(TestAttempt, on_delete=models.CASCADE, related_name='user_answers')
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    selected_answer = models.ForeignKey(Answer, on_delete=models.CASCADE, null=True, blank=True)
    is_correct = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['attempt', 'question']

    def __str__(self):
        return f"{self.attempt.user.username} - {self.question.question_text[:30]}"


class LiveSession(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='live_sessions')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    stream_url = models.URLField(blank=True, help_text='YouTube or other streaming URL')
    scheduled_at = models.DateTimeField()
    duration = models.PositiveIntegerField(help_text='Duration in minutes', default=60)
    is_active = models.BooleanField(default=False)
    day = models.PositiveIntegerField(default=1, help_text='Day number for this live session')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['day', 'scheduled_at']

    def __str__(self):
        return self.title


class ChatMessage(models.Model):
    MESSAGE_TYPE_CHOICES = (
        ('user_to_admin', 'User to Admin'),
        ('admin_to_all', 'Admin to All'),
        ('admin_to_user', 'Admin to User'),
    )
    
    live_session = models.ForeignKey(LiveSession, on_delete=models.CASCADE, related_name='chat_messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages', null=True, blank=True)
    message_type = models.CharField(max_length=20, choices=MESSAGE_TYPE_CHOICES, default='user_to_admin')
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.sender.username}: {self.message[:30]}"


# Signal handlers for automatic file cleanup
@receiver(pre_delete, sender=Course)
def delete_course_thumbnail(sender, instance, **kwargs):
    """Delete course thumbnail file when Course is deleted"""
    if instance.thumbnail:
        instance.thumbnail.delete(save=False)


@receiver(pre_delete, sender=Video)
def delete_video_files(sender, instance, **kwargs):
    """Delete video file and thumbnail when Video is deleted"""
    if instance.video_file:
        instance.video_file.delete(save=False)
    if instance.thumbnail:
        instance.thumbnail.delete(save=False)


@receiver(pre_delete, sender=CourseFile)
def delete_course_file(sender, instance, **kwargs):
    """Delete course file when CourseFile is deleted"""
    if instance.file:
        instance.file.delete(save=False)
