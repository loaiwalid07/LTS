import { useEffect, useState } from 'react';
import { trendsApi } from '../services/api';
import { TrendingUp, ExternalLink, Hash, X, Plus, Loader2, Youtube } from 'lucide-react';

interface TrendVideo {
  id: string;
  title: string;
  channelTitle: string;
  description: string;
  thumbnail: string;
  publishedAt: string;
  keyword: string;
}

interface Interest {
  id: string;
  keyword: string;
}

export default function Trends() {
  const [trends, setTrends] = useState<TrendVideo[]>([]);
  const [interests, setInterests] = useState<Interest[]>([]);
  const [newKeyword, setNewKeyword] = useState('');
  const [loading, setLoading] = useState(true);
  const [addingKeyword, setAddingKeyword] = useState(false);
  const [error, setError] = useState('');

  const fetchData = async () => {
    setLoading(true);
    try {
      const [trendsData, interestsData] = await Promise.all([
        trendsApi.list(),
        trendsApi.getInterests(),
      ]);
      setTrends(trendsData.trends || []);
      setInterests(interestsData.interests || []);
    } catch (err) {
      console.error('Failed to fetch trends:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const addInterest = async () => {
    if (!newKeyword.trim()) return;
    setAddingKeyword(true);
    try {
      const data = await trendsApi.addInterest(newKeyword);
      setInterests((prev) => [data.interest, ...prev]);
      setNewKeyword('');
      // Refresh trends with new interest
      const trendsData = await trendsApi.list();
      setTrends(trendsData.trends || []);
    } catch (err: any) {
      setError(err.response?.data?.error || 'Failed to add interest');
    } finally {
      setAddingKeyword(false);
    }
  };

  const removeInterest = async (id: string) => {
    try {
      await trendsApi.removeInterest(id);
      setInterests((prev) => prev.filter((i) => i.id !== id));
      // Refresh trends
      const trendsData = await trendsApi.list();
      setTrends(trendsData.trends || []);
    } catch (err) {
      console.error('Failed to remove interest:', err);
    }
  };

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-white">YouTube Trends</h1>
        <p className="mt-1 text-gray-400">
          Trending videos based on your interests
        </p>
      </div>

      {/* Interests */}
      <div className="card mb-8">
        <h3 className="font-semibold text-white mb-3 flex items-center gap-2">
          <Hash className="h-4 w-4 text-brand-400" />
          Your Interests
        </h3>

        <div className="flex gap-2 mb-3">
          <input
            type="text"
            className="input flex-1"
            placeholder="e.g., AI, basketball, cooking..."
            value={newKeyword}
            onChange={(e) => setNewKeyword(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && addInterest()}
          />
          <button
            onClick={addInterest}
            className="btn-primary"
            disabled={addingKeyword || !newKeyword.trim()}
          >
            {addingKeyword ? <Loader2 className="h-4 w-4 animate-spin" /> : <Plus className="h-4 w-4" />}
            Add
          </button>
        </div>

        {error && (
          <p className="text-sm text-red-400 mb-2">{error}</p>
        )}

        <div className="flex flex-wrap gap-2">
          {interests.length === 0 && (
            <p className="text-sm text-gray-500">Add interests to see personalized trends.</p>
          )}
          {interests.map((interest) => (
            <span
              key={interest.id}
              className="inline-flex items-center gap-1.5 rounded-full bg-gray-800 px-3 py-1 text-sm text-gray-300"
            >
              {interest.keyword}
              <button
                onClick={() => removeInterest(interest.id)}
                className="text-gray-500 hover:text-gray-300 transition-colors"
              >
                <X className="h-3 w-3" />
              </button>
            </span>
          ))}
        </div>
      </div>

      {/* Trends Grid */}
      {loading ? (
        <div className="flex items-center justify-center py-20">
          <Loader2 className="h-8 w-8 animate-spin text-brand-400" />
        </div>
      ) : trends.length === 0 ? (
        <div className="card text-center py-16">
          <TrendingUp className="mx-auto h-12 w-12 text-gray-600 mb-4" />
          <h3 className="text-lg font-medium text-gray-300 mb-2">No trends found</h3>
          <p className="text-sm text-gray-500">
            {interests.length === 0
              ? 'Add interests above to get started.'
              : 'Could not fetch trends. Check your YouTube API key.'}
          </p>
        </div>
      ) : (
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
          {trends.map((video) => (
            <a
              key={video.id}
              href={`https://youtube.com/watch?v=${video.id}`}
              target="_blank"
              rel="noopener noreferrer"
              className="card group hover:border-brand-500/50 transition-all"
            >
              <div className="relative mb-3 aspect-video rounded-lg overflow-hidden bg-gray-800">
                {video.thumbnail ? (
                  <img
                    src={video.thumbnail}
                    alt={video.title}
                    className="w-full h-full object-cover"
                  />
                ) : (
                  <div className="flex items-center justify-center h-full">
                    <Youtube className="h-8 w-8 text-gray-600" />
                  </div>
                )}
                <div className="absolute inset-0 bg-black/0 group-hover:bg-black/30 transition-colors flex items-center justify-center">
                  <ExternalLink className="h-6 w-6 text-white opacity-0 group-hover:opacity-100 transition-opacity" />
                </div>
              </div>

              <h3 className="font-medium text-white line-clamp-2 group-hover:text-brand-400 transition-colors">
                {video.title}
              </h3>
              <p className="text-sm text-gray-400 mt-1">{video.channelTitle}</p>
              <div className="flex items-center gap-2 mt-2 text-xs text-gray-500">
                <Hash className="h-3 w-3" />
                <span>{video.keyword}</span>
                <span className="ml-auto">
                  {new Date(video.publishedAt).toLocaleDateString()}
                </span>
              </div>
            </a>
          ))}
        </div>
      )}
    </div>
  );
}
