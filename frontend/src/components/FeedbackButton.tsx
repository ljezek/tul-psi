import { useState, FormEvent, useEffect } from 'react';
import { MessageSquare, Send, CheckCircle, AlertCircle } from 'lucide-react';
import { useLocation } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { useLanguage } from '@/contexts/LanguageContext';
import { config } from '@/config';
import { Modal } from '@/components/ui/Modal';
import { Button } from '@/components/ui/Button';

export const FeedbackButton = () => {
  const { t } = useLanguage();
  const { user } = useAuth();
  const location = useLocation();
  
  const [isOpen, setIsOpen] = useState(false);
  const [email, setEmail] = useState('');
  const [feedback, setFeedback] = useState('');
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState<'idle' | 'success' | 'error'>('idle');

  useEffect(() => {
    if (user?.email && !email) {
      setEmail(user.email);
    }
  }, [user, isOpen]);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!feedback.trim()) return;

    setLoading(true);
    setStatus('idle');

    try {
      const payload: Record<string, string> = {
        feedback,
        url: window.location.origin + location.pathname + location.search,
      };

      if (email.trim()) {
        payload.email = email.trim();
      }

      const response = await fetch(config.logicAppFeedbackUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        throw new Error('Failed to submit feedback');
      }

      setStatus('success');
      setFeedback('');
      setTimeout(() => {
        setIsOpen(false);
        setStatus('idle');
      }, 2000);
    } catch (error) {
      console.error('Feedback submission error:', error);
      setStatus('error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <button
        onClick={() => setIsOpen(true)}
        className="flex items-center text-slate-600 hover:text-tul-blue font-bold px-3 py-2 rounded-lg transition-all hover:bg-slate-50"
        title={t('feedback.button')}
      >
        <MessageSquare size={18} />
      </button>

      <Modal
        isOpen={isOpen}
        onClose={() => setIsOpen(false)}
        title={t('feedback.title')}
      >
        <form onSubmit={handleSubmit} className="space-y-6 pb-4">
          {status === 'success' ? (
            <div className="py-8 text-center space-y-4 animate-in fade-in zoom-in-95">
              <div className="w-16 h-16 bg-green-100 text-green-600 rounded-full flex items-center justify-center mx-auto">
                <CheckCircle size={32} />
              </div>
              <p className="font-bold text-slate-800">{t('feedback.success')}</p>
            </div>
          ) : (
            <>
              <div className="space-y-4">
                <div>
                  <label htmlFor="feedback-email" className="block text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1.5 ml-1">
                    {t('feedback.label_email')}
                  </label>
                  <input
                    id="feedback-email"
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder={t('login.email_placeholder')}
                    className="w-full bg-slate-50 border border-slate-200 rounded-xl px-4 py-2.5 text-slate-900 focus:outline-none focus:ring-2 focus:ring-tul-blue/20 font-bold"
                  />
                </div>

                <div>
                  <label htmlFor="feedback-text" className="block text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1.5 ml-1">
                    {t('feedback.label_text')}
                  </label>
                  <textarea
                    id="feedback-text"
                    required
                    rows={4}
                    value={feedback}
                    onChange={(e) => setFeedback(e.target.value)}
                    placeholder={t('feedback.placeholder_text')}
                    className="w-full bg-slate-50 border border-slate-200 rounded-xl px-4 py-2.5 text-slate-900 focus:outline-none focus:ring-2 focus:ring-tul-blue/20 font-bold resize-none text-sm"
                  />
                </div>
              </div>

              {status === 'error' && (
                <div className="flex items-center gap-2 text-red-600 bg-red-50 p-4 rounded-xl border border-red-100 text-sm font-bold animate-in slide-in-from-top-1">
                  <AlertCircle size={18} />
                  {t('feedback.error')}
                </div>
              )}

              <div className="flex justify-end gap-3 pt-4 border-t border-slate-100">
                <Button 
                  type="button" 
                  variant="ghost" 
                  onClick={() => setIsOpen(false)}
                  disabled={loading}
                >
                  {t('common.cancel')}
                </Button>
                <Button
                  type="submit"
                  isLoading={loading}
                  disabled={!feedback.trim()}
                  className="px-8 shadow-lg shadow-tul-blue/20"
                >
                  <Send size={18} className="mr-2" />
                  {t('feedback.submit')}
                </Button>
              </div>
            </>
          )}
        </form>
      </Modal>
    </>
  );
};
