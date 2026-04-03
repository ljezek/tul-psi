import { useState, useEffect, useRef, FormEvent } from 'react';
import { User, Save, CheckCircle, X, Mail, Shield } from 'lucide-react';
import { GitHubLogo } from '@/components/icons/GitHubLogo';
import { useAuth } from '@/contexts/AuthContext';
import { useLanguage } from '@/contexts/LanguageContext';
import { updateCurrentUser } from '@/api';
import { Button } from '@/components/ui/Button';
import { UserRole } from '@/types';

export const ProfileDropdown = () => {
  const { user, refreshUser } = useAuth();
  const { t } = useLanguage();
  const [isOpen, setIsOpen] = useState(false);
  const [name, setName] = useState(user?.name || '');
  const [github, setGithub] = useState(user?.github_alias || '');
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (user) {
      setName(user.name);
      setGithub(user.github_alias || '');
    }
  }, [user]);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleSave = async (e: FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setSuccess(false);
    try {
      await updateCurrentUser({ name, github_alias: github || null });
      await refreshUser();
      setSuccess(true);
      setTimeout(() => setSuccess(false), 2000);
    } catch (error) {
      console.error('Failed to update profile:', error);
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
    <div className="relative" ref={dropdownRef}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 text-sm font-semibold text-slate-700 hover:text-tul-blue transition-all px-2.5 py-1.5 rounded-xl hover:bg-slate-100 group"
      >
        <div className="w-8 h-8 rounded-full bg-tul-blue/10 flex items-center justify-center text-tul-blue group-hover:bg-tul-blue group-hover:text-white transition-colors">
          <User size={18} />
        </div>
        <span className="max-w-[150px] truncate">{user.name}</span>
      </button>

      {isOpen && (
        <div className="absolute right-0 mt-3 w-80 bg-white rounded-2xl shadow-2xl border border-slate-100 z-50 overflow-hidden animate-in fade-in zoom-in-95 duration-200">
          <div className="p-4 bg-slate-50 border-b border-slate-100 flex justify-between items-center">
            <h3 className="font-bold text-slate-800">{t('profile.editing')}</h3>
            <button 
              onClick={() => setIsOpen(false)} 
              className="p-1 rounded-full hover:bg-slate-200 text-slate-400 hover:text-slate-600 transition-colors"
            >
              <X size={18} />
            </button>
          </div>
          
          <div className="p-5 border-b border-slate-50 space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 text-[10px] font-black text-slate-400 uppercase tracking-[0.15em]">
                <Shield size={12} />
                {t('profile.role') || 'Role'}
              </div>
              <RoleBadge role={user.role} />
            </div>
            
            <div className="space-y-1.5">
              <div className="flex items-center gap-2 text-[10px] font-black text-slate-400 uppercase tracking-[0.15em]">
                <Mail size={12} />
                {t('login.email_label')}
              </div>
              <div className="text-sm font-medium text-slate-600 bg-slate-50 px-3 py-2 rounded-lg border border-slate-100 break-all">
                {user.email}
              </div>
            </div>
          </div>

          <form onSubmit={handleSave} className="p-5 space-y-5">
            <div>
              <label className="block text-[10px] font-black text-slate-400 uppercase tracking-[0.15em] mb-1.5 ml-1">
                {t('profile.name')}
              </label>
              <div className="relative group">
                <User size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400 group-focus-within:text-tul-blue transition-colors" />
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="w-full pl-10 pr-3 py-2.5 text-sm border border-slate-200 rounded-xl focus:outline-none focus:ring-4 focus:ring-tul-blue/10 focus:border-tul-blue transition-all bg-slate-50 focus:bg-white"
                  required
                />
              </div>
            </div>

            <div>
              <label className="block text-[10px] font-black text-slate-400 uppercase tracking-[0.15em] mb-1.5 ml-1">
                {t('profile.github')}
              </label>
              <div className="relative group">
                <GitHubLogo size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400 group-focus-within:text-tul-blue transition-colors" />
                <input
                  type="text"
                  value={github}
                  onChange={(e) => setGithub(e.target.value)}
                  className="w-full pl-10 pr-3 py-2.5 text-sm border border-slate-200 rounded-xl focus:outline-none focus:ring-4 focus:ring-tul-blue/10 focus:border-tul-blue transition-all bg-slate-50 focus:bg-white"
                  placeholder="github-username"
                />
              </div>
            </div>

            <Button
              type="submit"
              disabled={loading}
              className={`w-full py-3 rounded-xl text-sm font-bold flex items-center justify-center gap-2 transition-all ${
                success ? 'bg-green-600 hover:bg-green-700' : ''
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
      )}
    </div>
  );
};
