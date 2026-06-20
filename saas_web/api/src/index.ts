import express from 'express';
import cors from 'cors';
import { config } from './config';
import authRoutes from './routes/auth';
import shortsRoutes from './routes/shorts';
import trendsRoutes from './routes/trends';
import billingRoutes from './routes/billing';
import uploadRoutes from './routes/upload';
import settingsRoutes from './routes/settings';

const app = express();

// Trust Vercel proxy
app.set('trust proxy', 1);

// CORS
app.use(cors({
  origin: config.clientUrl,
  credentials: true,
  methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
  allowedHeaders: ['Content-Type', 'Authorization'],
}));

// Body parsing — raw for webhooks, json for everything else
app.use('/api/billing/webhook', express.raw({ type: 'application/json' }));
app.use(express.json());

// Health check
app.get('/api/health', (_req, res) => {
  res.json({ status: 'ok', timestamp: new Date().toISOString() });
});

// Routes
app.use('/api/auth', authRoutes);
app.use('/api/shorts', shortsRoutes);
app.use('/api/trends', trendsRoutes);
app.use('/api/billing', billingRoutes);
app.use('/api/upload', uploadRoutes);
app.use('/api/settings', settingsRoutes);

// 404 handler
app.use((_req, res) => {
  res.status(404).json({ error: 'Route not found' });
});

// Error handler
app.use((err: Error, _req: express.Request, res: express.Response, _next: express.NextFunction) => {
  console.error('Unhandled error:', err);
  res.status(500).json({ error: 'Internal server error' });
});

// Start server (local dev)
if (process.env.NODE_ENV !== 'production' && !process.env.VERCEL) {
  app.listen(config.port, () => {
    console.log(`🚀 API running on http://localhost:${config.port}`);
  });
}

export default app;
