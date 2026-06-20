import { Router, Response } from 'express';
import { prisma } from '../lib/prisma';
import { authenticate } from '../middleware/auth';
import { requirePaid } from '../middleware/paid';
import { AuthRequest } from '../types';
import { config } from '../config';

const router = Router();

// GET /api/trends — Fetch trending videos based on user interests
router.get('/', authenticate, requirePaid, async (req: AuthRequest, res: Response) => {
  try {
    const userId = req.user!.userId;

    // Get user's interests
    const interests = await prisma.interest.findMany({
      where: { userId },
      select: { keyword: true },
    });

    if (interests.length === 0) {
      res.json({
        trends: [],
        message: 'Add interests in Settings to see personalized trends.',
      });
      return;
    }

    // Fetch trending from YouTube API for each interest
    const trendResults = [];

    for (const interest of interests) {
      try {
        const url = `https://www.googleapis.com/youtube/v3/search?part=snippet&q=${encodeURIComponent(interest.keyword)}&order=date&type=video&maxResults=5&key=${config.youtubeApiKey}`;
        const response = await fetch(url);
        const data = await response.json();

        if (data.items) {
          for (const item of data.items) {
            trendResults.push({
              id: item.id.videoId,
              title: item.snippet.title,
              channelTitle: item.snippet.channelTitle,
              description: item.snippet.description,
              thumbnail: item.snippet.thumbnails?.high?.url || item.snippet.thumbnails?.default?.url,
              publishedAt: item.snippet.publishedAt,
              keyword: interest.keyword,
            });
          }
        }
      } catch {
        // Skip failed interest queries
        continue;
      }
    }

    // Sort by published date (most recent first)
    trendResults.sort((a, b) => new Date(b.publishedAt).getTime() - new Date(a.publishedAt).getTime());

    res.json({ trends: trendResults.slice(0, 30) });
  } catch (err) {
    console.error('Trends error:', err);
    res.status(500).json({ error: 'Failed to fetch trends' });
  }
});

// POST /api/trends/interests — Add an interest keyword
router.post('/interests', authenticate, async (req: AuthRequest, res: Response) => {
  try {
    const { keyword } = req.body;
    if (!keyword || typeof keyword !== 'string' || keyword.trim().length === 0) {
      res.status(400).json({ error: 'Keyword is required' });
      return;
    }

    const interest = await prisma.interest.create({
      data: { userId: req.user!.userId, keyword: keyword.trim().toLowerCase() },
    });

    res.status(201).json({ interest });
  } catch (err: any) {
    if (err?.code === 'P2002') {
      res.status(409).json({ error: 'Interest already exists' });
      return;
    }
    console.error('Add interest error:', err);
    res.status(500).json({ error: 'Failed to add interest' });
  }
});

// GET /api/trends/interests — List user's interests
router.get('/interests', authenticate, async (req: AuthRequest, res: Response) => {
  try {
    const interests = await prisma.interest.findMany({
      where: { userId: req.user!.userId },
      orderBy: { createdAt: 'desc' },
    });

    res.json({ interests });
  } catch (err) {
    console.error('List interests error:', err);
    res.status(500).json({ error: 'Failed to fetch interests' });
  }
});

// DELETE /api/trends/interests/:id — Remove an interest
router.delete('/interests/:id', authenticate, async (req: AuthRequest, res: Response) => {
  try {
    const interest = await prisma.interest.findFirst({
      where: { id: req.params.id, userId: req.user!.userId },
    });

    if (!interest) {
      res.status(404).json({ error: 'Interest not found' });
      return;
    }

    await prisma.interest.delete({ where: { id: interest.id } });
    res.json({ message: 'Interest removed' });
  } catch (err) {
    console.error('Delete interest error:', err);
    res.status(500).json({ error: 'Failed to remove interest' });
  }
});

export default router;
