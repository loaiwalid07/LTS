from django.views.generic import TemplateView


class IndexView(TemplateView):
    """Public landing / marketing page."""

    template_name = 'core/index.html'


class AboutView(TemplateView):
    """About page."""

    template_name = 'core/about.html'
