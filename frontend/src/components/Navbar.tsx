import React, { useState } from 'react';
import { Link, NavLink } from 'react-router-dom';
import { Globe, Menu, X } from 'lucide-react';
import { useLanguage } from '../contexts/LanguageContext';

const Navbar: React.FC = () => {
  const { t, language, setLanguage } = useLanguage();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const toggleLanguage = () => {
    setLanguage(language === 'cs' ? 'en' : 'cs');
  };

  const navLinkClass = ({ isActive }: { isActive: boolean }) =>
    `px-3 py-2 rounded-md text-sm font-medium transition-colors ${
      isActive
        ? 'text-tul-blue font-semibold'
        : 'text-slate-600 hover:text-slate-900'
    }`;

  return (
    <nav className="sticky top-0 z-40 bg-white/80 backdrop-blur-md border-b border-slate-200/60 shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16 items-center">
          {/* Logo */}
          <Link to="/" className="flex items-center gap-3">
            <div className="bg-tul-blue w-8 h-8 rounded flex items-center justify-center text-white font-bold text-sm">
              FM
            </div>
            <span className="text-xl font-bold text-slate-800 tracking-tight">
              {language === 'cs' ? 'Katalog' : 'Project'}{' '}
              <span className="text-tul-blue">
                {language === 'cs' ? 'Projektů' : 'Catalog'}
              </span>
            </span>
          </Link>

          {/* Desktop navigation */}
          <div className="hidden md:flex items-center gap-2">
            <NavLink to="/catalog" className={navLinkClass}>
              {t('nav.catalog')}
            </NavLink>
            <NavLink to="/student" className={navLinkClass}>
              {t('nav.student')}
            </NavLink>
            <NavLink to="/admin" className={navLinkClass}>
              {t('nav.admin')}
            </NavLink>

            <button
              onClick={toggleLanguage}
              className="ml-2 flex items-center gap-2 text-sm font-semibold text-slate-600 hover:text-tul-blue transition-colors px-2 py-1"
              aria-label="Toggle language"
            >
              <Globe size={18} />
              <span>{language.toUpperCase()}</span>
            </button>
          </div>

          {/* Mobile controls */}
          <div className="md:hidden flex items-center gap-3">
            <button
              onClick={toggleLanguage}
              className="text-sm font-bold text-slate-600"
              aria-label="Toggle language"
            >
              {language.toUpperCase()}
            </button>
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="p-2 text-slate-600"
              aria-label="Toggle menu"
            >
              {mobileMenuOpen ? <X size={20} /> : <Menu size={20} />}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile menu */}
      {mobileMenuOpen && (
        <div className="md:hidden bg-white border-t border-slate-200 px-4 py-3 space-y-1">
          <NavLink
            to="/catalog"
            className={navLinkClass}
            onClick={() => setMobileMenuOpen(false)}
          >
            {t('nav.catalog')}
          </NavLink>
          <NavLink
            to="/student"
            className={navLinkClass}
            onClick={() => setMobileMenuOpen(false)}
          >
            {t('nav.student')}
          </NavLink>
          <NavLink
            to="/admin"
            className={navLinkClass}
            onClick={() => setMobileMenuOpen(false)}
          >
            {t('nav.admin')}
          </NavLink>
        </div>
      )}
    </nav>
  );
};

export default Navbar;
