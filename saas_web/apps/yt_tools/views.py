"""
Views for the VidSnap clip pipeline.
"""
import re
import threading

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, DetailView

from .forms import ClipGenerateForm
from .models import ClipJob, ClipSegment
from .services.analyzer import ask_gemini
from .services.clipper import download_and_cut_direct
from .services.logger import log
from .services.transcript import extract_video_id, get_free_transcript


# ══════════════════════════════════════════════════════════════════════════
# BACKGROUND PIPELINE
# ══════════════════════════════════════════════════════════════════════════

STEPS = [
    ('Extracting video ID from URL...', 5),
    ('Fetching transcript...', 20),
    ('Analyzing with Gemini AI...', 35),
    ('Saving clip segments...', 50),
    ('Downloading clip videos...', 70),
    ('Fetching video title...', 95),
]


def _set_step(job: ClipJob, label: str, pct: int):
    """Update the job's progress text + percentage, persist to DB."""
    job.progress_step = f'{pct}%|{label}'
    job.save(update_fields=['progress_step'])
    log.info('PROGRESS job=%d | %s (%d%%)', job.pk, label, pct)


def _process_job(job: ClipJob, api_key: str, cookies_path: str):
    """Run the full clip pipeline in a background thread."""
    log.info('=== PIPELINE START job=%d (url=%.80s) ===', job.pk, job.youtube_url)

    try:
        # ── Step 0 — mark as processing ────────────────────────────
        job.status = ClipJob.Status.PROCESSING
        _set_step(job, 'Starting...', 0)

        # ── Step 1 — extract video ID ───────────────────────────────
        _set_step(job, STEPS[0][0], STEPS[0][1])
        video_id = extract_video_id(job.youtube_url)
        if not video_id:
            raise ValueError('Could not extract video ID from URL')
        job.video_id = video_id
        job.save(update_fields=['video_id'])

        # ── Step 2 — fetch transcript ──────────────────────────────
        _set_step(job, STEPS[1][0], STEPS[1][1])
        transcript = get_free_transcript(video_id)
        if not transcript:
            raise ValueError(
                'Could not fetch transcript for this video. '
                'The video may not have captions, or the transcript service is unavailable.'
            )

        # ── Step 3 — AI analysis via Gemini ─────────────────────────
        _set_step(job, STEPS[2][0], STEPS[2][1])
        raw_clips = ask_gemini(
            api_key=api_key,
            transcript_text=transcript,
            n_clips=job.n_clips,
            max_dur=job.max_duration,
            custom_focus=job.custom_focus,
        )
        if not raw_clips:
            raise ValueError(
                'AI could not find any suitable clips. '
                'Check that GEMINI_API_KEY is set and the transcript has content.'
            )

        # ── Step 4 — save segments ──────────────────────────────────
        _set_step(job, STEPS[3][0], STEPS[3][1])
        segments = []
        for idx, clip_data in enumerate(raw_clips):
            seg = ClipSegment.objects.create(
                job=job,
                title=clip_data.get('title', f'Clip {idx + 1}') or f'Clip {idx + 1}',
                start_time=float(clip_data['start']),
                end_time=float(clip_data['end']),
                reason=clip_data.get('reason', ''),
                is_downloaded=False,
            )
            segments.append(seg)

        log.info('  → %d segments saved', len(segments))

        # ── Step 5 — download & cut each clip ──────────────────────
        total = len(segments)
        for i, seg in enumerate(segments):
            pct = STEPS[4][1] + int((i / total) * (STEPS[5][1] - STEPS[4][1]) / 2)
            _set_step(job, f'Downloading clip {i+1}/{total}...', pct)
            try:
                safe_title = re.sub(r'[^\w\s-]', '', seg.title).strip()[:30] or f'clip-{i+1}'
                suffix = f'{safe_title}_{seg.start_time:.0f}s'.replace(' ', '_')

                out_path = download_and_cut_direct(
                    url=job.youtube_url,
                    start=seg.start_time,
                    end=seg.end_time,
                    output_dir=f'media/clips/{job.id}',
                    cookies_path=cookies_path,
                    filename_suffix=suffix,
                )
                if out_path:
                    seg.video_file.name = f'clips/{job.id}/{out_path.name}'
                    seg.is_downloaded = True
                    seg.save(update_fields=['video_file', 'is_downloaded'])
            except Exception as e:
                log.error('  → Download failed for segment %d: %s', seg.id, e, exc_info=True)

        # ── Step 6 — fetch video title ─────────────────────────────
        _set_step(job, STEPS[5][0], STEPS[5][1])
        try:
            import yt_dlp
            with yt_dlp.YoutubeDL({'quiet': True, 'no_warnings': True}) as ydl:
                info = ydl.extract_info(
                    f'https://www.youtube.com/watch?v={video_id}',
                    download=False,
                )
                if info and info.get('title'):
                    job.video_title = info['title'][:512]
                    job.save(update_fields=['video_title'])
        except ImportError:
            log.warning('yt-dlp not installed — skipping title fetch')
        except Exception as e:
            log.warning('Title fetch failed (non-fatal): %s', e)

        # ── Done ──────────────────────────────────────────────────
        job.status = ClipJob.Status.DONE
        _set_step(job, 'Complete!', 100)
        job.save(update_fields=['status'])
        log.info('=== PIPELINE DONE job=%d ===', job.pk)

    except Exception as e:
        log.error('=== PIPELINE FAILED job=%d | %s ===', job.pk, e, exc_info=True)
        job.status = ClipJob.Status.ERROR
        job.error_message = str(e)[:2000]
        _set_step(job, f'Failed: {e!s}', -1)
        job.save(update_fields=['status', 'error_message'])


