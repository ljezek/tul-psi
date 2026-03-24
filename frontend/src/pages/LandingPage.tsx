import React from 'react';
import { Link } from 'react-router-dom';
import { LayoutGrid, GraduationCap, Shield } from 'lucide-react';
import { useLanguage } from '../contexts/LanguageContext';

const LandingPage: React.FC = () => {
  const { t } = useLanguage();

  const features = [
    {
      icon: <LayoutGrid size={28} className="text-tul-blue" />,
      title: t('landing.feature_browse_title'),
      desc: t('landing.feature_browse_desc'),
    },
    {
      icon: <GraduationCap size={28} className="text-tul-blue" />,
      title: t('landing.feature_feedback_title'),
      desc: t('landing.feature_feedback_desc'),
    },
    {
      icon: <Shield size={28} className="text-tul-blue" />,
      title: t('landing.feature_admin_title'),
      desc: t('landing.feature_admin_desc'),
    },
  ];

  return (
    <div className="space-y-16">
      {/* Hero section */}
      <section className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-tul-blue to-blue-800 text-white px-8 py-16 md:py-24 text-center shadow-lg">
        <div className="relative z-10 max-w-3xl mx-auto">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-white/20 rounded-2xl mb-6">
            <LayoutGrid size={32} />
          </div>
          <h1 className="text-3xl md:text-5xl font-bold mb-4 leading-tight">
            {t('landing.hero_title')}
          </h1>
          <p className="text-blue-100 text-lg mb-8 leading-relaxed">
            {t('landing.hero_subtitle')}
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link
              to="/catalog"
              className="inline-flex items-center justify-center gap-2 bg-white text-tul-blue font-semibold px-6 py-3 rounded-lg hover:bg-blue-50 transition-colors shadow"
            >
              <LayoutGrid size={18} />
              {t('landing.cta_browse')}
            </Link>
            <Link
              to="/student"
              className="inline-flex items-center justify-center gap-2 bg-white/10 border border-white/30 text-white font-semibold px-6 py-3 rounded-lg hover:bg-white/20 transition-colors"
            >
              <GraduationCap size={18} />
              {t('landing.cta_student')}
            </Link>
          </div>
        </div>
      </section>

      {/* Features section */}
      <section>
        <h2 className="text-2xl font-bold text-slate-800 text-center mb-8">
          {t('landing.features_title')}
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {features.map((feature) => (
            <div
              key={feature.title}
              className="bg-white rounded-xl p-6 shadow-sm border border-slate-100 hover:shadow-md transition-shadow"
            >
              <div className="mb-4">{feature.icon}</div>
              <h3 className="text-lg font-semibold text-slate-800 mb-2">{feature.title}</h3>
              <p className="text-slate-500 text-sm leading-relaxed">{feature.desc}</p>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
};

export default LandingPage;
