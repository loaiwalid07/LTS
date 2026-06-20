import { useEffect, useState } from 'react';
import { shortsApi } from '../services/api';
import { Images, Clock, Trash2, Download, ExternalLink, Youtube, Loader2 } from 'lucide-react';

interface Short {
  id: string;
  youtubeUrl: string;
  title: string;
  caption: string | null;
  duration: number;
  thumbnail: string | null;
  videoUrl: string | null;
  status: string;
  createdAt: string;
}

export default function Gallery() {
  const [shorts, setShorts] = useState<Short[]>([]);
  const [loading, setLoading] = useState(true);
  const [downloadingId, setDownloadingId] = useState<string | null>(null);

  const fetchShorts = () => {
    setLoading(true);
    shortsApi.list()
      .then((data) => setShorts(data.shorts || []))
      .catch(() => {})
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchShorts();
  }, []);

  const handleDownload = async (id: string) => {
    setDownloadingId(id);
    try {
      const result = await shortsApi.download(id);
      if (result.videoUrl) {
        window.open(result.videoUrl, '_blank');
      }
      fetchShorts();
    } catch (err) {
      console.error('Download failed:', err);
    } finally {
      setDownloadingId(null);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Delete this short?')) return;
    try {
      await shortsApi.delete(id);
      setShorts((prev) => prev.filter((s) => s.id !== id));
    } catch (err) {
      console.error('Delete failed:', err);
    }
  };

  const getYoutubeId = (url: string) => {
    const match = url.match(/(?:youtube\.com\/(?:watch\?v=|embed\/|shorts\/)|youtu\.be\/)([a-zA-Z0-9_-]{11})/);
    return match?.[1] || null;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <Loader2 className="h-8 w-8 animate-spin text-brand-400" />
      </div>
    );
  }

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-white">Gallery</h1>
        <p className="mt-1 text-gray-400">
          Your generated shorts — {shorts.length} total
        </p>
      </div>

      {shorts.length === 0 ? (
        <div className="card text-center py-16">
          <Images className="mx-auto h-12 w-12 text-gray-600 mb-4" />
          <h3 className="text-lg font-medium text-gray-300 mb-2">No shorts yet</h3>
          <p className="text-sm text-gray-500 mb-4">
            Start by creating your first short from a YouTube video.
          </p>
          <a href="/create" className="btn-primary inline-flex">
            Create Your First Short
          </a>
        </div>
      ) : (
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
          {shorts.map((short) => (
            <div key={short.id} className="card group relative overflow-hidden">
              {/* Thumbnail */}
              <div className="relative mb-3 aspect-video rounded-lg overflow-hidden bg-gray-800">
                {short.thumbnail ? (
                  <img
                    src={short.thumbnail}
                    alt={short.title}
                    className="w-full h-full object-cover"
                  />
                ) : (
                  <div className="flex items-center justify-center h-full">
                    <Youtube className="h-8 w-8 text-gray-600" />
                  </div>
                )}
                <div className="absolute top-2 right-2">
                  <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${
                    short.status === 'ready' ? 'bg-emerald-500/20 text-emerald-400' :
                    short.status === 'downloading' ? 'bg-amber-500/20 text-amber-400' :
                    'bg-gray-500/20 text-gray-400'
                  }`}>
                    {short.status}
                  </span>
                </div>
              </div>

              {/* Info */}
              <h3 className="font-medium text-white truncate">{short.title}</h3>
              {short.caption && (
                <p className="text-sm text-gray-400 mt-1 line-clamp-2">{short.caption}</p>
              )}

              <div className="flex items-center gap-3 mt-3 text-xs text-gray-500">
                <span className="flex items-center gap-1">
                  <Clock className="h-3 w-3" />
                  {short.duration}s
                </span>
                <span>{new Date(short.createdAt).toLocaleDateString()}</span>
              </div>

              {/* Actions */}
              <div className="flex gap-2 mt-4 pt-3 border-t border-gray-800">
                <button
                  onClick={() => handleDownload(short.id)}
                  className="btn flex-1 text-xs"
                  disabled={downloadingId === short.id}
                >
                  {downloadingId === short.id ? (
                    <Loader2 className="h-3 w-3 animate-spin" />
                  ) : (
                    <Download className="h-3 w-3" />
                  )}
                  {short.videoUrl ? 'Download' : 'Prepare'}
                </button>

                <a
                  href={short.youtubeUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="btn text-xs"
                  title="Open original video"
                >
                  <ExternalLink className="h-3 w-3" />
                </a>

                <button
                  onClick={() => handleDelete(short.id)}
                  className="btn text-xs text-red-400 hover:text-red-300 hover:bg-red-500/10"
                  title="Delete"
                >
                  <Trash2 className="h-3 w-3" />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
