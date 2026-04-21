import { useState, FormEvent, useRef, KeyboardEvent, ClipboardEvent, useEffect } from 'react';
import { Navigate } from 'react-router-dom';
import { Mail, ArrowLeft, RefreshCw } from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';
import { useLanguage } from '@/contexts/LanguageContext';
import { requestOtp, ApiError } from '@/api';
import { Button } from '@/components/ui/Button';
import { UserRole } from '@/types';

export const Login = () => {
  const { user, login } = useAuth();
  const { t } = useLanguage();

  const [step, setStep] = useState<'email' | 'otp'>('email');
  const [emailPrefix, setEmailPrefix] = useState('');
  const [otpValues, setOtpValues] = useState(['', '', '', '', '', '']);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const otpRefs = useRef<(HTMLInputElement | null)[]>([]);

  const fullEmail = `${emailPrefix}@tul.cz`;
  const fullOtp = otpValues.join('');

  // Auto-submit when all 6 digits are filled
  useEffect(() => {
    if (fullOtp.length === 6 && step === 'otp' && !loading) {
      handleVerifyOtp();
    }
  }, [fullOtp]);

  const handleSendOtp = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!emailPrefix.trim()) {
      setError(t('login.error_invalid_email'));
      return;
    }

    setLoading(true);
    try {
      await requestOtp(fullEmail);
      setStep('otp');
    } catch (err) {
      if (err instanceof ApiError && err.status === 422) {
        setError(t('login.error_invalid_email'));
      } else {
        setError(t('login.error_unexpected'));
        console.error(err);
      }
    } finally {
      setLoading(false);
    }
  };

  const handleVerifyOtp = async (e?: FormEvent) => {
    e?.preventDefault();
    setError(null);

    if (fullOtp.length !== 6) {
      setError(t('login.error_invalid_otp'));
      return;
    }

    setLoading(true);
    try {
      await login(fullEmail, fullOtp);
    } catch (err) {
      if (err instanceof ApiError) {
        if (err.status === 401) {
          setError(t('login.error_invalid_otp'));
        } else if (err.status === 429) {
          setError(t('login.error_too_many'));
        } else {
          setError(t('login.error_unexpected'));
        }
      } else {
        setError(t('login.error_unexpected'));
        console.error(err);
      }
    } finally {
      setLoading(false);
    }
  };

  const handleResendOtp = async () => {
    setError(null);
    setLoading(true);
    try {
      await requestOtp(fullEmail);
    } catch (err) {
      setError(t('login.error_unexpected'));
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleOtpChange = (index: number, value: string) => {
    // Only allow numbers
    if (value && !/^\d$/.test(value)) return;

    const newOtpValues = [...otpValues];
    newOtpValues[index] = value;
    setOtpValues(newOtpValues);

    // Move to next input if value is entered
    if (value && index < 5) {
      otpRefs.current[index + 1]?.focus();
    }
  };

  const handleKeyDown = (index: number, e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Backspace' && !otpValues[index] && index > 0) {
      // Move to previous input on backspace if current is empty
      otpRefs.current[index - 1]?.focus();
    }
  };

  const handlePaste = (e: ClipboardEvent<HTMLInputElement>) => {
    e.preventDefault();
    const pastedData = e.clipboardData.getData('text').replace(/\D/g, '').slice(0, 6);
    if (!pastedData) return;

    const newOtpValues = [...otpValues];
    pastedData.split('').forEach((char, i) => {
      if (i < 6) newOtpValues[i] = char;
    });
    setOtpValues(newOtpValues);

    // Focus last filled input or the one after
    const nextIndex = Math.min(pastedData.length, 5);
    otpRefs.current[nextIndex]?.focus();
  };

  // Redirect if already authenticated
  // CRITICAL: This must happen AFTER all hook declarations (useState, useRef, useEffect)
  if (user) {
    const destination = user.role === UserRole.STUDENT ? '/student' : '/lecturer';
    return <Navigate to={destination} replace />;
  }

  return (
    <div className="min-h-[80vh] flex items-center justify-center px-4 py-12">
      <div className="max-w-md w-full bg-white rounded-2xl shadow-xl overflow-hidden border border-slate-100">
        {/* TUL Branding Header */}
        <div className="bg-tul-blue p-8 text-white text-center relative overflow-hidden">
          <div className="absolute top-0 right-0 w-32 h-32 bg-white/10 rounded-full -mr-16 -mt-16 blur-2xl"></div>
          <div className="absolute bottom-0 left-0 w-24 h-24 bg-white/5 rounded-full -ml-12 -mb-12 blur-xl"></div>
          
          <div className="relative z-10">
            <div className="bg-white text-tul-blue w-16 h-16 rounded-2xl flex items-center justify-center mx-auto mb-4 shadow-lg">
               <span className="text-2xl font-black">FM</span>
            </div>
            <h1 className="text-2xl font-bold tracking-tight">{t('login.title')}</h1>
            <p className="text-blue-100 mt-1 font-medium">{t('app.title')}</p>
          </div>
        </div>

        <div className="p-8">
          {step === 'email' ? (
            <form onSubmit={handleSendOtp} className="space-y-6">
              <div>
                <label htmlFor="email" className="block text-sm font-semibold text-slate-700 mb-1.5 ml-1">
                  {t('login.email_label')}
                </label>
                <div className="relative group flex">
                  <div className="relative flex-grow">
                    <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none transition-colors group-focus-within:text-tul-blue text-slate-400">
                      <Mail className="h-5 w-5" />
                    </div>
                    <input
                      id="email"
                      type="text"
                      required
                      autoFocus
                      autoComplete="username"
                      disabled={loading}
                      className="block w-full pl-11 pr-3 py-3.5 border border-slate-200 rounded-l-xl leading-5 bg-slate-50 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-tul-blue/20 focus:border-tul-blue focus:bg-white transition-all text-slate-900 text-right disabled:opacity-50"
                      placeholder="jan.novak"
                      value={emailPrefix}
                      onChange={(e) => setEmailPrefix(e.target.value.split('@')[0])}
                    />
                  </div>
                  <div className="flex items-center px-4 bg-slate-100 border border-l-0 border-slate-200 rounded-r-xl text-slate-500 font-bold text-sm">
                    @tul.cz
                  </div>
                </div>
                
                {loading && (
                  <div className="mt-4 flex items-center justify-center gap-3 text-tul-blue font-bold animate-pulse">
                    <RefreshCw className="h-5 w-5 animate-spin" />
                    <span className="text-sm">{t('login.otp_generating')}</span>
                  </div>
                )}

                <p className="mt-2.5 text-sm text-slate-500 flex items-start gap-2 ml-1">
                  <span className="inline-block w-1.5 h-1.5 rounded-full bg-tul-blue/40 mt-1.5 flex-shrink-0"></span>
                  {t('login.email_info')}
                </p>
              </div>

              {error && (
                <div className="text-sm text-red-600 font-medium bg-red-50 p-4 rounded-xl border border-red-100 animate-in fade-in slide-in-from-top-1">
                  {error}
                </div>
              )}

              <Button
                type="submit"
                className="w-full py-7 rounded-xl text-lg font-bold shadow-lg shadow-tul-blue/20 hover:shadow-tul-blue/30 active:scale-[0.98] transition-all"
                disabled={loading || !emailPrefix.trim()}
              >
                {loading ? (
                  <RefreshCw className="h-5 w-5 animate-spin mr-3" />
                ) : null}
                {t('login.send_code')}
              </Button>
            </form>
          ) : (
            <form onSubmit={handleVerifyOtp} className="space-y-6">
              <div>
                <div className="flex justify-between items-end mb-4 ml-1">
                  <label className="block text-sm font-semibold text-slate-700">
                    {t('login.otp_label')}
                  </label>
                  <button
                    type="button"
                    onClick={() => setStep('email')}
                    className="text-sm font-bold text-tul-blue hover:text-tul-blue/80 transition-colors flex items-center gap-1"
                  >
                    <ArrowLeft className="h-3.5 w-3.5" />
                    {t('login.back')}
                  </button>
                </div>
                
                <div className="flex justify-between gap-2">
                  {otpValues.map((value, index) => (
                    <input
                      key={index}
                      ref={(el) => { otpRefs.current[index] = el; }}
                      type="text"
                      inputMode="numeric"
                      maxLength={1}
                      value={value}
                      autoFocus={index === 0}
                      autoComplete={index === 0 ? "one-time-code" : "off"}
                      aria-label={t('login.otp_digit').replace('{index}', (index + 1).toString())}
                      onChange={(e) => handleOtpChange(index, e.target.value)}
                      onKeyDown={(e) => handleKeyDown(index, e)}
                      onPaste={index === 0 ? handlePaste : undefined}
                      className="w-full h-14 text-center text-2xl font-black border border-slate-200 rounded-xl bg-slate-50 focus:outline-none focus:ring-4 focus:ring-tul-blue/10 focus:border-tul-blue focus:bg-white transition-all text-slate-900"
                    />
                  ))}
                </div>

                <p className="mt-6 text-sm text-slate-500 text-center">
                  {t('login.code_sent')}{' '}
                  <span className="font-bold text-slate-800 bg-slate-100 px-2 py-1 rounded-lg">{fullEmail}</span>
                </p>
              </div>

              {error && (
                <div className="text-sm text-red-600 font-medium bg-red-50 p-4 rounded-xl border border-red-100 animate-in fade-in slide-in-from-top-1">
                  {error}
                </div>
              )}

              <div className="space-y-4">
                <Button
                  type="submit"
                  className="w-full py-7 rounded-xl text-lg font-bold shadow-lg shadow-tul-blue/20 hover:shadow-tul-blue/30 active:scale-[0.98] transition-all"
                  disabled={loading || fullOtp.length !== 6}
                >
                  {loading ? (
                    <RefreshCw className="h-5 w-5 animate-spin mr-3" />
                  ) : null}
                  {t('login.verify')}
                </Button>

                <button
                  type="button"
                  onClick={handleResendOtp}
                  disabled={loading}
                  className="w-full text-sm font-bold text-slate-500 hover:text-tul-blue transition-colors py-2"
                >
                  {t('login.resend')}
                </button>
              </div>
            </form>
          )}
        </div>
        
        <div className="p-6 bg-slate-50 border-t border-slate-100 text-center">
           <p className="text-xs text-slate-400 uppercase tracking-widest font-bold">
             Technická univerzita v Liberci
           </p>
        </div>
      </div>
    </div>
  );
};
