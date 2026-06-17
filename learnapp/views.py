from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.http import FileResponse, Http404, JsonResponse, HttpResponseNotAllowed
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.core.paginator import Paginator
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from django.db.models import Q
from .models import Course, Video, CourseFile, Enrollment, VideoProgress, Category, Test, Question, Answer, TestAttempt, UserAnswer, LiveSession, ChatMessage
from .forms import CourseForm, VideoForm, CourseFileForm, TestForm, QuestionForm, AnswerForm, LiveSessionForm, ContactAdminForm
from secondapp.decorators import admin_required

User = get_user_model()


def course_list(request):
    # Show all published courses to all visitors
    courses = Course.objects.filter(is_published=True)
    categories = Category.objects.all()
    
    category_filter = request.GET.get('category')
    if category_filter:
        courses = courses.filter(category_id=category_filter)
    
    paginator = Paginator(courses, 9)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'course_list.html', {
        'page_obj': page_obj,
        'categories': categories,
        'selected_category': category_filter
    })


def course_detail(request, course_id):
    course = get_object_or_404(Course, id=course_id, is_published=True)
    is_enrolled = False
    if request.user.is_authenticated:
        is_enrolled = Enrollment.objects.filter(user=request.user, course=course).exists()
    
    # Split learning outcomes and requirements into lists
    learning_outcomes_list = [line.strip() for line in course.learning_outcomes.split('\n') if line.strip()] if course.learning_outcomes else []
    requirements_list = [line.strip() for line in course.requirements.split('\n') if line.strip()] if course.requirements else []
    
    return render(request, 'course_detail.html', {
        'course': course,
        'is_enrolled': is_enrolled,
        'learning_outcomes_list': learning_outcomes_list,
        'requirements_list': requirements_list
    })


@login_required
def enroll_course(request, course_id):
    course = get_object_or_404(Course, id=course_id, is_published=True)
    
    if Enrollment.objects.filter(user=request.user, course=course).exists():
        messages.info(request, 'You are already enrolled in this course.')
        return redirect('course_detail', course_id=course.id)
    
    # Enroll directly - payment removed, access controlled by admin
    Enrollment.objects.create(user=request.user, course=course)
    messages.success(request, 'Successfully enrolled in the course!')
    return redirect('course_learning', course_id=course.id)


def contact_admin(request, course_id):
    course = get_object_or_404(Course, id=course_id, is_published=True)
    
    if request.method == 'POST':
        form = ContactAdminForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data['name']
            email = form.cleaned_data['email']
            message = form.cleaned_data['message']
            
            # Prepare email content
            subject = f'Course Inquiry: {course.title}'
            email_message = f'''
Name: {name}
Email: {email}
Course: {course.title}
Price: ₹{course.price}

Message:
{message}
'''
            
            # Send email to admin
            try:
                send_mail(
                    subject,
                    email_message,
                    settings.EMAIL_HOST_USER,
                    [settings.EMAIL_HOST_USER],  # Send to admin email
                    fail_silently=False,
                )
                messages.success(request, 'Your message has been sent to the administrator.')
            except Exception as e:
                messages.error(request, 'There was an error sending your message. Please try again.')
            
            return redirect('course_detail', course_id=course.id)
    else:
        form = ContactAdminForm()
    
    return render(request, 'contact_admin.html', {
        'form': form,
        'course': course
    })


