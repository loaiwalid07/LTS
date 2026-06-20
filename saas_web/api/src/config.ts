import dotenv from 'dotenv';
dotenv.config({ path: '../.env' });

export const config = {
  jwtSecret: process.env.JWT_SECRET || 'dev-secret-change-in-prod',
  port: parseInt(process.env.PORT || '3001'),
  workerApiUrl: process.env.WORKER_API_URL || '',
  paymobApiKey: process.env.PAYMOB_API_KEY || '',
  paymobHmacSecret: process.env.PAYMOB_HMAC_SECRET || '',
  paymobIntegrationId: process.env.PAYMOB_INTEGRATION_ID || '',
  paymobIframeId: process.env.PAYMOB_IFRAME_ID || '',
  cloudinary: {
    cloudName: process.env.CLOUDINARY_CLOUD_NAME || '',
    apiKey: process.env.CLOUDINARY_API_KEY || '',
    apiSecret: process.env.CLOUDINARY_API_SECRET || '',
  },
  youtubeApiKey: process.env.YOUTUBE_API_KEY || '',
  clientUrl: process.env.CLIENT_URL || 'http://localhost:5173',
};
