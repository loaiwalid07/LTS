import { Router, Response } from 'express';
import crypto from 'crypto';
import { prisma } from '../lib/prisma';
import { authenticate } from '../middleware/auth';
import { AuthRequest } from '../types';
import { config } from '../config';

const router = Router();

// POST /api/billing/create-payment — Create Paymob payment intent
router.post('/create-payment', authenticate, async (req: AuthRequest, res: Response) => {
  try {
    const user = req.user!;

    // Check if user already paid
    const existingUser = await prisma.user.findUnique({
      where: { id: user.userId },
      select: { paid: true },
    });

    if (existingUser?.paid) {
      res.status(400).json({ error: 'You already have lifetime access' });
      return;
    }

    // Step 1: Get auth token from Paymob
    const authResponse = await fetch('https://accept.paymob.com/api/auth/tokens', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ api_key: config.paymobApiKey }),
    });

    const authData = await authResponse.json();
    if (!authData.token) {
      res.status(500).json({ error: 'Failed to initialize payment gateway' });
      return;
    }

    // Step 2: Create order
    const orderResponse = await fetch('https://accept.paymob.com/api/ecommerce/orders', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        auth_token: authData.token,
        delivery_needed: 'false',
        amount_cents: '29900', // 299 EGP (adjust as needed)
        currency: 'EGP',
        items: [],
      }),
    });

    const orderData = await orderResponse.json();
    if (!orderData.id) {
      res.status(500).json({ error: 'Failed to create order' });
      return;
    }

    // Step 3: Generate payment key
    const billingData = {
      street: 'N/A',
      building: 'N/A',
      floor: 'N/A',
      apartment: 'N/A',
    };

    const paymentKeyResponse = await fetch('https://accept.paymob.com/api/acceptance/payment_keys', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        auth_token: authData.token,
        amount_cents: '29900',
        expiration: 36000,
        order_id: orderData.id,
        billing_data: billingData,
        currency: 'EGP',
        integration_id: parseInt(config.paymobIntegrationId),
        lock_order_when_paid: 'true',
      }),
    });

    const paymentKeyData = await paymentKeyResponse.json();

    res.json({
      paymentKey: paymentKeyData.token,
      iframeId: config.paymobIframeId,
      orderId: orderData.id,
      amount: 29900,
      currency: 'EGP',
    });
  } catch (err) {
    console.error('Create payment error:', err);
    res.status(500).json({ error: 'Failed to create payment' });
  }
});

// POST /api/billing/webhook — Paymob transaction callback
router.post('/webhook', async (req, res: Response) => {
  try {
    const { obj } = req.body;

    if (!obj) {
      res.status(400).json({ error: 'Invalid payload' });
      return;
    }

    // Verify HMAC signature
    const hmac = req.query.hmac as string;
    if (hmac && config.paymobHmacSecret) {
      const calculatedHmac = crypto
        .createHmac('sha512', config.paymobHmacSecret)
        .update(JSON.stringify(req.body))
        .digest('hex');

      if (hmac !== calculatedHmac) {
        res.status(401).json({ error: 'Invalid signature' });
        return;
      }
    }

    const transactionId = String(obj.id);
    const orderId = String(obj.order.id);
    const amountCents = obj.amount_cents;
    const paymentMethod = obj.source_data?.type || 'unknown';
    const success = obj.success === true;

    // Find user by order metadata (we store order_info in a pending payment)
    // For simplicity, we'll create a payment record and look up the transaction
    // In production, store a mapping of order_id → user_id

    // Try to find existing payment record
    let payment = await prisma.payment.findUnique({
      where: { transactionId },
    });

    if (!payment) {
      // New webhook — try to match by order or create placeholder
      // For now, we log and return
      console.log('Webhook received for unknown transaction:', transactionId);
      res.json({ received: true });
      return;
    }

    if (success) {
      await prisma.payment.update({
        where: { id: payment.id },
        data: { status: 'completed' },
      });

      await prisma.user.update({
        where: { id: payment.userId },
        data: { paid: true },
      });
    } else {
      await prisma.payment.update({
        where: { id: payment.id },
        data: { status: 'failed' },
      });
    }

    res.json({ received: true });
  } catch (err) {
    console.error('Webhook error:', err);
    res.status(500).json({ error: 'Webhook processing failed' });
  }
});

// POST /api/billing/verify — Verify payment after redirect
router.post('/verify', authenticate, async (req: AuthRequest, res: Response) => {
  try {
    const { transactionId } = req.body;

    if (!transactionId) {
      res.status(400).json({ error: 'Transaction ID is required' });
      return;
    }

    // Check payment in our database
    const payment = await prisma.payment.findFirst({
      where: { transactionId, userId: req.user!.userId },
    });

    if (!payment) {
      // Check with Paymob API
      const authResponse = await fetch('https://accept.paymob.com/api/auth/tokens', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ api_key: config.paymobApiKey }),
      });

      const authData = await authResponse.json();
      if (authData.token) {
        const transactionResponse = await fetch(
          `https://accept.paymob.com/api/acceptance/transactions/${transactionId}`,
          {
            headers: { Authorization: `Bearer ${authData.token}` },
          }
        );

        const transactionData = await transactionResponse.json();

        if (transactionData.success) {
          // Create payment record and mark user as paid
          await prisma.payment.create({
            data: {
              userId: req.user!.userId,
              amount: transactionData.amount_cents,
              transactionId,
              method: transactionData.source_data?.type || 'unknown',
              status: 'completed',
            },
          });

          await prisma.user.update({
            where: { id: req.user!.userId },
            data: { paid: true },
          });

          res.json({ paid: true });
          return;
        }
      }

      res.json({ paid: false });
      return;
    }

    res.json({ paid: payment.status === 'completed' });
  } catch (err) {
    console.error('Verify payment error:', err);
    res.status(500).json({ error: 'Failed to verify payment' });
  }
});

// POST /api/billing/create-pending — Create pending payment record before redirect
router.post('/create-pending', authenticate, async (req: AuthRequest, res: Response) => {
  try {
    const { transactionId, method } = req.body;

    if (!transactionId) {
      res.status(400).json({ error: 'Transaction ID is required' });
      return;
    }

    const payment = await prisma.payment.create({
      data: {
        userId: req.user!.userId,
        amount: 29900,
        transactionId,
        method: method || 'unknown',
        status: 'pending',
      },
    });

    res.status(201).json({ payment });
  } catch (err) {
    console.error('Create pending payment error:', err);
    res.status(500).json({ error: 'Failed to record payment' });
  }
});

export default router;
