import { useEffect, useState, FormEvent } from 'react';
import { PlusCircle, Edit2, Trash2, ToggleLeft, ToggleRight } from 'lucide-react';
import { useLanguage } from '@/contexts/LanguageContext';
import {
  getAnnouncements,
  createAnnouncement,
  updateAnnouncement,
  deleteAnnouncement,
  ApiError,
} from '@/api';
import { AnnouncementPublic, AnnouncementCreate, AnnouncementSeverity } from '@/types';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { ErrorMessage } from '@/components/ui/ErrorMessage';
import { Button } from '@/components/ui/Button';
import { Modal } from '@/components/ui/Modal';

// Maps severity to a Tailwind badge colour class.
const SEVERITY_BADGE: Record<AnnouncementSeverity, string> = {
  [AnnouncementSeverity.INFO]: 'bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300',
  [AnnouncementSeverity.WARNING]: 'bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-300',
  [AnnouncementSeverity.ERROR]: 'bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-300',
};

interface AnnouncementFormState {
  message: string;
  severity: AnnouncementSeverity;
  is_active: boolean;
}

const EMPTY_FORM: AnnouncementFormState = {
  message: '',
  severity: AnnouncementSeverity.INFO,
  is_active: false,
};

export const AnnouncementManagement = () => {
  const { t } = useLanguage();

  const [announcements, setAnnouncements] = useState<AnnouncementPublic[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingAnnouncement, setEditingAnnouncement] = useState<AnnouncementPublic | null>(null);
  const [form, setForm] = useState<AnnouncementFormState>(EMPTY_FORM);
  const [formError, setFormError] = useState<string | null>(null);
  const [formLoading, setFormLoading] = useState(false);

  const [deletingId, setDeletingId] = useState<number | null>(null);
  const [togglingId, setTogglingId] = useState<number | null>(null);

  const loadAnnouncements = async () => {
    setLoading(true);
    setError(null);
    try {
      setAnnouncements(await getAnnouncements());
    } catch (err) {
      setError(err instanceof ApiError ? String(err.detail) : t('common.error_generic'));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadAnnouncements(); }, []);

  const openCreate = () => {
    setEditingAnnouncement(null);
    setForm(EMPTY_FORM);
    setFormError(null);
    setIsModalOpen(true);
  };

  const openEdit = (ann: AnnouncementPublic) => {
    setEditingAnnouncement(ann);
    setForm({ message: ann.message, severity: ann.severity, is_active: ann.is_active });
    setFormError(null);
    setIsModalOpen(true);
  };

  const closeModal = () => {
    setIsModalOpen(false);
    setEditingAnnouncement(null);
    setForm(EMPTY_FORM);
    setFormError(null);
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setFormLoading(true);
    setFormError(null);
    try {
      if (editingAnnouncement) {
        const updated = await updateAnnouncement(editingAnnouncement.id, form);
        setAnnouncements(prev => prev.map(a => (a.id === updated.id ? updated : a)));
      } else {
        const created = await createAnnouncement(form as AnnouncementCreate);
        setAnnouncements(prev => [created, ...prev]);
      }
      closeModal();
    } catch (err) {
      setFormError(err instanceof ApiError ? String(err.detail) : t('common.error_generic'));
    } finally {
      setFormLoading(false);
    }
  };

  const handleToggleActive = async (ann: AnnouncementPublic) => {
    setTogglingId(ann.id);
    try {
      const updated = await updateAnnouncement(ann.id, { is_active: !ann.is_active });
      setAnnouncements(prev => prev.map(a => (a.id === updated.id ? updated : a)));
    } catch (err) {
      setError(err instanceof ApiError ? String(err.detail) : t('common.error_generic'));
    } finally {
      setTogglingId(null);
    }
  };

  const handleDelete = async (id: number) => {
    setDeletingId(id);
    try {
      await deleteAnnouncement(id);
      setAnnouncements(prev => prev.filter(a => a.id !== id));
    } catch (err) {
      setError(err instanceof ApiError ? String(err.detail) : t('common.error_generic'));
    } finally {
      setDeletingId(null);
    }
  };

  if (loading) return <LoadingSpinner />;

  return (
    <div>
      <div className="flex justify-end mb-6">
        <Button onClick={openCreate} className="flex items-center gap-2 rounded-xl">
          <PlusCircle size={16} />
          {t('admin.announcement_create')}
        </Button>
      </div>

      {error && <ErrorMessage message={error} />}

      {/* Announcements list */}
      {announcements.length === 0 ? (
        <div className="text-center py-20 text-slate-400 dark:text-slate-600 text-sm">
          {t('admin.announcements_empty')}
        </div>
      ) : (
        <div className="space-y-3">
          {announcements.map(ann => (
            <div
              key={ann.id}
              className="flex items-start gap-4 bg-white dark:bg-slate-800 rounded-2xl border border-slate-200 dark:border-slate-700 p-4 shadow-sm"
            >
              {/* Status toggle */}
              <button
                onClick={() => handleToggleActive(ann)}
                disabled={togglingId === ann.id}
                aria-label={ann.is_active ? t('admin.announcement_deactivate') : t('admin.announcement_activate')}
                className="mt-0.5 shrink-0 cursor-pointer disabled:opacity-50 transition-opacity"
              >
                {ann.is_active ? (
                  <ToggleRight size={24} className="text-green-500" />
                ) : (
                  <ToggleLeft size={24} className="text-slate-400" />
                )}
              </button>

              {/* Content */}
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <span
                    className={`text-xs font-bold uppercase tracking-widest px-2 py-0.5 rounded-full ${SEVERITY_BADGE[ann.severity]}`}
                  >
                    {t(`enum.${ann.severity}`)}
                  </span>
                  {ann.is_active && (
                    <span className="text-xs font-bold uppercase tracking-widest px-2 py-0.5 rounded-full bg-green-100 text-green-700 dark:bg-green-900/40 dark:text-green-300">
                      {t('admin.announcement_active')}
                    </span>
                  )}
                </div>
                <p className="text-sm text-slate-700 dark:text-slate-300 leading-snug break-words">
                  {ann.message}
                </p>
                <p className="text-xs text-slate-400 dark:text-slate-500 mt-1">
                  {new Date(ann.updated_at).toLocaleString()}
                </p>
              </div>

              {/* Actions */}
              <div className="flex items-center gap-1 shrink-0">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => openEdit(ann)}
                  aria-label={t('common.edit')}
                  className="rounded-xl text-slate-400 hover:text-tul-blue"
                >
                  <Edit2 size={16} />
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => handleDelete(ann.id)}
                  disabled={deletingId === ann.id}
                  aria-label={t('common.delete')}
                  className="rounded-xl text-slate-400 hover:text-red-600 hover:bg-red-50 dark:hover:bg-red-950 disabled:opacity-50"
                >
                  <Trash2 size={16} />
                </Button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Create / Edit modal */}
      <Modal
        isOpen={isModalOpen}
        onClose={closeModal}
        title={editingAnnouncement ? t('admin.announcement_edit') : t('admin.announcement_create')}
        footer={
          <div className="flex gap-3 justify-end">
            <Button variant="outline" onClick={closeModal} className="rounded-xl">
              {t('common.cancel')}
            </Button>
            <Button
              onClick={e => handleSubmit(e as unknown as FormEvent)}
              disabled={formLoading || !form.message.trim()}
              className="rounded-xl"
            >
              {formLoading
                ? t('common.saving')
                : editingAnnouncement
                  ? t('common.save')
                  : t('admin.announcement_create')}
            </Button>
          </div>
        }
      >
        <form onSubmit={handleSubmit} className="space-y-4">
          {formError && <ErrorMessage message={formError} />}

          {/* Message */}
          <div>
            <label
              htmlFor="ann-message"
              className="block text-sm font-bold text-slate-700 dark:text-slate-300 mb-1"
            >
              {t('admin.announcement_message')}
            </label>
            <textarea
              id="ann-message"
              rows={3}
              maxLength={1000}
              required
              value={form.message}
              onChange={e => setForm(prev => ({ ...prev, message: e.target.value }))}
              className="w-full px-3 py-2 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-800 dark:text-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-tul-blue/40 resize-none"
              placeholder={t('admin.announcement_message_placeholder')}
            />
            <p className="text-xs text-slate-400 mt-1 text-right">
              {form.message.length}/1000
            </p>
          </div>

          {/* Severity */}
          <div>
            <label
              htmlFor="ann-severity"
              className="block text-sm font-bold text-slate-700 dark:text-slate-300 mb-1"
            >
              {t('admin.announcement_severity')}
            </label>
            <select
              id="ann-severity"
              value={form.severity}
              onChange={e => setForm(prev => ({ ...prev, severity: e.target.value as AnnouncementSeverity }))}
              className="w-full px-3 py-2 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-800 dark:text-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-tul-blue/40"
            >
              {Object.values(AnnouncementSeverity).map(s => (
                <option key={s} value={s}>{t(`enum.${s}`)}</option>
              ))}
            </select>
          </div>

          {/* Active toggle */}
          <div className="flex items-center gap-3">
            <input
              type="checkbox"
              id="ann-active"
              checked={form.is_active}
              onChange={e => setForm(prev => ({ ...prev, is_active: e.target.checked }))}
              className="w-4 h-4 accent-tul-blue cursor-pointer"
            />
            <label
              htmlFor="ann-active"
              className="text-sm font-medium text-slate-700 dark:text-slate-300 cursor-pointer select-none"
            >
              {t('admin.announcement_set_active')}
            </label>
          </div>
        </form>
      </Modal>
    </div>
  );
};