@login_required
def course_learning(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    enrollment = get_object_or_404(Enrollment, user=request.user, course=course)
    
    videos = course.videos.all()
    files = course.files.all()
    tests = course.tests.all()
    live_sessions = course.live_sessions.all()
    
    # Group content by day
    days = {}
    for video in videos:
        if video.day not in days:
            days[video.day] = {'videos': [], 'files': [], 'tests': [], 'live_sessions': []}
        days[video.day]['videos'].append(video)
    
    for file in files:
        if file.day not in days:
            days[file.day] = {'videos': [], 'files': [], 'tests': [], 'live_sessions': []}
        days[file.day]['files'].append(file)
    
    for test in tests:
        if test.day not in days:
            days[test.day] = {'videos': [], 'files': [], 'tests': [], 'live_sessions': []}
        days[test.day]['tests'].append(test)
    
    for session in live_sessions:
        if session.day not in days:
            days[session.day] = {'videos': [], 'files': [], 'tests': [], 'live_sessions': []}
        days[session.day]['live_sessions'].append(session)
    
    # Sort days
    sorted_days = dict(sorted(days.items()))
    
    # Get first video or selected video
    video_id = request.GET.get('video')
    if video_id:
        current_video = get_object_or_404(Video, id=video_id, course=course)
    else:
        current_video = videos.first()
    
    # Get video progress for current video
    video_progress = None
    if current_video:
        video_progress = VideoProgress.objects.filter(
            user=request.user, 
            video=current_video
        ).first()
    
    # Get user's test attempts
    test_attempts = TestAttempt.objects.filter(user=request.user, test__course=course)
    
    return render(request, 'course_learning.html', {
        'course': course,
        'enrollment': enrollment,
        'days': sorted_days,
        'current_video': current_video,
        'video_progress': video_progress,
        'test_attempts': test_attempts
    })


@login_required
def update_video_progress(request, video_id):
    video = get_object_or_404(Video, id=video_id)
    enrollment = get_object_or_404(Enrollment, user=request.user, course=video.course)
    
    if request.method == 'POST':
        watched_duration = int(request.POST.get('watched_duration', 0))
        is_completed = request.POST.get('is_completed') == 'true'
        
        progress, created = VideoProgress.objects.get_or_create(
            user=request.user,
            video=video,
            defaults={'watched_duration': watched_duration, 'is_completed': is_completed}
        )
        
        if not created:
            progress.watched_duration = watched_duration
            progress.is_completed = is_completed
            progress.save()
        
        # Update overall course progress
        total_videos = video.course.videos.count()
        completed_videos = VideoProgress.objects.filter(
            user=request.user,
            video__course=video.course,
            is_completed=True
        ).count()
        
        enrollment.progress = int((completed_videos / total_videos) * 100) if total_videos > 0 else 0
        if enrollment.progress == 100:
            enrollment.is_completed = True
        enrollment.save()
    
    return redirect(f"{reverse('course_learning', kwargs={'course_id': video.course.id})}?video={video.id}")


@login_required
def download_file(request, file_id):
    file_obj = get_object_or_404(CourseFile, id=file_id)
    
    # Check if user is enrolled in the course
    if not Enrollment.objects.filter(user=request.user, course=file_obj.course).exists():
        raise Http404("File not found")
    
    # Download is now completely disabled for all users
    messages.error(request, 'Downloading is disabled. You can only view files within the platform.')
    return redirect('course_learning', course_id=file_obj.course.id)


@login_required
def view_file(request, file_id):
    file_obj = get_object_or_404(CourseFile, id=file_id)
    
    # Check if user is enrolled in the course
    if not Enrollment.objects.filter(user=request.user, course=file_obj.course).exists():
        raise Http404("File not found")
    
    # Check if streaming is allowed
    if not file_obj.allow_streaming:
        messages.error(request, 'This file is not available for viewing.')
        return redirect('course_learning', course_id=file_obj.course.id)
    
    # Serve the file inline for viewing (no download)
    try:
        response = FileResponse(file_obj.file.open('rb'), as_attachment=False)
        response['Content-Disposition'] = f'inline; filename="{file_obj.title}"'
        response['X-Content-Type-Options'] = 'nosniff'
        response['Content-Security-Policy'] = "default-src 'self'"
        return response
    except Exception as e:
        messages.error(request, 'Error viewing file.')
        return redirect('course_learning', course_id=file_obj.course.id)


@login_required
def protected_video_stream(request, video_id):
    video = get_object_or_404(Video, id=video_id)
    
    # Check if user is enrolled in the course
    if not Enrollment.objects.filter(user=request.user, course=video.course).exists():
        raise Http404("Video not found")
    
    # Check if streaming is allowed
    if not video.allow_streaming:
        messages.error(request, 'This video is not available for viewing.')
        return redirect('course_learning', course_id=video.course.id)
    
    # Serve the video file with streaming headers (no download)
    try:
        response = FileResponse(
            video.video_file.open('rb'),
            content_type='video/mp4'
        )
        response['Content-Disposition'] = 'inline'
        response['X-Content-Type-Options'] = 'nosniff'
        response['Accept-Ranges'] = 'bytes'
        response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response['Pragma'] = 'no-cache'
        response['Expires'] = '0'
        return response
    except Exception as e:
        messages.error(request, 'Error streaming video.')
        return redirect('course_learning', course_id=video.course.id)


# Admin Views
@admin_required
def admin_course_list(request):
    courses = Course.objects.all()
    return render(request, 'admin_course_list.html', {'courses': courses})


@admin_required
def admin_course_create(request):
    if request.method == 'POST':
        form = CourseForm(request.POST, request.FILES)
        if form.is_valid():
            course = form.save(commit=False)
            course.instructor = request.user
            course.save()
            messages.success(request, 'Course created successfully.')
            return redirect('admin_course_detail', course_id=course.id)
    else:
        form = CourseForm()
    
    return render(request, 'admin_course_form.html', {'form': form, 'action': 'Create'})


@admin_required
def admin_course_edit(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    
    if request.method == 'POST':
        form = CourseForm(request.POST, request.FILES, instance=course)
        if form.is_valid():
            form.save()
            messages.success(request, 'Course updated successfully.')
            return redirect('admin_course_detail', course_id=course.id)
    else:
        form = CourseForm(instance=course)
    
    return render(request, 'admin_course_form.html', {'form': form, 'action': 'Edit', 'course': course})


@admin_required
def admin_course_detail(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    videos = course.videos.all()
    files = course.files.all()
    enrollments = course.enrollments.all()
    
    # Get all users who are not enrolled in this course
    enrolled_user_ids = enrollments.values_list('user_id', flat=True)
    available_users = User.objects.exclude(id__in=enrolled_user_ids).filter(user_type='user')
    
    return render(request, 'admin_course_detail.html', {
        'course': course,
        'videos': videos,
        'files': files,
        'enrollments': enrollments,
        'available_users': available_users
    })


@admin_required
def admin_video_upload(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    
    if request.method == 'POST':
        form = VideoForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                video = form.save(commit=False)
                video.course = course
                video.save()
                messages.success(request, 'Video uploaded successfully.')
                return redirect('admin_course_detail', course_id=course.id)
            except Exception as e:
                messages.error(request, f'Error uploading video: {str(e)}')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = VideoForm()
    
    return render(request, 'admin_video_upload.html', {'form': form, 'course': course})


@admin_required
def admin_video_edit(request, video_id):
    video = get_object_or_404(Video, id=video_id)
    
    if request.method == 'POST':
        form = VideoForm(request.POST, request.FILES, instance=video)
        if form.is_valid():
            form.save()
            messages.success(request, 'Video updated successfully.')
            return redirect('admin_course_detail', course_id=video.course.id)
    else:
        form = VideoForm(instance=video)
    
    return render(request, 'admin_video_upload.html', {'form': form, 'course': video.course, 'video': video})


@admin_required
def admin_video_delete(request, video_id):
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])
    
    try:
        video = get_object_or_404(Video, id=video_id)
        course_id = video.course.id
        
        # Delete video file using Django's built-in delete method
        if video.video_file:
            video.video_file.delete(save=False)
        
        # Delete thumbnail file using Django's built-in delete method
        if video.thumbnail:
            video.thumbnail.delete(save=False)
        
        video.delete()
        messages.success(request, 'Video deleted successfully.')
    except Exception as e:
        messages.error(request, f'Error deleting video: {str(e)}')
        return redirect('admin_course_detail', course_id=course_id)
    
    return redirect('admin_course_detail', course_id=course_id)


@admin_required
def admin_start_live(request, video_id):
    video = get_object_or_404(Video, id=video_id)
    
    # Generate a unique stream key
    import uuid
    video.live_stream_key = str(uuid.uuid4())
    video.is_live = True
    video.save()
    
    messages.success(request, 'Live stream started successfully.')
    return redirect('admin_course_detail', course_id=video.course.id)


@admin_required
def admin_stop_live(request, video_id):
    video = get_object_or_404(Video, id=video_id)
    video.is_live = False
    video.live_stream_key = None
    video.save()
    
    messages.success(request, 'Live stream stopped successfully.')
    return redirect('admin_course_detail', course_id=video.course.id)


@admin_required
def admin_file_upload(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    
    if request.method == 'POST':
        form = CourseFileForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                file = form.save(commit=False)
                file.course = course
                file.save()
                messages.success(request, 'File uploaded successfully.')
                return redirect('admin_course_detail', course_id=course.id)
            except Exception as e:
                messages.error(request, f'Error uploading file: {str(e)}')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = CourseFileForm()
    
    return render(request, 'admin_file_upload.html', {'form': form, 'course': course})


@admin_required
def admin_file_delete(request, file_id):
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])
    
    try:
        course_file = get_object_or_404(CourseFile, id=file_id)
        course_id = course_file.course.id
        
        # Delete file using Django's built-in delete method
        if course_file.file:
            course_file.file.delete(save=False)
        
        course_file.delete()
        messages.success(request, 'File deleted successfully.')
    except Exception as e:
        messages.error(request, f'Error deleting file: {str(e)}')
        return redirect('admin_course_detail', course_id=course_id)
    
    return redirect('admin_course_detail', course_id=course_id)


@admin_required
def admin_enroll_user(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        if user_id:
            user = get_object_or_404(User, id=user_id)
            
            if Enrollment.objects.filter(user=user, course=course).exists():
                messages.info(request, f'{user.username} is already enrolled in this course.')
            else:
                Enrollment.objects.create(user=user, course=course)
                messages.success(request, f'Successfully enrolled {user.username} in {course.title}.')
        else:
            messages.error(request, 'Please select a user to enroll.')
    
    return redirect('admin_course_detail', course_id=course.id)


@login_required
def live_stream(request, video_id):
    video = get_object_or_404(Video, id=video_id)
    
    if not video.is_live:
        messages.error(request, 'This stream is not currently live.')
        return redirect('course_detail', course_id=video.course.id)
    
    enrollment = get_object_or_404(Enrollment, user=request.user, course=video.course)
    
    return render(request, 'live_stream.html', {
        'video': video,
        'enrollment': enrollment
    })


# Test Management Views
@login_required
def create_test(request, course_id):
    if request.user.user_type != 'admin':
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    
    course = get_object_or_404(Course, id=course_id)
    
    if request.method == 'POST':
        form = TestForm(request.POST)
        if form.is_valid():
            test = form.save(commit=False)
            test.course = course
            test.save()
            messages.success(request, 'Test created successfully.')
            return redirect('admin_course_detail', course_id=course.id)
    else:
        form = TestForm()
    
    return render(request, 'create_test.html', {
        'form': form,
        'course': course
    })


@login_required
def add_question(request, test_id):
    if request.user.user_type != 'admin':
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    
    test = get_object_or_404(Test, id=test_id)
    
    if request.method == 'POST':
        form = QuestionForm(request.POST)
        if form.is_valid():
            question = form.save(commit=False)
            question.test = test
            question.save()
            messages.success(request, 'Question added successfully.')
            return redirect('test_detail', test_id=test.id)
    else:
        form = QuestionForm()
    
    return render(request, 'add_question.html', {
        'form': form,
        'test': test
    })


@login_required
def edit_question(request, question_id):
    if request.user.user_type != 'admin':
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    
    question = get_object_or_404(Question, id=question_id)
    
    if request.method == 'POST':
        form = QuestionForm(request.POST, instance=question)
        if form.is_valid():
            form.save()
            messages.success(request, 'Question updated successfully.')
            return redirect('test_detail', test_id=question.test.id)
    else:
        form = QuestionForm(instance=question)
    
    return render(request, 'edit_question.html', {
        'form': form,
        'question': question
    })


@login_required
def delete_question(request, question_id):
    if request.user.user_type != 'admin':
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    
    question = get_object_or_404(Question, id=question_id)
    test_id = question.test.id
    
    if request.method == 'POST':
        question.delete()
        messages.success(request, 'Question deleted successfully.')
        return redirect('test_detail', test_id=test_id)
    
    return render(request, 'delete_question.html', {
        'question': question
    })


@login_required
def add_answer(request, question_id):
    if request.user.user_type != 'admin':
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    
    question = get_object_or_404(Question, id=question_id)
    
    if request.method == 'POST':
        form = AnswerForm(request.POST)
        if form.is_valid():
            answer = form.save(commit=False)
            answer.question = question
            answer.save()
            messages.success(request, 'Answer added successfully.')
            return redirect('test_detail', test_id=question.test.id)
    else:
        form = AnswerForm()
    
    return render(request, 'add_answer.html', {
        'form': form,
        'question': question
    })


@login_required
def edit_answer(request, answer_id):
    if request.user.user_type != 'admin':
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    
    answer = get_object_or_404(Answer, id=answer_id)
    
    if request.method == 'POST':
        form = AnswerForm(request.POST, instance=answer)
        if form.is_valid():
            form.save()
            messages.success(request, 'Answer updated successfully.')
            return redirect('test_detail', test_id=answer.question.test.id)
    else:
        form = AnswerForm(instance=answer)
    
    return render(request, 'edit_answer.html', {
        'form': form,
        'answer': answer
    })


@login_required
def delete_answer(request, answer_id):
    if request.user.user_type != 'admin':
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    
    answer = get_object_or_404(Answer, id=answer_id)
    test_id = answer.question.test.id
    
    if request.method == 'POST':
        answer.delete()
        messages.success(request, 'Answer deleted successfully.')
        return redirect('test_detail', test_id=test_id)
    
    return render(request, 'delete_answer.html', {
        'answer': answer
    })


@login_required
def test_detail(request, test_id):
    test = get_object_or_404(Test, id=test_id)
    questions = test.questions.all()
    
    return render(request, 'test_detail.html', {
        'test': test,
        'questions': questions
    })


@login_required
def edit_test(request, test_id):
    if request.user.user_type != 'admin':
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    
    test = get_object_or_404(Test, id=test_id)
    
    if request.method == 'POST':
        form = TestForm(request.POST, instance=test)
        if form.is_valid():
            form.save()
            messages.success(request, 'Test updated successfully.')
            return redirect('test_detail', test_id=test.id)
    else:
        form = TestForm(instance=test)
    
    return render(request, 'edit_test.html', {
        'form': form,
        'test': test
    })


@login_required
def delete_test(request, test_id):
    if request.user.user_type != 'admin':
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    
    test = get_object_or_404(Test, id=test_id)
    course_id = test.course.id
    
    if request.method == 'POST':
        # Log the deletion action
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f'Test deleted by admin {request.user.username}: Test ID {test.id}, Title: {test.title}')
        
        # Delete the test (this will cascade delete questions, answers, attempts, etc.)
        test.delete()
        
        messages.success(request, 'Test deleted successfully.')
        return redirect('admin_course_detail', course_id=course_id)
    
    return render(request, 'delete_test.html', {
        'test': test
    })


@login_required
def take_test(request, test_id):
    test = get_object_or_404(Test, id=test_id)
    
    # Check if user is enrolled in the course
    enrollment = Enrollment.objects.filter(user=request.user, course=test.course).first()
    if not enrollment:
        messages.error(request, 'You must be enrolled in this course to take the test.')
        return redirect('course_detail', course_id=test.course.id)
    
    # Check attempts
    attempts = TestAttempt.objects.filter(user=request.user, test=test).count()
    remaining_attempts = test.max_attempts - attempts
    
    if remaining_attempts <= 0:
        messages.info(request, f'You have used all your {test.max_attempts} attempts for this test.')
        return redirect('test_result', attempt_id=TestAttempt.objects.filter(user=request.user, test=test).first().id)
    
    if request.method == 'POST':
        # Create test attempt
        attempt = TestAttempt.objects.create(
            user=request.user,
            test=test,
            total_questions=test.questions.count()
        )
        
        # Redirect to first question
        first_question = test.questions.first()
        if first_question:
            return redirect('take_test_question', attempt_id=attempt.id, question_id=first_question.id)
        else:
            messages.error(request, 'No questions available for this test.')
            return redirect('course_detail', course_id=test.course.id)
    
    # Show pre-test popup information
    return render(request, 'take_test_confirm.html', {
        'test': test,
        'attempts': attempts,
        'remaining_attempts': remaining_attempts,
        'total_questions': test.questions.count(),
        'total_marks': test.questions.count(),
        'time_per_question': test.time_per_question
    })


@login_required
def take_test_question(request, attempt_id, question_id):
    attempt = get_object_or_404(TestAttempt, id=attempt_id, user=request.user)
    question = get_object_or_404(Question, id=question_id, test=attempt.test)
    
    # Check if attempt is already completed
    if attempt.completed_at:
        messages.info(request, 'This test has already been completed.')
        return redirect('test_result', attempt_id=attempt.id)
    
    # Get all questions for this test
    all_questions = list(attempt.test.questions.all().order_by('order'))
    current_index = all_questions.index(question)
    
    if request.method == 'POST':
        # Save answer
        answer_id = request.POST.get('answer_id')
        if answer_id:
            answer = get_object_or_404(Answer, id=answer_id)
            UserAnswer.objects.create(
                attempt=attempt,
                question=question,
                selected_answer=answer,
                is_correct=answer.is_correct
            )
        else:
            # No answer selected - mark as incorrect
            UserAnswer.objects.create(
                attempt=attempt,
                question=question,
                selected_answer=None,
                is_correct=False
            )
        
        # Move to next question or submit
        if current_index < len(all_questions) - 1:
            next_question = all_questions[current_index + 1]
            return redirect('take_test_question', attempt_id=attempt.id, question_id=next_question.id)
        else:
            # Calculate final score
            attempt.correct_answers = UserAnswer.objects.filter(attempt=attempt, is_correct=True).count()
            attempt.score = (attempt.correct_answers / attempt.total_questions) * 100 if attempt.total_questions > 0 else 0
            attempt.is_passed = attempt.score >= attempt.test.passing_score
            attempt.completed_at = timezone.now()
            attempt.save()
            
            messages.success(request, 'Test completed successfully.')
            return redirect('test_result', attempt_id=attempt.id)
    
    return render(request, 'take_test_question.html', {
        'attempt': attempt,
        'question': question,
        'answers': question.answers.all().order_by('order'),
        'current_index': current_index + 1,
        'total_questions': len(all_questions),
        'time_per_question': attempt.test.time_per_question,
        'progress_percentage': int((current_index / len(all_questions)) * 100)
    })


@login_required
def test_result(request, attempt_id):
    # Admin can view all results, users can only view their own
    if request.user.user_type == 'admin':
        attempt = get_object_or_404(TestAttempt, id=attempt_id)
    else:
        attempt = get_object_or_404(TestAttempt, id=attempt_id, user=request.user)
    
    return render(request, 'test_result.html', {
        'attempt': attempt
    })


@login_required
def view_user_test_results(request, course_id):
    if request.user.user_type != 'admin':
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    
    course = get_object_or_404(Course, id=course_id)
    attempts = TestAttempt.objects.filter(test__course=course)
    
    return render(request, 'user_test_results.html', {
        'course': course,
        'attempts': attempts
    })


@login_required
def admin_test_results(request):
    if request.user.user_type != 'admin':
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    
    # Get filter parameters
    selected_test = request.GET.get('test', '')
    selected_course = request.GET.get('course', '')
    selected_status = request.GET.get('status', '')
    student_search = request.GET.get('student', '')
    
    # Get all tests and courses for filter dropdowns
    tests = Test.objects.all()
    courses = Course.objects.all()
    
    # Build query for results
    results_queryset = TestAttempt.objects.all()
    
    # Apply filters
    if selected_test:
        results_queryset = results_queryset.filter(test_id=selected_test)
    if selected_course:
        results_queryset = results_queryset.filter(test__course_id=selected_course)
    if student_search:
        results_queryset = results_queryset.filter(
            Q(student__username__icontains=student_search) |
            Q(student__first_name__icontains=student_search) |
            Q(student__last_name__icontains=student_search) |
            Q(student__email__icontains=student_search)
        )
    
    # Calculate statistics
    all_students = User.objects.filter(user_type='student').count()
    completed_count = results_queryset.filter(status='completed').count()
    pending_count = results_queryset.filter(status='pending').count()
    
    # Calculate scores
    completed_attempts = results_queryset.filter(status='completed')
    scores = [attempt.score for attempt in completed_attempts if attempt.score is not None]
    
    average_score = round(sum(scores) / len(scores)) if scores else 0
    highest_score = max(scores) if scores else 0
    lowest_score = min(scores) if scores else 0
    
    # Calculate pass percentage
    passed_count = len([s for s in scores if s >= 50])
    pass_percentage = round((passed_count / len(scores)) * 100) if scores else 0
    
    stats = {
        'total_students': all_students,
        'completed': completed_count,
        'pending': pending_count,
        'average_score': average_score,
        'highest_score': highest_score,
        'lowest_score': lowest_score,
        'pass_percentage': pass_percentage
    }
    
    # Prepare results with status and passed info
    results = []
    for attempt in results_queryset:
        status = 'pending'
        if attempt.status == 'completed':
            status = 'completed'
        elif attempt.status == 'in_progress':
            status = 'in_progress'
        
        passed = False
        if attempt.score and attempt.score >= 50:
            passed = True
        
        results.append({
            'id': attempt.id,
            'student': attempt.student,
            'test': attempt.test,
            'status': status,
            'score': attempt.score,
            'passed': passed,
            'attempts_used': attempt.attempt_number,
            'max_attempts': attempt.test.max_attempts or 3
        })
    
    # Apply status filter if specified
    if selected_status:
        if selected_status == 'completed':
            results = [r for r in results if r['status'] == 'completed']
        elif selected_status == 'pending':
            results = [r for r in results if r['status'] == 'pending']
        elif selected_status == 'in_progress':
            results = [r for r in results if r['status'] == 'in_progress']
    
    # Pagination
    paginator = Paginator(results, 10)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'admin_test_results.html', {
        'tests': tests,
        'courses': courses,
        'selected_test': selected_test,
        'selected_course': selected_course,
        'selected_status': selected_status,
        'student_search': student_search,
        'stats': stats,
        'results': page_obj,
        'page_obj': page_obj
    })


