from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils import timezone
from django.views.generic import TemplateView

from apps.yt_tools.models import ClipJob


class HomeView(LoginRequiredMixin, TemplateView):
    """Main dashboard view — shows clip stats and recent jobs."""

    template_name = 'dashboard/home.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user

        jobs = ClipJob.objects.filter(user=user)
        today = timezone.now().date()

        ctx['total_clips'] = sum(j.clips.count() for j in jobs.filter(status='done'))
        ctx['jobs_today'] = jobs.filter(created_at__date=today).count()
        ctx['recent_jobs'] = jobs.filter(status='done').count()
        ctx['jobs'] = jobs[:10]
        ctx['storage_used'] = '—'

        return ctx
