import { Router, Response } from 'express';
import { z } from 'zod';
import { prisma } from '../lib/prisma';
import { authenticate } from '../middleware/auth';
import { requirePaid } from '../middleware/paid';
import { AuthRequest } from '../types';
import { config } from '../config';

const router = Router();

const createSchema = z.object({
  youtubeUrl: z.string().url('Invalid YouTube URL'),
});

// POST /api/shorts/create — Submit YouTube URL to worker
router.post('/create', authenticate, requirePaid, async (req: AuthRequest, res: Response) => {
  try {
    const { youtubeUrl } = createSchema.parse(req.body);
    const userId = req.user!.userId;

    // Call the Python worker API
    let workerResult;
    try {
      const workerResponse = await fetch(`${config.workerApiUrl}/process`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ youtubeUrl, userId }),
      });

      if (!workerResponse.ok) {
        throw new Error(`Worker responded with ${workerResponse.status}`);
      }

      workerResult = await workerResponse.json();
    } catch (workerErr) {
      // If worker is unavailable, create a pending short record
      const short = await prisma.short.create({
        data: {
          userId,
          youtubeUrl,
          title: 'Processing...',
          duration: 0,
          status: 'pending',
        },
      });

      res.status(202).json({
        short,
        message: 'Your video is being processed. Check back shortly.',
      });
      return;
    }

    // Worker returned successfully
    const short = await prisma.short.create({
      data: {
        userId,
        youtubeUrl,
        title: workerResult.title || 'Untitled Short',
        caption: workerResult.caption || '',
        duration: workerResult.duration || 0,
        thumbnail: workerResult.thumbnail || null,
        videoUrl: workerResult.videoUrl || null,
        status: workerResult.videoUrl ? 'ready' : 'pending',
      },
    });

    res.status(201).json({ short });
  } catch (err) {
    if (err instanceof z.ZodError) {
      res.status(400).json({ error: err.errors[0].message });
      return;
    }
    console.error('Create short error:', err);
    res.status(500).json({ error: 'Failed to create short' });
  }
});

// GET /api/shorts — List user's shorts
router.get('/', authenticate, requirePaid, async (req: AuthRequest, res: Response) => {
  try {
    const userId = req.user!.userId;
    const shorts = await prisma.short.findMany({
      where: { userId },
      orderBy: { createdAt: 'desc' },
    });

    res.json({ shorts });
  } catch (err) {
    console.error('List shorts error:', err);
    res.status(500).json({ error: 'Failed to fetch shorts' });
  }
});

// GET /api/shorts/:id — Get single short
router.get('/:id', authenticate, requirePaid, async (req: AuthRequest, res: Response) => {
  try {
    const short = await prisma.short.findFirst({
      where: { id: req.params.id, userId: req.user!.userId },
    });

    if (!short) {
      res.status(404).json({ error: 'Short not found' });
      return;
    }

    res.json({ short });
  } catch (err) {
    console.error('Get short error:', err);
    res.status(500).json({ error: 'Failed to fetch short' });
  }
});

// POST /api/shorts/:id/download — Trigger download (on-demand cutting)
router.post('/:id/download', authenticate, requirePaid, async (req: AuthRequest, res: Response) => {
  try {
    const short = await prisma.short.findFirst({
      where: { id: req.params.id, userId: req.user!.userId },
    });

    if (!short) {
      res.status(404).json({ error: 'Short not found' });
      return;
    }

    // Update status to downloading
    await prisma.short.update({
      where: { id: short.id },
      data: { status: 'downloading' },
    });

    // Call worker to generate downloadable video
    try {
      const workerResponse = await fetch(`${config.workerApiUrl}/download`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ shortId: short.id, youtubeUrl: short.youtubeUrl }),
      });

      if (workerResponse.ok) {
        const result = await workerResponse.json();

        await prisma.short.update({
          where: { id: short.id },
          data: {
            videoUrl: result.videoUrl || short.videoUrl,
            status: result.videoUrl ? 'ready' : 'downloading',
          },
        });

        res.json({ videoUrl: result.videoUrl, status: 'ready' });
        return;
      }
    } catch {
      // Worker unavailable — return current status
    }

    res.json({
      message: 'Download queued. Check back shortly.',
      status: 'downloading',
    });
  } catch (err) {
    console.error('Download short error:', err);
    res.status(500).json({ error: 'Failed to process download' });
  }
});

// DELETE /api/shorts/:id — Delete a short
router.delete('/:id', authenticate, requirePaid, async (req: AuthRequest, res: Response) => {
  try {
    const short = await prisma.short.findFirst({
      where: { id: req.params.id, userId: req.user!.userId },
    });

    if (!short) {
      res.status(404).json({ error: 'Short not found' });
      return;
    }

    await prisma.short.delete({ where: { id: short.id } });
    res.json({ message: 'Short deleted' });
  } catch (err) {
    console.error('Delete short error:', err);
    res.status(500).json({ error: 'Failed to delete short' });
  }
});

export default router;
