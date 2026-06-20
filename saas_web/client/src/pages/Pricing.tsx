import { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { billingApi } from '../services/api';
import { Check, Loader2, CreditCard, Smartphone, Landmark } from 'lucide-react';

const features = [
  'Create unlimited shorts from YouTube videos',
  'AI-generated titles and captions',
  'Browse personalized YouTube trends',
  'Upload to Instagram, YouTube & TikTok',
  'Download shorts on demand',
  'No recurring fees — pay once',
];

export default function Pricing() {
  const { user, refreshUser } = useAuth();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handlePurchase = async () => {
    setLoading(true);
    setError('');

    try {
      const data = await billingApi.createPayment();

      // Build Paymob iframe URL
      const iframeUrl = `https://accept.paymob.com/api/acceptance/iframes/${data.iframeId}?payment_token=${data.paymentKey}`;

      // Open Paymob checkout in same window
      window.location.href = iframeUrl;
    } catch (err: any) {
      if (err.response?.status === 400 && err.response?.data?.error?.includes('already')) {
        await refreshUser();
        setError('You already have lifetime access!');
        return;
      }
      setError(err.response?.data?.error || 'Failed to initiate payment');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center px-4 py-12">
      <div className="w-full max-w-lg">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-white">Lifetime Access</h1>
          <p className="mt-2 text-gray-400">
            Pay once, use forever. No subscriptions, no hidden fees.
          </p>
        </div>

        {/* Pricing Card */}
        <div className="card border-brand-800 relative overflow-hidden">
          {/* Popular badge */}
          <div className="absolute top-0 right-0">
            <div className="bg-brand-600 text-white text-xs font-medium px-4 py-1 rounded-bl-lg">
              Best Value
            </div>
          </div>

          {/* Price */}
          <div className="text-center mb-6 pt-2">
            <div className="flex items-baseline justify-center gap-1">
              <span className="text-5xl font-bold text-white">299</span>
              <span className="text-xl text-gray-400">EGP</span>
            </div>
            <p className="text-sm text-gray-500 mt-1">One-time payment</p>
          </div>

          {/* Features */}
          <ul className="space-y-3 mb-8">
            {features.map((feature) => (
              <li key={feature} className="flex items-start gap-3 text-sm text-gray-300">
                <Check className="h-5 w-5 text-emerald-400 shrink-0 mt-0.5" />
                {feature}
              </li>
            ))}
          </ul>

          {/* Payment methods */}
          <div className="mb-6 p-3 rounded-lg bg-gray-800/50">
            <p className="text-xs text-gray-500 mb-2">Accepted payment methods:</p>
            <div className="flex items-center gap-4">
              <span className="flex items-center gap-1.5 text-sm text-gray-400">
                <CreditCard className="h-4 w-4" /> Card
              </span>
              <span className="flex items-center gap-1.5 text-sm text-gray-400">
                <Smartphone className="h-4 w-4" /> Vodafone Cash
              </span>
              <span className="flex items-center gap-1.5 text-sm text-gray-400">
                <Landmark className="h-4 w-4" /> InstaPay
              </span>
            </div>
          </div>

          {error && (
            <div className="mb-4 rounded-lg bg-red-900/50 border border-red-800 px-4 py-2 text-sm text-red-400">
              {error}
            </div>
          )}

          <button
            onClick={handlePurchase}
            className="btn-primary w-full py-3 text-base"
            disabled={loading || user?.paid}
          >
            {loading ? (
              <Loader2 className="h-5 w-5 animate-spin" />
            ) : user?.paid ? (
              'Already Purchased ✓'
            ) : (
              'Buy Lifetime Access'
            )}
          </button>

          {!loading && !user?.paid && (
            <p className="text-xs text-gray-500 text-center mt-3">
              Secure checkout powered by Paymob
            </p>
          )}
        </div>

        {/* Money-back guarantee */}
        <p className="text-center text-sm text-gray-600 mt-6">
          Questions? Contact support
        </p>
      </div>
    </div>
  );
}
