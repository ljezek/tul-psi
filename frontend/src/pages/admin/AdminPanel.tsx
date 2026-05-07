import { NavLink, Outlet } from 'react-router-dom';
import { Users, BellRing } from 'lucide-react';
import { useLanguage } from '@/contexts/LanguageContext';

export const AdminPanel = () => {
  const { t } = useLanguage();

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12 space-y-6 animate-fade-in">
      <h1 className="text-3xl font-black text-slate-900">{t('nav.admin_panel')}</h1>

      {/* Tab bar */}
      <div className="border-b border-slate-200">
        <nav className="flex gap-1" aria-label={t('nav.admin_panel')}>
          <NavLink
            to="/admin/users"
            className={({ isActive }) =>
              `flex items-center gap-2 px-4 py-3 text-sm font-bold border-b-2 -mb-px transition-colors ${
                isActive
                  ? 'border-fm-orange text-fm-orange'
                  : 'border-transparent text-slate-500 hover:text-slate-700 hover:border-slate-300'
              }`
            }
          >
            <Users size={16} />
            {t('admin.user_management')}
          </NavLink>
          <NavLink
            to="/admin/announcements"
            className={({ isActive }) =>
              `flex items-center gap-2 px-4 py-3 text-sm font-bold border-b-2 -mb-px transition-colors ${
                isActive
                  ? 'border-fm-orange text-fm-orange'
                  : 'border-transparent text-slate-500 hover:text-slate-700 hover:border-slate-300'
              }`
            }
          >
            <BellRing size={16} />
            {t('admin.announcements')}
          </NavLink>
        </nav>
      </div>

      <Outlet />
    </div>
  );
};
