import React from 'react';
import { useLanguage } from '../contexts/LanguageContext';

const Footer: React.FC = () => {
  const { t } = useLanguage();

  return (
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
  );
};

export default Footer;
