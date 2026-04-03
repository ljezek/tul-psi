import { useState, useEffect, useRef } from 'react';
import { User, X } from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';
import { useLanguage } from '@/contexts/LanguageContext';
import { ProfileForm } from './ProfileForm';

export const ProfileDropdown = () => {
  const { user } = useAuth();
  const { t } = useLanguage();
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  if (!user) return null;

  return (
    <div className="relative" ref={dropdownRef}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        aria-haspopup="true"
        aria-expanded={isOpen}
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
          
          <div className="p-5">
            <ProfileForm />
          </div>
        </div>
      )}
    </div>
  );
};
