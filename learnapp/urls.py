from django.urls import path
from . import views

urlpatterns = [
    # User views
    path('', views.course_list, name='course_list'),
    path('course/<int:course_id>/', views.course_detail, name='course_detail'),
    path('course/<int:course_id>/enroll/', views.enroll_course, name='enroll_course'),
    path('course/<int:course_id>/learn/', views.course_learning, name='course_learning'),
    path('course/<int:course_id>/contact/', views.contact_admin, name='contact_admin'),
    path('video/<int:video_id>/progress/', views.update_video_progress, name='update_video_progress'),
    path('video/<int:video_id>/stream/', views.protected_video_stream, name='protected_video_stream'),
    path('file/<int:file_id>/download/', views.download_file, name='download_file'),
    path('file/<int:file_id>/view/', views.view_file, name='view_file'),
    path('live/<int:video_id>/', views.live_stream, name='live_stream'),
    
    # Admin views
    path('admin/courses/', views.admin_course_list, name='admin_course_list'),
    path('admin/course/create/', views.admin_course_create, name='admin_course_create'),
    path('admin/course/<int:course_id>/edit/', views.admin_course_edit, name='admin_course_edit'),
    path('admin/course/<int:course_id>/', views.admin_course_detail, name='admin_course_detail'),
    path('admin/course/<int:course_id>/video/upload/', views.admin_video_upload, name='admin_video_upload'),
    path('admin/video/<int:video_id>/edit/', views.admin_video_edit, name='admin_video_edit'),
    path('admin/video/<int:video_id>/delete/', views.admin_video_delete, name='admin_video_delete'),
    path('admin/video/<int:video_id>/start-live/', views.admin_start_live, name='admin_start_live'),
    path('admin/video/<int:video_id>/stop-live/', views.admin_stop_live, name='admin_stop_live'),
    path('admin/course/<int:course_id>/file/upload/', views.admin_file_upload, name='admin_file_upload'),
    path('file/<int:file_id>/delete/', views.admin_file_delete, name='admin_file_delete'),
    path('admin/course/<int:course_id>/enroll/', views.admin_enroll_user, name='admin_enroll_user'),
    path('admin/test-results/', views.admin_test_results, name='admin_test_results'),
    path('admin/test-result/<int:result_id>/', views.admin_test_result_detail, name='admin_test_result_detail'),
    
    # Test management URLs
    path('admin/course/<int:course_id>/test/create/', views.create_test, name='create_test'),
    path('test/<int:test_id>/edit/', views.edit_test, name='edit_test'),
    path('test/<int:test_id>/delete/', views.delete_test, name='delete_test'),
    path('test/<int:test_id>/question/add/', views.add_question, name='add_question'),
    path('question/<int:question_id>/edit/', views.edit_question, name='edit_question'),
    path('question/<int:question_id>/delete/', views.delete_question, name='delete_question'),
    path('question/<int:question_id>/answer/add/', views.add_answer, name='add_answer'),
    path('answer/<int:answer_id>/edit/', views.edit_answer, name='edit_answer'),
    path('answer/<int:answer_id>/delete/', views.delete_answer, name='delete_answer'),
    path('test/<int:test_id>/', views.test_detail, name='test_detail'),
    path('test/<int:test_id>/take/', views.take_test, name='take_test'),
    path('test/attempt/<int:attempt_id>/question/<int:question_id>/', views.take_test_question, name='take_test_question'),
    path('test/result/<int:attempt_id>/', views.test_result, name='test_result'),
    path('admin/course/<int:course_id>/test-results/', views.view_user_test_results, name='view_user_test_results'),
    path('admin/test-results/', views.admin_test_results, name='admin_test_results'),
    path('admin/test-result/<int:result_id>/', views.admin_test_result_detail, name='admin_test_result_detail'),
    
    # Live session URLs
    path('admin/course/<int:course_id>/live-session/create/', views.create_live_session, name='create_live_session'),
    path('admin/live-session/<int:session_id>/toggle/', views.toggle_live_session, name='toggle_live_session'),
    path('live-session/<int:session_id>/watch/', views.watch_live_session, name='watch_live_session'),
    path('live-session/<int:session_id>/chat/', views.live_chat, name='live_chat'),
    path('live-session/<int:session_id>/delete/', views.delete_live_session, name='delete_live_session'),
]
