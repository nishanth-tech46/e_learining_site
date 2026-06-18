from django import forms
from .models import Course, Video, CourseFile, Category, Test, Question, Answer, LiveSession


class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ['title', 'description', 'category', 'thumbnail', 'price', 'duration', 'level', 'lessons_count', 'learning_outcomes', 'requirements', 'is_published']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 5}),
            'learning_outcomes': forms.Textarea(attrs={'rows': 5, 'placeholder': 'Enter each learning outcome on a new line'}),
            'requirements': forms.Textarea(attrs={'rows': 5, 'placeholder': 'Enter each requirement on a new line'}),
        }


class VideoForm(forms.ModelForm):
    class Meta:
        model = Video
        fields = ['title', 'description', 'video_file', 'thumbnail', 'duration', 'order', 'day']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }


class CourseFileForm(forms.ModelForm):
    class Meta:
        model = CourseFile
        fields = ['title', 'file', 'file_type', 'description', 'order', 'day']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }


class TestForm(forms.ModelForm):
    class Meta:
        model = Test
        fields = ['title', 'description', 'duration', 'passing_score', 'day', 'max_attempts', 'time_per_question']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }


class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ['question_text', 'question_type', 'order', 'marks']
        widgets = {
            'question_text': forms.Textarea(attrs={'rows': 3}),
        }


class AnswerForm(forms.ModelForm):
    class Meta:
        model = Answer
        fields = ['answer_text', 'is_correct', 'order']


class QuestionWithOptionsForm(forms.Form):
    question_text = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}), required=True)
    option_1 = forms.CharField(max_length=500, required=True, label='Option 1')
    option_2 = forms.CharField(max_length=500, required=True, label='Option 2')
    option_3 = forms.CharField(max_length=500, required=True, label='Option 3')
    option_4 = forms.CharField(max_length=500, required=True, label='Option 4')
    correct_answer = forms.ChoiceField(
        choices=[
            ('1', 'Option 1'),
            ('2', 'Option 2'),
            ('3', 'Option 3'),
            ('4', 'Option 4'),
        ],
        required=True,
        label='Correct Answer'
    )
    marks = forms.IntegerField(min_value=1, required=True, initial=1)
    order = forms.IntegerField(min_value=1, required=True, initial=1)


class LiveSessionForm(forms.ModelForm):
    class Meta:
        model = LiveSession
        fields = ['title', 'description', 'stream_url', 'scheduled_at', 'duration', 'is_active', 'day']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'scheduled_at': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }


class ContactAdminForm(forms.Form):
    name = forms.CharField(max_length=100, label='Full Name')
    email = forms.EmailField(label='Email Address')
    message = forms.CharField(widget=forms.Textarea(attrs={'rows': 5}), label='Message')
