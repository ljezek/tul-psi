import { useState } from 'react';
import { Outlet, Link, useNavigate } from 'react-router-dom';
import { Menu, X, Globe, LogIn, LogOut, User as UserIcon } from 'lucide-react';
import { useLanguage } from '@/contexts/LanguageContext';
import { useAuth } from '@/contexts/AuthContext';
import { UserRole } from '@/types';
import { Button } from '@/components/ui/Button';

export const MainLayout = () => {
  const { t, language, setLanguage } = useLanguage();
  const { user, logout } = useAuth();
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
      <Link to="/" className="text-slate-600 hover:text-tul-blue font-medium px-3 py-2 rounded-md transition-colors">
        {t('nav.dashboard')}
      </Link>
      {user?.role === UserRole.STUDENT && (
        <Link to="/student" className="text-slate-600 hover:text-tul-blue font-medium px-3 py-2 rounded-md transition-colors">
          {t('nav.student_zone')}
        </Link>
      )}
      {(user?.role === UserRole.LECTURER || user?.role === UserRole.ADMIN) && (
        <Link to="/lecturer" className="text-slate-600 hover:text-tul-blue font-medium px-3 py-2 rounded-md transition-colors">
          {t('nav.lecturer_panel')}
        </Link>
      )}
    </>
  );

  return (
    <div className="min-h-screen flex flex-col bg-slate-50">
      {/* Navigation Bar */}
      <nav className="sticky top-0 z-40 bg-white/80 backdrop-blur-md border-b border-white/20 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16 items-center">
            {/* Logo */}
            <Link to="/" className="flex items-center gap-3">
              <div className="bg-tul-blue w-8 h-8 rounded flex items-center justify-center text-white font-bold">
                FM
              </div>
              <span className="text-xl font-bold text-slate-800 tracking-tight">
                {t('app.title')}
              </span>
            </Link>

            {/* Desktop Navigation */}
            <div className="hidden md:flex items-center gap-6">
              <div className="flex items-center gap-2">
                <NavLinks />
              </div>

              <div className="h-6 w-px bg-slate-200"></div>

              <div className="flex items-center gap-4">
                <button 
                  onClick={toggleLanguage}
                  className="flex items-center gap-2 text-sm font-semibold text-slate-600 hover:text-tul-blue transition-colors px-2 py-1"
                >
                  <Globe size={18} />
                  <span>{language.toUpperCase()}</span>
                </button>

                {user ? (
                  <div className="flex items-center gap-4">
                    <div className="flex items-center gap-2 text-sm text-slate-700">
                      <UserIcon size={16} />
                      <span className="font-medium">{user.name}</span>
                      <span className="px-2 py-0.5 bg-slate-100 rounded text-xs text-slate-500 font-semibold uppercase">
                        {user.role}
                      </span>
                    </div>
                    <Button variant="ghost" size="sm" onClick={handleLogout} className="text-slate-500 hover:text-red-600">
                      <LogOut size={16} className="mr-2" />
                      {t('nav.logout')}
                    </Button>
                  </div>
                ) : (
                  <Link to="/login">
                    <Button variant="outline" size="sm">
                      <LogIn size={16} className="mr-2" />
                      {t('nav.login')}
                    </Button>
                  </Link>
                )}
              </div>
            </div>

            {/* Mobile menu button */}
            <div className="md:hidden flex items-center gap-4">
              <button 
                onClick={toggleLanguage}
                className="flex items-center gap-1 text-sm font-bold text-slate-600"
              >
                {language.toUpperCase()}
              </button>
              <button
                onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
                className="p-2 text-slate-600"
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
          <div id="mobile-nav-menu" className="md:hidden bg-white border-t border-slate-200 p-4 space-y-4">
            <div className="flex flex-col gap-2">
              <NavLinks />
            </div>
            
            <div className="pt-4 border-t border-slate-100">
              {user ? (
                <div className="space-y-4">
                  <div className="flex items-center gap-2 text-sm text-slate-700 px-3">
                    <UserIcon size={16} />
                    <span className="font-medium">{user.name}</span>
                    <span className="px-2 py-0.5 bg-slate-100 rounded text-xs text-slate-500 font-semibold uppercase">
                      {user.role}
                    </span>
                  </div>
                  <Button variant="ghost" className="w-full justify-start text-slate-500 hover:text-red-600" onClick={() => { handleLogout(); setMobileMenuOpen(false); }}>
                    <LogOut size={16} className="mr-2" />
                    {t('nav.logout')}
                  </Button>
                </div>
              ) : (
                <Link to="/login" onClick={() => setMobileMenuOpen(false)}>
                  <Button variant="outline" className="w-full justify-start">
                    <LogIn size={16} className="mr-2" />
                    {t('nav.login')}
                  </Button>
                </Link>
              )}
            </div>
          </div>
        )}
      </nav>

      {/* Main Content Area */}
      <main className="flex-grow w-full">
        <Outlet />
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-slate-200 py-8 mt-auto">
        <div className="max-w-7xl mx-auto px-4 text-center">
          <p className="text-slate-500 text-sm">
            © {new Date().getFullYear()} {t('footer.copyright')}
          </p>
          <p className="text-slate-400 text-xs mt-2">
            Technická univerzita v Liberci | Studentská 1402/2 | 461 17 Liberec 1
          </p>
        </div>
      </footer>
    </div>
  );
};
