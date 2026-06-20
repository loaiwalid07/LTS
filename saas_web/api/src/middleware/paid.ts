import { Response, NextFunction } from 'express';
import { prisma } from '../lib/prisma';
import { AuthRequest } from '../types';

export async function requirePaid(req: AuthRequest, res: Response, next: NextFunction): Promise<void> {
  if (!req.user) {
    res.status(401).json({ error: 'Not authenticated' });
    return;
  }

  const user = await prisma.user.findUnique({
    where: { id: req.user.userId },
    select: { paid: true },
  });

  if (!user?.paid) {
    res.status(403).json({ error: 'Payment required. Please purchase lifetime access.', code: 'PAYMENT_REQUIRED' });
    return;
  }

  next();
}
