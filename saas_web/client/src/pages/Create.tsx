import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { shortsApi } from '../services/api';
import { Video, ArrowRight, Loader2, CheckCircle, Youtube } from 'lucide-react';

export default function Create() {
  const navigate = useNavigate();
  const [youtubeUrl, setYoutubeUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [result, setResult] = useState<any>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    setResult(null);

    try {
      const data = await shortsApi.create(youtubeUrl);
      setResult(data.short || data);
    } catch (err: any) {
      if (err.response?.status === 403) {
        navigate('/pricing');
        return;
      }
      setError(err.response?.data?.error || 'Failed to create short');
    } finally {
      setLoading(false);
    }
  };

  const extractVideoId = (url: string) => {
    const match = url.match(/(?:youtube\.com\/(?:watch\?v=|embed\/|shorts\/)|youtu\.be\/)([a-zA-Z0-9_-]{11})/);
    return match?.[1] || null;
  };

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-white">Create Short</h1>
        <p className="mt-1 text-gray-400">
          Paste a YouTube video URL to generate a short with captions.
        </p>
      </div>

      {/* Input Form */}
      <div className="card mb-8">
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label htmlFor="youtubeUrl" className="block text-sm font-medium text-gray-300 mb-2">
              YouTube Video URL
            </label>
            <div className="flex gap-3">
              <div className="relative flex-1">
                <Youtube className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-500" />
                <input
                  id="youtubeUrl"
                  type="url"
                  className="input pl-10"
                  placeholder="https://youtube.com/watch?v=..."
                  value={youtubeUrl}
                  onChange={(e) => setYoutubeUrl(e.target.value)}
                  required
                />
              </div>
              <button
                type="submit"
                className="btn-primary"
                disabled={loading || !youtubeUrl}
              >
                {loading ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <ArrowRight className="h-4 w-4" />
                )}
                {loading ? 'Processing...' : 'Generate'}
              </button>
            </div>
          </div>

          {youtubeUrl && extractVideoId(youtubeUrl) && (
            <div className="flex items-center gap-2 text-sm text-gray-500">
              <CheckCircle className="h-3.5 w-3.5 text-emerald-400" />
              YouTube video detected
            </div>
          )}
        </form>

        {error && (
          <div className="mt-4 rounded-lg bg-red-900/50 border border-red-800 px-4 py-2 text-sm text-red-400">
            {error}
          </div>
        )}
      </div>

      {/* Result */}
      {loading && (
        <div className="card text-center py-12">
          <Loader2 className="mx-auto h-8 w-8 animate-spin text-brand-400 mb-4" />
          <p className="text-gray-400">
            Processing your video...<br />
            <span className="text-sm text-gray-500">Downloading and generating captions</span>
          </p>
        </div>
      )}

      {result && (
        <div className="card">
          <div className="flex items-center gap-3 mb-4">
            <CheckCircle className="h-6 w-6 text-emerald-400" />
            <h2 className="text-lg font-semibold text-white">Short Created!</h2>
          </div>

          {result.thumbnail && (
            <img
              src={result.thumbnail}
              alt={result.title}
              className="w-full aspect-video rounded-lg object-cover mb-4"
            />
          )}

          <div className="space-y-3">
            <div>
              <label className="block text-xs font-medium text-gray-500 uppercase tracking-wider">
                Title
              </label>
              <p className="text-white font-medium">{result.title || 'Untitled'}</p>
            </div>

            {result.caption && (
              <div>
                <label className="block text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Caption
                </label>
                <p className="text-sm text-gray-300">{result.caption}</p>
              </div>
            )}

            <div className="flex gap-4 text-sm">
              <span className="text-gray-400">Duration: <strong className="text-white">{result.duration || 0}s</strong></span>
              <span className="text-gray-400">Status: <strong className={`${result.status === 'ready' ? 'text-emerald-400' : 'text-amber-400'}`}>{result.status}</strong></span>
            </div>

            <div className="flex gap-3 pt-2">
              <button
                onClick={() => navigate('/gallery')}
                className="btn-primary"
              >
                View in Gallery
              </button>
              <button
                onClick={() => {
                  setYoutubeUrl('');
                  setResult(null);
                }}
                className="btn-secondary"
              >
                Create Another
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Tips */}
      {!result && !loading && (
        <div className="card mt-6">
          <h3 className="font-semibold text-white mb-2">Tips</h3>
          <ul className="space-y-2 text-sm text-gray-400">
            <li>• Use long videos (10+ minutes) for best short extraction</li>
            <li>• Videos with clear speech generate better captions</li>
            <li>• Processing time depends on video length</li>
          </ul>
        </div>
      )}
    </div>
  );
}
