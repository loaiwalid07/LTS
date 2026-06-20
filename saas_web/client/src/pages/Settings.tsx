import { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { settingsApi, trendsApi } from '../services/api';
import { User, Key, Hash, X, Plus, Loader2, Save, CheckCircle, CreditCard } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

interface Interest {
  id: string;
  keyword: string;
}

export default function Settings() {
  const { user, refreshUser } = useAuth();
  const navigate = useNavigate();
  const [name, setName] = useState(user?.name || '');
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  // Password
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [passwordSaving, setPasswordSaving] = useState(false);
  const [passwordError, setPasswordError] = useState('');
  const [passwordSuccess, setPasswordSuccess] = useState('');

  // Interests
  const [interests, setInterests] = useState<Interest[]>([]);
  const [newKeyword, setNewKeyword] = useState('');

  useEffect(() => {
    trendsApi.getInterests().then((data) => {
      setInterests(data.interests || []);
    }).catch(() => {});
  }, []);

  const handleSaveProfile = async () => {
    setSaving(true);
    try {
      await settingsApi.updateProfile({ name });
      await refreshUser();
      setSaved(true);
      setTimeout(() => setSaved(false), 2000);
    } catch (err) {
      console.error('Failed to update profile:', err);
    } finally {
      setSaving(false);
    }
  };

  const handleChangePassword = async (e: React.FormEvent) => {
    e.preventDefault();
    setPasswordError('');
    setPasswordSuccess('');
    setPasswordSaving(true);
    try {
      await settingsApi.updatePassword(currentPassword, newPassword);
      setPasswordSuccess('Password updated successfully');
      setCurrentPassword('');
      setNewPassword('');
    } catch (err: any) {
      setPasswordError(err.response?.data?.error || 'Failed to update password');
    } finally {
      setPasswordSaving(false);
    }
  };

  const addInterest = async () => {
    if (!newKeyword.trim()) return;
    try {
      const data = await trendsApi.addInterest(newKeyword);
      setInterests((prev) => [data.interest, ...prev]);
      setNewKeyword('');
    } catch (err: any) {
      console.error('Failed to add interest:', err);
    }
  };

  const removeInterest = async (id: string) => {
    try {
      await trendsApi.removeInterest(id);
      setInterests((prev) => prev.filter((i) => i.id !== id));
    } catch (err) {
      console.error('Failed to remove interest:', err);
    }
  };

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-white">Settings</h1>
        <p className="mt-1 text-gray-400">Manage your account and preferences</p>
      </div>

      <div className="space-y-6 max-w-2xl">
        {/* Profile Section */}
        <div className="card">
          <h3 className="font-semibold text-white flex items-center gap-2 mb-4">
            <User className="h-4 w-4 text-brand-400" />
            Profile
          </h3>

          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1.5">Email</label>
              <input
                type="email"
                className="input bg-gray-800/30 text-gray-500 cursor-not-allowed"
                value={user?.email || ''}
                disabled
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1.5">Name</label>
              <input
                type="text"
                className="input"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="Your name"
              />
            </div>

            <div className="flex items-center gap-3">
              <button onClick={handleSaveProfile} className="btn-primary" disabled={saving}>
                {saving ? <Loader2 className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />}
                Save
              </button>
              {saved && (
                <span className="flex items-center gap-1 text-sm text-emerald-400">
                  <CheckCircle className="h-4 w-4" /> Saved
                </span>
              )}
            </div>
          </div>
        </div>

        {/* Password Section */}
        <div className="card">
          <h3 className="font-semibold text-white flex items-center gap-2 mb-4">
            <Key className="h-4 w-4 text-brand-400" />
            Change Password
          </h3>

          <form onSubmit={handleChangePassword} className="space-y-4">
            {passwordError && (
              <div className="rounded-lg bg-red-900/50 border border-red-800 px-4 py-2 text-sm text-red-400">
                {passwordError}
              </div>
            )}
            {passwordSuccess && (
              <div className="rounded-lg bg-emerald-900/50 border border-emerald-800 px-4 py-2 text-sm text-emerald-400">
                {passwordSuccess}
              </div>
            )}

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1.5">Current Password</label>
              <input
                type="password"
                className="input"
                value={currentPassword}
                onChange={(e) => setCurrentPassword(e.target.value)}
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1.5">New Password</label>
              <input
                type="password"
                className="input"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                required
                minLength={6}
              />
            </div>

            <button type="submit" className="btn-primary" disabled={passwordSaving}>
              {passwordSaving ? <Loader2 className="h-4 w-4 animate-spin" /> : null}
              Update Password
            </button>
          </form>
        </div>

        {/* Interests Section */}
        <div className="card">
          <h3 className="font-semibold text-white flex items-center gap-2 mb-4">
            <Hash className="h-4 w-4 text-brand-400" />
            Interests
          </h3>
          <p className="text-sm text-gray-400 mb-4">
            Used to personalize your YouTube trends feed.
          </p>

          <div className="flex gap-2 mb-3">
            <input
              type="text"
              className="input flex-1"
              placeholder="e.g., AI, basketball, cooking..."
              value={newKeyword}
              onChange={(e) => setNewKeyword(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && addInterest()}
            />
            <button onClick={addInterest} className="btn-primary" disabled={!newKeyword.trim()}>
              <Plus className="h-4 w-4" />
              Add
            </button>
          </div>

          <div className="flex flex-wrap gap-2">
            {interests.length === 0 && (
              <p className="text-sm text-gray-500">No interests added yet.</p>
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

        {/* Billing Section */}
        <div className="card">
          <h3 className="font-semibold text-white flex items-center gap-2 mb-4">
            <CreditCard className="h-4 w-4 text-brand-400" />
            Billing
          </h3>

          {user?.paid ? (
            <div className="flex items-center gap-3 text-sm">
              <CheckCircle className="h-5 w-5 text-emerald-400" />
              <span className="text-gray-300">You have lifetime access</span>
            </div>
          ) : (
            <div>
              <p className="text-sm text-gray-400 mb-3">
                Purchase lifetime access to unlock all features.
              </p>
              <button
                onClick={() => navigate('/pricing')}
                className="btn-primary"
              >
                Get Lifetime Access — 299 EGP
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
