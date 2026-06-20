import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { shortsApi } from '../services/api';
import { Video, TrendingUp, Images, CreditCard, ArrowRight } from 'lucide-react';

export default function Dashboard() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [shortCount, setShortCount] = useState(0);
  const [recentShorts, setRecentShorts] = useState<any[]>([]);

  useEffect(() => {
    if (user?.paid) {
      shortsApi.list().then((data) => {
        setShortCount(data.shorts?.length || 0);
        setRecentShorts(data.shorts?.slice(0, 3) || []);
      }).catch(() => {});
    }
  }, [user?.paid]);

  const stats = [
    { label: 'Total Shorts', value: shortCount, icon: Video, color: 'text-brand-400', bg: 'bg-brand-500/10' },
    { label: 'Trends Tracked', value: user?.paid ? 'Active' : '—', icon: TrendingUp, color: 'text-emerald-400', bg: 'bg-emerald-500/10' },
    { label: 'Platforms', value: '3', icon: Images, color: 'text-purple-400', bg: 'bg-purple-500/10' },
    { label: 'Account', value: user?.paid ? 'Lifetime' : 'Free', icon: CreditCard, color: 'text-amber-400', bg: 'bg-amber-500/10' },
  ];

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-white">
          Welcome back, {user?.name || user?.email}
        </h1>
        <p className="mt-1 text-gray-400">
          {user?.paid
            ? 'You have lifetime access. Create shorts from YouTube videos.'
            : 'Purchase lifetime access to unlock all features.'}
        </p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        {stats.map(({ label, value, icon: Icon, color, bg }) => (
          <div key={label} className="card">
            <div className={`mb-3 inline-flex rounded-lg p-2.5 ${bg}`}>
              <Icon className={`h-5 w-5 ${color}`} />
            </div>
            <p className="text-2xl font-bold text-white">{value}</p>
            <p className="text-sm text-gray-400">{label}</p>
          </div>
        ))}
      </div>

      {/* Quick Actions */}
      <div className="grid md:grid-cols-2 gap-6 mb-8">
        <button
          onClick={() => navigate(user?.paid ? '/create' : '/pricing')}
          className="card text-left group hover:border-brand-500/50 transition-colors"
        >
          <h3 className="font-semibold text-white flex items-center gap-2">
            <Video className="h-4 w-4 text-brand-400" />
            Create New Short
            <ArrowRight className="h-4 w-4 ml-auto text-brand-400 opacity-0 group-hover:opacity-100 transition-opacity" />
          </h3>
          <p className="mt-2 text-sm text-gray-400">
            Paste a YouTube URL and generate a short with AI-powered captions.
          </p>
        </button>

        <button
          onClick={() => navigate(user?.paid ? '/trends' : '/pricing')}
          className="card text-left group hover:border-brand-500/50 transition-colors"
        >
          <h3 className="font-semibold text-white flex items-center gap-2">
            <TrendingUp className="h-4 w-4 text-emerald-400" />
            Browse Trends
            <ArrowRight className="h-4 w-4 ml-auto text-emerald-400 opacity-0 group-hover:opacity-100 transition-opacity" />
          </h3>
          <p className="mt-2 text-sm text-gray-400">
            See what's trending on YouTube based on your interests.
          </p>
        </button>
      </div>

      {/* Recent Shorts */}
      {user?.paid && recentShorts.length > 0 && (
        <div>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-white">Recent Shorts</h2>
            <button
              onClick={() => navigate('/gallery')}
              className="text-sm text-brand-400 hover:text-brand-300"
            >
              View all
            </button>
          </div>
          <div className="grid md:grid-cols-3 gap-4">
            {recentShorts.map((short: any) => (
              <div key={short.id} className="card">
                {short.thumbnail && (
                  <img
                    src={short.thumbnail}
                    alt={short.title}
                    className="mb-3 w-full aspect-video rounded-lg object-cover"
                  />
                )}
                <h4 className="font-medium text-white truncate">{short.title}</h4>
                <p className="text-sm text-gray-400 mt-1">
                  {short.duration}s · {short.status}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* CTA for free users */}
      {!user?.paid && (
        <div className="card border-brand-800 bg-brand-950/30">
          <h3 className="text-lg font-semibold text-white">Unlock Full Access</h3>
          <p className="mt-2 text-sm text-gray-400">
            Get lifetime access to create unlimited shorts, browse YouTube trends, and upload to social media.
          </p>
          <button
            onClick={() => navigate('/pricing')}
            className="btn-primary mt-4"
          >
            View Pricing
          </button>
        </div>
      )}
    </div>
  );
}
