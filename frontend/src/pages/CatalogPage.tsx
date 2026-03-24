import React from 'react';
import { Search } from 'lucide-react';
import { useLanguage } from '../contexts/LanguageContext';

const CatalogPage: React.FC = () => {
  const { t } = useLanguage();

  return (
    <div className="space-y-6">
      {/* Page header */}
      <div>
        <h1 className="text-3xl font-bold text-slate-800">{t('dashboard.title')}</h1>
        <p className="text-slate-500 mt-1">{t('dashboard.subtitle')}</p>
      </div>

      {/* Search & filters */}
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
          <input
            type="text"
            placeholder={t('dashboard.search_placeholder')}
            className="w-full pl-9 pr-4 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-tul-blue/30 focus:border-tul-blue bg-white"
            disabled
          />
        </div>
        <select
          className="px-3 py-2 border border-slate-200 rounded-lg text-sm bg-white text-slate-500"
          disabled
        >
          <option>{t('dashboard.all_subjects')}</option>
        </select>
        <select
          className="px-3 py-2 border border-slate-200 rounded-lg text-sm bg-white text-slate-500"
          disabled
        >
          <option>{t('dashboard.all_years')}</option>
        </select>
      </div>

      {/* Placeholder content */}
      <div className="bg-white border border-slate-200 rounded-xl p-12 text-center">
        <div className="inline-flex items-center justify-center w-14 h-14 bg-slate-100 rounded-full mb-4">
          <Search size={24} className="text-slate-400" />
        </div>
        <h2 className="text-lg font-semibold text-slate-700 mb-2">
          {t('dashboard.no_results')}
        </h2>
        <p className="text-slate-400 text-sm">{t('dashboard.coming_soon')}</p>
      </div>
    </div>
  );
};

export default CatalogPage;
