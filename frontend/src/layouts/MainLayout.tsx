import { useState } from 'react';
import { Outlet, Link, useNavigate } from 'react-router-dom';
import { Menu, X, Globe, LogIn, LogOut, Shield, BookOpen, RefreshCw, Moon, Sun, BellRing } from 'lucide-react';
import { useLanguage } from '@/contexts/LanguageContext';
import { useTheme } from '@/contexts/ThemeContext';
import { useAuth } from '@/contexts/AuthContext';
import { UserRole } from '@/types';
import { Button } from '@/components/ui/Button';
import { ProfileDropdown } from '@/components/ProfileDropdown';
import { FeedbackButton } from '@/components/FeedbackButton';
import { EnvironmentRibbon } from '@/components/EnvironmentRibbon';
import { AnnouncementBanner } from '@/components/AnnouncementBanner';

export const MainLayout = () => {
  const { t, language, setLanguage } = useLanguage();
  const { theme, toggleTheme } = useTheme();
  const { user, logout, isResurrecting } = useAuth();
  const navigate = useNavigate();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const toggleLanguage = () => {
    setLanguage(language === 'cs' ? 'en' : 'cs');
  };

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  const NavLinks = () => (
    <>
      <Link to="/" className="text-slate-600 hover:text-fm-orange font-bold px-3 py-2 rounded-lg transition-all hover:bg-slate-50 dark:text-slate-300 dark:hover:bg-slate-800">
        {t('nav.dashboard')}
      </Link>
      <Link to="/courses" className="text-slate-600 hover:text-fm-orange font-bold px-3 py-2 rounded-lg transition-all hover:bg-slate-50 dark:text-slate-300 dark:hover:bg-slate-800">
        {t('nav.courses')}
      </Link>
      {user?.role === UserRole.STUDENT && (
        <Link to="/student" className="text-slate-600 hover:text-fm-orange font-bold px-3 py-2 rounded-lg transition-all hover:bg-slate-50 dark:text-slate-300 dark:hover:bg-slate-800">
          {t('nav.student_zone')}
        </Link>
      )}
      {user?.role === UserRole.ADMIN && (
        <>
          <Link to="/lecturer" className="text-slate-600 hover:text-fm-orange font-bold px-3 py-2 rounded-lg transition-all hover:bg-slate-50 flex items-center gap-2 dark:text-slate-300 dark:hover:bg-slate-800">
            <BookOpen size={16} />
            {t('nav.lecturer_panel')}
          </Link>
          <Link to="/admin/users" className="text-slate-600 hover:text-fm-orange font-bold px-3 py-2 rounded-lg transition-all hover:bg-slate-50 flex items-center gap-2 dark:text-slate-300 dark:hover:bg-slate-800">
            <Shield size={16} />
            {t('admin.user_management')}
          </Link>
          <Link to="/admin/announcements" className="text-slate-600 hover:text-fm-orange font-bold px-3 py-2 rounded-lg transition-all hover:bg-slate-50 flex items-center gap-2 dark:text-slate-300 dark:hover:bg-slate-800">
            <BellRing size={16} />
            {t('admin.announcements')}
          </Link>
        </>
      )}
      {user?.role === UserRole.LECTURER && (
        <Link to="/lecturer" className="text-slate-600 hover:text-fm-orange font-bold px-3 py-2 rounded-lg transition-all hover:bg-slate-50 dark:text-slate-300 dark:hover:bg-slate-800">
          {t('nav.lecturer_panel')}
        </Link>
      )}
    </>
  );

  return (
    <div className="min-h-screen flex flex-col bg-slate-50 dark:bg-slate-900">
      <EnvironmentRibbon />
      {/* Navigation Bar */}
      <nav className="sticky top-0 z-40 bg-white/90 backdrop-blur-lg border-b border-slate-200/60 shadow-sm dark:bg-slate-900/90 dark:border-slate-700/60">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-20 items-center">
            {/* Logo */}
            <Link to="/" className="flex items-center gap-3 group">
              <div className="bg-fm-orange w-9 h-9 rounded-xl flex items-center justify-center text-white font-black shadow-lg shadow-fm-orange/20 group-hover:scale-105 transition-transform">
                FM
              </div>
              <div className="flex flex-col leading-none">
                <span className="text-[10px] font-black tracking-widest text-fm-orange uppercase">FM TUL</span>
                <span className="text-lg font-black text-slate-800 tracking-tighter dark:text-slate-100">
                  {t('app.title')}
                </span>
              </div>
            </Link>

            {/* Desktop Navigation */}
            <div className="hidden md:flex items-center gap-6">
              <div className="flex items-center gap-1">
                <NavLinks />
              </div>

              <div className="h-6 w-px bg-slate-200 mx-2 dark:bg-slate-700"></div>

              <div className="flex items-center gap-4">
                <button
                  onClick={toggleLanguage}
                  className="flex items-center gap-2 text-xs font-black tracking-widest text-slate-400 hover:text-fm-orange transition-colors px-3 py-1.5 rounded-lg border border-slate-100 bg-slate-50 uppercase cursor-pointer dark:border-slate-700 dark:bg-slate-800 dark:text-slate-500 dark:hover:text-fm-orange"
                >
                  <Globe size={14} />
                  <span>{language}</span>
                </button>

                <button
                  onClick={toggleTheme}
                  aria-label={theme === 'light' ? t('theme.to_dark') : t('theme.to_light')}
                  className="flex items-center text-slate-400 hover:text-fm-orange transition-colors px-2.5 py-1.5 rounded-lg border border-slate-100 bg-slate-50 cursor-pointer dark:border-slate-700 dark:bg-slate-800 dark:text-slate-500 dark:hover:text-fm-orange"
                >
                  {theme === 'light' ? <Moon size={14} /> : <Sun size={14} />}
                </button>

                <FeedbackButton />

                {user ? (
                  <div className="flex items-center gap-4">
                    <div className="flex items-center gap-3">
                      <ProfileDropdown />
                    </div>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={handleLogout}
                      className="text-slate-400 hover:text-red-600 hover:bg-red-50 rounded-xl dark:hover:bg-red-950"
                    >
                      <LogOut size={20} />
                    </Button>
                  </div>
                ) : (
                  <Link to="/login">
                    <Button variant="outline" size="sm" className="rounded-xl border-slate-200 font-bold px-5">
                      <LogIn size={18} className="mr-2" />
                      {t('nav.login')}
                    </Button>
                  </Link>
                )}
              </div>
            </div>

            {/* Mobile menu button */}
            <div className="md:hidden flex items-center gap-4">
              <button
                onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
                className="p-2 text-slate-600 rounded-xl hover:bg-slate-100 transition-colors cursor-pointer dark:text-slate-400 dark:hover:bg-slate-800"
                aria-label={mobileMenuOpen ? t('nav.close_menu') : t('nav.open_menu')}
                aria-expanded={mobileMenuOpen}
                aria-controls="mobile-nav-menu"
              >
                {mobileMenuOpen ? <X /> : <Menu />}
              </button>
            </div>
          </div>
        </div>

        {/* Mobile Navigation Menu */}
        {mobileMenuOpen && (
          <div id="mobile-nav-menu" className="md:hidden bg-white border-t border-slate-100 p-6 space-y-6 animate-in slide-in-from-top-4 duration-300 dark:bg-slate-900 dark:border-slate-800">
            <div className="flex flex-col gap-3">
              <NavLinks />
              <div className="pt-2 border-t border-slate-50 md:hidden dark:border-slate-800">
                <FeedbackButton />
              </div>
            </div>

            <div className="pt-6 border-t border-slate-100 dark:border-slate-800">
              <div className="flex items-center justify-between mb-6">
                <button
                  onClick={toggleLanguage}
                  className="flex items-center gap-2 text-xs font-black tracking-widest text-slate-500 bg-slate-50 px-4 py-2 rounded-xl border border-slate-100 uppercase cursor-pointer dark:text-slate-400 dark:bg-slate-800 dark:border-slate-700"
                >
                  <Globe size={16} />
                  {language === 'cs' ? 'Čeština' : 'English'}
                </button>

                <button
                  onClick={toggleTheme}
                  aria-label={theme === 'light' ? t('theme.to_dark') : t('theme.to_light')}
                  className="flex items-center gap-2 text-xs font-black tracking-widest text-slate-500 bg-slate-50 px-4 py-2 rounded-xl border border-slate-100 uppercase cursor-pointer dark:text-slate-400 dark:bg-slate-800 dark:border-slate-700"
                >
                  {theme === 'light' ? <Moon size={16} /> : <Sun size={16} />}
                  <span>{theme === 'light' ? t('theme.to_dark') : t('theme.to_light')}</span>
                </button>
              </div>

              {user ? (
                <div className="space-y-6">
                  <div className="flex flex-col gap-3">
                    <div className="flex items-center justify-between px-2">
                       <span className="font-bold text-slate-800 dark:text-slate-200">{user.name}</span>
                       <span className="text-xs font-bold text-slate-400 uppercase tracking-widest">{user.role}</span>
                    </div>
                    <Link to="/profile" onClick={() => setMobileMenuOpen(false)}>
                       <Button variant="outline" className="w-full justify-center rounded-xl font-bold py-3">
                         {t('profile.editing')}
                       </Button>
                    </Link>
                    <Button
                      variant="ghost"
                      className="w-full justify-center text-red-600 hover:bg-red-50 rounded-xl font-bold py-3 dark:hover:bg-red-950"
                      onClick={() => { handleLogout(); setMobileMenuOpen(false); }}
                    >
                      <LogOut size={18} className="mr-2" />
                      {t('nav.logout')}
                    </Button>
                  </div>
                </div>
              ) : (
                <Link to="/login" onClick={() => setMobileMenuOpen(false)}>
                  <Button variant="outline" className="w-full justify-center rounded-xl font-bold py-4 border-slate-200">
                    <LogIn size={18} className="mr-2" />
                    {t('nav.login')}
                  </Button>
                </Link>
              )}
            </div>
          </div>
        )}
      </nav>

      {/* Backend Resurrection Banner */}
      {isResurrecting && (
        <div className="bg-fm-orange text-white py-2 px-4 flex items-center justify-center gap-3 animate-pulse sticky top-20 z-30 shadow-md">
          <RefreshCw size={16} className="animate-spin" />
          <span className="text-sm font-bold tracking-wide">{t('common.resurrecting')}</span>
        </div>
      )}

      {/* System Announcement Banner */}
      <AnnouncementBanner />

      {/* Main Content Area */}
      <main className="flex-grow w-full">
        <Outlet />
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-slate-200 py-12 mt-auto dark:bg-slate-900 dark:border-slate-800">
        <div className="max-w-7xl mx-auto px-4">
          <div className="flex flex-col md:flex-row justify-between items-center gap-6">
            <div className="flex items-center gap-3">
              <div className="bg-slate-200 w-8 h-8 rounded-lg flex items-center justify-center text-slate-500 font-bold text-sm dark:bg-slate-700 dark:text-slate-400">
                FM
              </div>
              <span className="text-slate-400 font-bold text-sm uppercase tracking-wider">
                TUL PSI {new Date().getFullYear()}
              </span>
            </div>

            <div className="text-slate-500 text-sm text-center md:text-right dark:text-slate-400">
              <p className="font-medium">{t('footer.copyright')}</p>
              <p className="text-slate-400 text-xs mt-1 dark:text-slate-500">
                <a
                  href="https://www.fm.tul.cz"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="hover:text-fm-orange transition-colors"
                >
                  Fakulta mechatroniky, informatiky a mezioborových studií
                </a>
                {' | '}
                <a
                  href="https://www.tul.cz"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="hover:text-fm-orange transition-colors"
                >
                  Technická univerzita v Liberci
                </a>
                {' | '}
                Studentská 1402/2 | 461 17 Liberec 1
              </p>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
};
