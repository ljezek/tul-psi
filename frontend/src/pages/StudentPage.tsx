import React from 'react';
import { GraduationCap } from 'lucide-react';
import { useLanguage } from '../contexts/LanguageContext';

const StudentPage: React.FC = () => {
  const { t } = useLanguage();

  return (
    <div className="space-y-6">
      {/* Page header banner */}
      <div className="bg-tul-blue text-white p-8 rounded-2xl shadow-lg relative overflow-hidden">
        <div className="absolute right-0 top-0 opacity-10 transform translate-x-10 -translate-y-10">
          <GraduationCap size={180} />
        </div>
        <div className="relative z-10">
          <h1 className="text-2xl font-bold mb-1">{t('student.zone_title')}</h1>
          <p className="text-blue-100">{t('student.zone_desc')}</p>
        </div>
      </div>

      {/* Placeholder content */}
      <div className="bg-white border border-slate-200 rounded-xl p-12 text-center">
        <div className="inline-flex items-center justify-center w-14 h-14 bg-blue-50 rounded-full mb-4">
          <GraduationCap size={24} className="text-tul-blue" />
        </div>
        <p className="text-slate-400 text-sm">{t('student.coming_soon')}</p>
      </div>
    </div>
  );
};

export default StudentPage;