# ══════════════════════════════════════════════════════════════════════════
# VIEWS
# ══════════════════════════════════════════════════════════════════════════


class ClipGenerateView(LoginRequiredMixin, CreateView):
    """Form page to submit a new clip generation job."""

    model = ClipJob
    form_class = ClipGenerateForm
    template_name = 'yt_tools/generate.html'
    success_url = reverse_lazy('yt_tools:generate')

    def form_valid(self, form):
        form.instance.user = self.request.user
        response = super().form_valid(form)

        log.info('ClipGenerateView | new job pk=%d user=%s', self.object.pk, self.request.user)

        api_key = settings.GEMINI_API_KEY
        cookies_path = settings.YT_CLIPS_COOKIES_PATH

        log.info('ClipGenerateView | GEMINI_API_KEY configured=%s', bool(api_key))

        thread = threading.Thread(
            target=_process_job,
            args=(self.object, api_key, cookies_path),
            daemon=True,
        )
        thread.start()

        messages.success(self.request, 'Clip generation started!')
        return redirect('yt_tools:results', pk=self.object.pk)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['recent_jobs'] = ClipJob.objects.filter(user=self.request.user)[:10]
        return ctx


class ClipResultsView(LoginRequiredMixin, DetailView):
    """View results for a specific clip job."""

    model = ClipJob
    template_name = 'yt_tools/results.html'
    context_object_name = 'job'

    def get_queryset(self):
        return super().get_queryset().filter(user=self.request.user)


class ClipRegenerateView(LoginRequiredMixin, DetailView):
    """Re-run clip processing for an existing job."""

    model = ClipJob
    http_method_names = ['post']

    def get_queryset(self):
        return super().get_queryset().filter(user=self.request.user)

    def post(self, request, *args, **kwargs):
        job = self.get_object()
        log.info('ClipRegenerateView | regenerating job=%d', job.pk)

        job.clips.all().delete()
        job.status = ClipJob.Status.PENDING
        job.error_message = ''
        job.progress_step = ''
        job.save(update_fields=['status', 'error_message', 'progress_step'])

        api_key = settings.GEMINI_API_KEY
        cookies_path = settings.YT_CLIPS_COOKIES_PATH

        thread = threading.Thread(
            target=_process_job,
            args=(job, api_key, cookies_path),
            daemon=True,
        )
        thread.start()

        messages.success(request, 'Regenerating clips...')
        return redirect('yt_tools:results', pk=job.pk)