@login_required
def admin_test_result_detail(request, result_id):
    if request.user.user_type != 'admin':
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    attempt = get_object_or_404(TestAttempt, id=result_id)
    
    # Calculate detailed statistics
    total_questions = attempt.test.questions.count()
    correct_answers = attempt.answers.filter(is_correct=True).count()
    wrong_answers = attempt.answers.filter(is_correct=False).count()
    percentage = attempt.score if attempt.score else 0
    
    data = {
        'student_name': attempt.student.get_full_name() or attempt.student.username,
        'student_email': attempt.student.email,
        'test_name': attempt.test.title,
        'attempt_number': attempt.attempt_number,
        'time_taken': str(attempt.time_taken) if attempt.time_taken else 'N/A',
        'questions_attempted': correct_answers + wrong_answers,
        'correct_answers': correct_answers,
        'wrong_answers': wrong_answers,
        'percentage': percentage,
        'passed': percentage >= 50 if percentage else False
    }
    
    return JsonResponse(data)


# Live Session Views
@login_required
def create_live_session(request, course_id):
    if request.user.user_type != 'admin':
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    
    course = get_object_or_404(Course, id=course_id)
    
    if request.method == 'POST':
        form = LiveSessionForm(request.POST)
        if form.is_valid():
            session = form.save(commit=False)
            session.course = course
            session.save()
            messages.success(request, 'Live session created successfully.')
            return redirect('admin_course_detail', course_id=course.id)
    else:
        form = LiveSessionForm()
    
    return render(request, 'create_live_session.html', {
        'form': form,
        'course': course
    })


