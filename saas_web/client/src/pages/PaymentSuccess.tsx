import { useEffect, useState } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { billingApi } from '../services/api';
import { useAuth } from '../contexts/AuthContext';
import { CheckCircle, XCircle, Loader2 } from 'lucide-react';

export default function PaymentSuccess() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { refreshUser } = useAuth();
  const [status, setStatus] = useState<'verifying' | 'success' | 'failed'>('verifying');
  const [message, setMessage] = useState('');

  useEffect(() => {
    const verifyPayment = async () => {
      const transactionId = searchParams.get('transaction_id') || searchParams.get('id');
      const success = searchParams.get('success');

      if (success === 'false') {
        setStatus('failed');
        setMessage('Payment was cancelled or failed.');
        return;
      }

      if (!transactionId) {
        setStatus('failed');
        setMessage('No transaction information received.');
        return;
      }

      try {
        await billingApi.createPending(transactionId);
        const result = await billingApi.verify(transactionId);

        if (result.paid) {
          await refreshUser();
          setStatus('success');
          setMessage('Your lifetime access has been activated!');
        } else {
          setStatus('failed');
          setMessage('Payment could not be verified. Please contact support.');
        }
      } catch {
        setStatus('failed');
        setMessage('Failed to verify payment. Please contact support.');
      }
    };

    verifyPayment();
  }, []);

  return (
    <div className="flex min-h-screen items-center justify-center px-4">
      <div className="w-full max-w-md text-center">
        {status === 'verifying' && (
          <div>
            <Loader2 className="mx-auto h-12 w-12 animate-spin text-brand-400 mb-4" />
            <h1 className="text-2xl font-bold text-white mb-2">Verifying Payment</h1>
            <p className="text-gray-400">Please wait while we confirm your payment...</p>
          </div>
        )}

        {status === 'success' && (
          <div>
            <CheckCircle className="mx-auto h-16 w-16 text-emerald-400 mb-4" />
            <h1 className="text-2xl font-bold text-white mb-2">Payment Successful!</h1>
            <p className="text-gray-400 mb-8">{message}</p>
            <button
              onClick={() => navigate('/dashboard')}
              className="btn-primary text-base px-8 py-3"
            >
              Go to Dashboard
            </button>
          </div>
        )}

        {status === 'failed' && (
          <div>
            <XCircle className="mx-auto h-16 w-16 text-red-400 mb-4" />
            <h1 className="text-2xl font-bold text-white mb-2">Payment Issue</h1>
            <p className="text-gray-400 mb-8">{message}</p>
            <div className="flex gap-3 justify-center">
              <button
                onClick={() => navigate('/pricing')}
                className="btn-primary"
              >
                Try Again
              </button>
              <button
                onClick={() => navigate('/dashboard')}
                className="btn-secondary"
              >
                Go to Dashboard
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
