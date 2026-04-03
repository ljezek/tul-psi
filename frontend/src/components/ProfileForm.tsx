import { useState, useEffect, FormEvent } from 'react';
import { User, Save, CheckCircle, Mail, Shield } from 'lucide-react';
import { GitHubLogo } from '@/components/icons/GitHubLogo';
import { useAuth } from '@/contexts/AuthContext';
import { useLanguage } from '@/contexts/LanguageContext';
import { updateCurrentUser } from '@/api';
import { Button } from '@/components/ui/Button';
import { UserRole } from '@/types';

interface ProfileFormProps {
  onSuccess?: () => void;
}

export const ProfileForm = ({ onSuccess }: ProfileFormProps) => {
  const { user, refreshUser } = useAuth();
  const { t } = useLanguage();
  const [name, setName] = useState(user?.name || '');
  const [github, setGithub] = useState(user?.github_alias || '');
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (user) {
      setName(user.name);
      setGithub(user.github_alias || '');
    }
  }, [user]);

  const handleSave = async (e: FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setSuccess(false);
    setError(null);
    try {
      await updateCurrentUser({ name, github_alias: github || null });
      await refreshUser();
      setSuccess(true);
      if (onSuccess) onSuccess();
      setTimeout(() => setSuccess(false), 2000);
    } catch (err) {
      console.error('Failed to update profile:', err);
      setError(t('profile.error_update'));
    } finally {
      setLoading(false);
    }
  };

  if (!user) return null;

  const RoleBadge = ({ role }: { role: UserRole }) => {
    const roleColors: Record<UserRole, string> = {
      [UserRole.STUDENT]: 'bg-purple-100 text-purple-700 border-purple-200',
      [UserRole.LECTURER]: 'bg-tul-blue/10 text-tul-blue border-tul-blue/20',
      [UserRole.ADMIN]: 'bg-slate-800 text-white border-slate-900',
    };

    const roleKey = `role.${role.toLowerCase()}`;

    return (
      <span className={`px-2 py-0.5 rounded-full text-[10px] font-black uppercase tracking-wider border ${roleColors[role]}`}>
        {t(roleKey)}
      </span>
    );
  };

  return (
    <div className="space-y-6">
      <div className="p-5 bg-slate-50 rounded-2xl border border-slate-100 space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 text-[10px] font-black text-slate-400 uppercase tracking-[0.15em]">
            <Shield size={12} />
            {t('profile.role')}
          </div>
          <RoleBadge role={user.role} />
        </div>
        
        <div className="space-y-1.5">
          <div className="flex items-center gap-2 text-[10px] font-black text-slate-400 uppercase tracking-[0.15em]">
            <Mail size={12} />
            {t('login.email_label')}
          </div>
          <div className="text-sm font-medium text-slate-600 bg-white px-3 py-2.5 rounded-xl border border-slate-100 break-all shadow-sm">
            {user.email}
          </div>
        </div>
      </div>

      <form onSubmit={handleSave} className="space-y-5">
        <div>
          <label 
            htmlFor="profile-name"
            className="block text-[10px] font-black text-slate-400 uppercase tracking-[0.15em] mb-1.5 ml-1"
          >
            {t('profile.name')}
          </label>
          <div className="relative group">
            <User size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400 group-focus-within:text-tul-blue transition-colors" />
            <input
              id="profile-name"
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full pl-10 pr-3 py-3 text-sm border border-slate-200 rounded-xl focus:outline-none focus:ring-4 focus:ring-tul-blue/10 focus:border-tul-blue transition-all bg-slate-50 focus:bg-white"
              required
            />
          </div>
        </div>

        <div>
          <label 
            htmlFor="profile-github"
            className="block text-[10px] font-black text-slate-400 uppercase tracking-[0.15em] mb-1.5 ml-1"
          >
            {t('profile.github')}
          </label>
          <div className="relative group">
            <GitHubLogo size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400 group-focus-within:text-tul-blue transition-colors" />
            <input
              id="profile-github"
              type="text"
              value={github}
              onChange={(e) => setGithub(e.target.value)}
              className="w-full pl-10 pr-3 py-3 text-sm border border-slate-200 rounded-xl focus:outline-none focus:ring-4 focus:ring-tul-blue/10 focus:border-tul-blue transition-all bg-slate-50 focus:bg-white"
              placeholder="github-username"
            />
          </div>
        </div>

        {error && (
          <div className="text-sm text-red-600 font-medium bg-red-50 p-4 rounded-xl border border-red-100 animate-in fade-in slide-in-from-top-1">
            {error}
          </div>
        )}

        <Button
          type="submit"
          disabled={loading}
          className={`w-full py-4 rounded-xl text-sm font-bold flex items-center justify-center gap-2 transition-all shadow-lg ${
            success ? 'bg-green-600 hover:bg-green-700 shadow-green-200' : 'shadow-tul-blue/20'
          }`}
        >
          {loading ? (
            <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
          ) : success ? (
            <CheckCircle size={18} />
          ) : (
            <Save size={18} />
          )}
          {success ? t('profile.success') : t('profile.save')}
        </Button>
      </form>
    </div>
  );
};