@login_required
def toggle_live_session(request, session_id):
    if request.user.user_type != 'admin':
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    
    session = get_object_or_404(LiveSession, id=session_id)
    session.is_active = not session.is_active
    session.save()
    
    if session.is_active:
        messages.success(request, f'Live session "{session.title}" is now LIVE.')
    else:
        messages.success(request, f'Live session "{session.title}" has been stopped.')
    
    return redirect('admin_course_detail', course_id=session.course.id)


@login_required
def delete_live_session(request, session_id):
    if request.user.user_type != 'admin':
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])
    
    try:
        session = get_object_or_404(LiveSession, id=session_id)
        course_id = session.course.id
        
        session.delete()
        messages.success(request, 'Live session deleted successfully.')
    except Exception as e:
        messages.error(request, f'Error deleting live session: {str(e)}')
        return redirect('admin_course_detail', course_id=course_id)
    
    return redirect('admin_course_detail', course_id=course_id)


@login_required
def watch_live_session(request, session_id):
    session = get_object_or_404(LiveSession, id=session_id)
    
    # Check if user is enrolled in the course
    enrollment = Enrollment.objects.filter(user=request.user, course=session.course).first()
    if not enrollment:
        messages.error(request, 'You must be enrolled in this course to watch the live session.')
        return redirect('course_detail', course_id=session.course.id)
    
    return render(request, 'watch_live_session.html', {
        'session': session,
        'enrollment': enrollment
    })


@login_required
def live_chat(request, session_id):
    session = get_object_or_404(LiveSession, id=session_id)
    
    # Check if user is enrolled in the course
    enrollment = Enrollment.objects.filter(user=request.user, course=session.course).first()
    if not enrollment:
        messages.error(request, 'You must be enrolled in this course to participate in the chat.')
        return redirect('course_detail', course_id=session.course.id)
    
    if request.method == 'POST':
        message = request.POST.get('message')
        recipient_id = request.POST.get('recipient_id')
        message_type = request.POST.get('message_type', 'user_to_admin')
        
        recipient = None
        if recipient_id:
            recipient = get_object_or_404(User, id=recipient_id)
        
        ChatMessage.objects.create(
            live_session=session,
            sender=request.user,
            recipient=recipient,
            message_type=message_type,
            message=message
        )
        
        return redirect('live_chat', session_id=session.id)
    
    messages = ChatMessage.objects.filter(live_session=session)
    
    return render(request, 'live_chat.html', {
        'session': session,
        'messages': messages
    })
