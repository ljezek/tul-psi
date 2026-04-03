import { useLanguage } from '@/contexts/LanguageContext';
import { ProfileForm } from '@/components/ProfileForm';
import { User } from 'lucide-react';

export const Profile = () => {
  const { t } = useLanguage();

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      <div className="max-w-md mx-auto">
        <div className="flex items-center gap-4 mb-8">
          <div className="bg-tul-blue w-12 h-12 rounded-2xl flex items-center justify-center text-white shadow-lg shadow-tul-blue/20">
            <User size={24} />
          </div>
          <div>
            <h1 className="text-3xl font-black text-slate-800 tracking-tight">
              {t('profile.title')}
            </h1>
            <p className="text-slate-500 font-medium italic">
              {t('profile.editing')}
            </p>
          </div>
        </div>

        <div className="bg-white rounded-3xl shadow-xl shadow-slate-200/50 border border-slate-100 p-8 overflow-hidden relative">
          <div className="absolute top-0 right-0 w-32 h-32 bg-tul-blue/5 rounded-full -mr-16 -mt-16 blur-2xl"></div>
          
          <div className="relative z-10">
            <ProfileForm />
          </div>
        </div>
      </div>
    </div>
  );
};
