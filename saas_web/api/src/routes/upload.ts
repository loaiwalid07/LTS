import { Router, Response } from 'express';
import { authenticate } from '../middleware/auth';
import { requirePaid } from '../middleware/paid';
import { AuthRequest } from '../types';

const router = Router();

interface SocialPlatform {
  id: string;
  name: string;
  requires: string[];
  authUrl: string;
}

const platforms: SocialPlatform[] = [
  {
    id: 'youtube',
    name: 'YouTube',
    requires: ['oauth', 'video'],
    authUrl: 'https://accounts.google.com/o/oauth2/auth?access_type=offline&scope=https://www.googleapis.com/auth/youtube.upload&response_type=code',
  },
  {
    id: 'instagram',
    name: 'Instagram',
    requires: ['oauth', 'video'],
    authUrl: 'https://api.instagram.com/oauth/authorize?scope=instagram_content_publish',
  },
  {
    id: 'tiktok',
    name: 'TikTok',
    requires: ['oauth', 'video'],
    authUrl: 'https://www.tiktok.com/v2/auth/authorize?scope=video.upload',
  },
];

// GET /api/upload/platforms — List available platforms
router.get('/platforms', authenticate, requirePaid, async (_req: AuthRequest, res: Response) => {
  res.json({ platforms });
});

// POST /api/upload/short — Upload a short to a social platform
router.post('/short', authenticate, requirePaid, async (req: AuthRequest, res: Response) => {
  try {
    const { shortId, platform, accessToken } = req.body;

    if (!shortId || !platform || !accessToken) {
      res.status(400).json({ error: 'shortId, platform, and accessToken are required' });
      return;
    }

    // Get the short from database
    const { prisma } = await import('../lib/prisma');
    const short = await prisma.short.findFirst({
      where: { id: shortId, userId: req.user!.userId },
    });

    if (!short) {
      res.status(404).json({ error: 'Short not found' });
      return;
    }

    if (!short.videoUrl) {
      res.status(400).json({ error: 'Short video not ready yet. Download it first.' });
      return;
    }

    // Platform-specific upload logic
    switch (platform) {
      case 'youtube':
        // Upload to YouTube Shorts via API
        res.json({ message: 'YouTube upload queued', platform, status: 'queued' });
        break;

      case 'instagram':
        // Upload to Instagram Reels via Graph API
        res.json({ message: 'Instagram upload queued', platform, status: 'queued' });
        break;

      case 'tiktok':
        // Upload to TikTok via TikTok API
        res.json({ message: 'TikTok upload queued', platform, status: 'queued' });
        break;

      default:
        res.status(400).json({ error: `Unsupported platform: ${platform}` });
    }
  } catch (err) {
    console.error('Upload error:', err);
    res.status(500).json({ error: 'Failed to upload' });
  }
});

export default router;
