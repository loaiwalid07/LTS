from django import forms

from .models import ClipJob


class ClipGenerateForm(forms.ModelForm):
    """Form to submit a new clip generation job."""

    class Meta:
        model = ClipJob
        fields = ('youtube_url', 'n_clips', 'max_duration', 'custom_focus')
        widgets = {
            'youtube_url': forms.URLInput(attrs={
                'class': 'auth-input',
                'placeholder': 'https://youtube.com/watch?v=...',
            }),
            'n_clips': forms.NumberInput(attrs={
                'class': 'auth-input',
                'min': 1,
                'max': 20,
            }),
            'max_duration': forms.NumberInput(attrs={
                'class': 'auth-input',
                'min': 10,
                'max': 300,
            }),
            'custom_focus': forms.TextInput(attrs={
                'class': 'auth-input',
                'placeholder': 'e.g. funny moments, key insights, tutorial steps',
            }),
        }
        labels = {
            'youtube_url': 'YouTube URL',
            'n_clips': 'Number of clips',
            'max_duration': 'Max clip duration (seconds)',
            'custom_focus': 'Focus area (optional)',
        }
        help_texts = {
            'n_clips': 'How many clips to generate (1–20)',
            'max_duration': 'Maximum length per clip in seconds (10–300)',
            'custom_focus': 'Tell the AI what to look for',
        }

    def clean_youtube_url(self):
        url = self.cleaned_data['youtube_url']
        # Basic validation — check it looks like a YouTube URL
        valid_domains = ('youtube.com', 'youtu.be', 'm.youtube.com')
        if not any(domain in url for domain in valid_domains):
            raise forms.ValidationError('Please enter a valid YouTube URL.')
        return url
