import { useState, useEffect } from 'react';
import { X, Info, AlertTriangle, AlertCircle } from 'lucide-react';
import { getActiveAnnouncement } from '@/api';
import { AnnouncementPublic, AnnouncementSeverity } from '@/types';

// localStorage key prefix for dismissed announcements; keyed per announcement ID so
// that a new announcement always appears even if the user dismissed a previous one.
const DISMISSED_KEY_PREFIX = 'announcement-dismissed-';

interface SeverityConfig {
  container: string;
  icon: string;
  closeButton: string;
  Icon: typeof Info;
}

const SEVERITY_CONFIG: Record<AnnouncementSeverity, SeverityConfig> = {
  [AnnouncementSeverity.INFO]: {
    container: 'bg-fm-orange/8 border-b border-fm-orange/20 text-slate-600 dark:bg-fm-orange/10 dark:border-fm-orange/25 dark:text-slate-300',
    icon: 'text-fm-orange/70 dark:text-fm-orange/60',
    closeButton: 'hover:bg-fm-orange/10 text-slate-400 dark:text-slate-500',
    Icon: Info,
  },
  [AnnouncementSeverity.WARNING]: {
    container: 'bg-amber-50/80 border-b border-amber-200 text-slate-600 dark:bg-amber-950/40 dark:border-amber-800 dark:text-slate-300',
    icon: 'text-amber-400 dark:text-amber-500',
    closeButton: 'hover:bg-amber-100/60 text-slate-400 dark:text-slate-500',
    Icon: AlertTriangle,
  },
  [AnnouncementSeverity.ERROR]: {
    container: 'bg-red-50/80 border-b border-red-200 text-slate-600 dark:bg-red-950/40 dark:border-red-800 dark:text-slate-300',
    icon: 'text-red-400 dark:text-red-500',
    closeButton: 'hover:bg-red-100/60 text-slate-400 dark:text-slate-500',
    Icon: AlertCircle,
  },
};

export const AnnouncementBanner = () => {
  const [announcement, setAnnouncement] = useState<AnnouncementPublic | null>(null);
  const [dismissed, setDismissed] = useState(false);

  useEffect(() => {
    let cancelled = false;

    const fetchAnnouncement = async () => {
      try {
        const data = await getActiveAnnouncement();
        if (cancelled) return;
        setAnnouncement(data);

        // Restore dismissal state for this specific announcement.
        if (data) {
          const key = `${DISMISSED_KEY_PREFIX}${data.id}`;
          try {
            setDismissed(localStorage.getItem(key) === 'true');
          } catch {
            setDismissed(false);
          }
        }
      } catch {
        // Silently ignore fetch errors — the banner is non-critical UI.
      }
    };

    fetchAnnouncement();
    return () => { cancelled = true; };
  }, []);

  const handleDismiss = () => {
    if (!announcement) return;
    const key = `${DISMISSED_KEY_PREFIX}${announcement.id}`;
    try {
      localStorage.setItem(key, 'true');
    } catch {
      // Storage unavailable — dismiss only for the current session.
    }
    setDismissed(true);
  };

  if (!announcement || dismissed) return null;

  const config = SEVERITY_CONFIG[announcement.severity];
  // Guard against an unrecognised severity value (e.g. from a stale API response).
  if (!config) return null;
  const { Icon } = config;

  return (
    <div
      role="alert"
      aria-live="polite"
      className={`${config.container} py-1.5 px-4 flex items-center justify-center gap-2`}
    >
      <Icon size={16} className={`shrink-0 ${config.icon}`} aria-hidden />
      <p className="text-xs font-medium text-center leading-snug">{announcement.message}</p>
      <button
        onClick={handleDismiss}
        aria-label="Dismiss announcement"
        className={`ml-auto shrink-0 rounded-lg p-1 transition-colors cursor-pointer ${config.closeButton}`}
      >
        <X size={16} />
      </button>
    </div>
  );
};
