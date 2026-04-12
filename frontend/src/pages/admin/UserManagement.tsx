import { useEffect, useState, useMemo, FormEvent, KeyboardEvent } from 'react';
import { Search, UserPlus, Edit2, Shield, User as UserIcon, CheckCircle, XCircle } from 'lucide-react';
import { useLanguage } from '@/contexts/LanguageContext';
import { getUsers, createUser, updateUser, ApiError } from '@/api';
import { UserPublic, UserRole, UserCreate, AdminUserUpdate } from '@/types';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { ErrorMessage } from '@/components/ui/ErrorMessage';
import { Button } from '@/components/ui/Button';
import { Modal } from '@/components/ui/Modal';

export const UserManagement = () => {
  const { t } = useLanguage();
  const [users, setUsers] = useState<UserPublic[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [search, setSearch] = useState('');
  const [roleFilter, setRoleFilter] = useState<string>('all');
  const [showInactive, setShowInactive] = useState(false);

  // Modal State
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingUser, setEditingUser] = useState<UserPublic | null>(null);
  const [formError, setFormError] = useState<string | null>(null);
  const [formLoading, setFormLoading] = useState(false);

  // Form State
  const [email, setEmail] = useState('');
  const [name, setName] = useState('');
  const [githubAlias, setGithubAlias] = useState('');
  const [role, setRole] = useState<UserRole>(UserRole.STUDENT);
  const [isActive, setIsActive] = useState(true);

  // Helper to normalize name to email format (first.last@tul.cz)
  const normalizeForEmail = (str: string): string => {
    return str
      .normalize('NFD')
      .replace(/[\u0300-\u036f]/g, '') // remove diacritics
      .toLowerCase()
      .replace(/[^a-z0-9]/g, '.') // replace non-alphanumeric with dot
      .replace(/\.+/g, '.') // replace multiple dots with one
      .replace(/^\.|\.$/g, ''); // trim dots from ends
  };

  const handleNameChange = (newName: string) => {
    setName(newName);
    if (!editingUser) {
      const parts = newName.trim().split(/\s+/);
      if (parts.length >= 2) {
        const generatedEmail = `${normalizeForEmail(parts[0])}.${normalizeForEmail(parts[parts.length - 1])}`;
        setEmail(generatedEmail);
      }
    }
  };

  const loadUsers = async () => {
    try {
      setLoading(true);
      const data = await getUsers();
      setUsers(data);
    } catch (err) {
      setError(err instanceof ApiError && typeof err.detail === 'string' ? err.detail : t('dashboard.error_fetching'));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadUsers();
  }, []);

  const filteredUsers = useMemo(() => {
    return users.filter(u => {
      const matchesSearch = u.name.toLowerCase().includes(search.toLowerCase()) || 
                            u.email.toLowerCase().includes(search.toLowerCase());
      const matchesRole = roleFilter === 'all' || u.role === roleFilter;
      const matchesStatus = showInactive || u.is_active;
      return matchesSearch && matchesRole && matchesStatus;
    });
  }, [users, search, roleFilter, showInactive]);

  const openAddModal = () => {
    setEditingUser(null);
    setEmail('');
    setName('');
    setGithubAlias('');
    setRole(UserRole.STUDENT);
    setIsActive(true);
    setFormError(null);
    setIsModalOpen(true);
  };

  const openEditModal = (user: UserPublic) => {
    setEditingUser(user);
    setEmail(user.email);
    setName(user.name);
    setGithubAlias(user.github_alias || '');
    setRole(user.role);
    setIsActive(user.is_active);
    setFormError(null);
    setIsModalOpen(true);
  };

  const handleFormSubmit = async (e?: FormEvent) => {
    e?.preventDefault();
    setFormLoading(true);
    setFormError(null);

    try {
      if (editingUser) {
        const updateData: AdminUserUpdate = {
          name: name.trim() || null,
          github_alias: githubAlias || null,
          role,
          is_active: isActive,
        };
        await updateUser(editingUser.id, updateData);
      } else {
        const createData: UserCreate = {
          email: email.includes('@') ? email : `${email}@tul.cz`,
          name: name.trim() || null,
          github_alias: githubAlias || null,
          role,
          is_active: isActive,
        };
        await createUser(createData);
      }
      setIsModalOpen(false);
      loadUsers();
    } catch (err) {
      setFormError(err instanceof ApiError && typeof err.detail === 'string' ? err.detail : t('login.error_unexpected'));
    } finally {
      setFormLoading(false);
    }
  };

  const handleKeyDown = (e: KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleFormSubmit();
    }
  };

  const toggleUserStatus = async (user: UserPublic) => {
    try {
      await updateUser(user.id, { is_active: !user.is_active });
      loadUsers();
    } catch (err) {
      alert(err instanceof ApiError && typeof err.detail === 'string' ? err.detail : t('login.error_unexpected'));
    }
  };

  if (loading) return <div className="py-20"><LoadingSpinner /></div>;
  if (error) return <div className="max-w-7xl mx-auto px-4 py-12"><ErrorMessage message={error} onRetry={loadUsers} /></div>;

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12 space-y-8 animate-fade-in">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div>
          <h1 className="text-3xl font-black text-slate-900">{t('admin.user_management')}</h1>
          <p className="text-slate-500 font-bold mt-1">
            {users.length} {t('admin.role').toLowerCase()}
          </p>
        </div>
        <Button onClick={openAddModal} className="flex items-center gap-2">
          <UserPlus size={18} />
          {t('admin.add_user')}
        </Button>
      </div>

      {/* Toolbar */}
      <div className="bg-white p-4 rounded-3xl border border-slate-200/60 shadow-sm flex flex-col md:flex-row gap-4 items-center">
        <div className="relative flex-1 w-full">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400 w-5 h-5" />
          <input
            type="text"
            placeholder={t('admin.search_placeholder')}
            value={search}
            onChange={e => setSearch(e.target.value)}
            className="w-full pl-12 pr-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-tul-blue/20 focus:border-tul-blue transition-all font-bold"
          />
        </div>
        
        <select
          value={roleFilter}
          onChange={e => setRoleFilter(e.target.value)}
          className="bg-slate-50 border border-slate-200 rounded-xl px-4 py-2.5 font-bold text-slate-700 focus:outline-none focus:ring-2 focus:ring-tul-blue/20"
        >
          <option value="all">{t('common.all')} {t('admin.role').toLowerCase()}</option>
          <option value={UserRole.ADMIN}>{t('role.admin')}</option>
          <option value={UserRole.LECTURER}>{t('role.lecturer')}</option>
          <option value={UserRole.STUDENT}>{t('role.student')}</option>
        </select>

        <label className="flex items-center gap-3 cursor-pointer select-none px-4 py-2 rounded-xl hover:bg-slate-50 transition-colors">
          <div className="relative">
            <input
              type="checkbox"
              className="sr-only"
              checked={showInactive}
              onChange={e => setShowInactive(e.target.checked)}
            />
            <div className={`w-10 h-6 rounded-full transition-colors ${showInactive ? 'bg-tul-blue' : 'bg-slate-200'}`} />
            <div className={`absolute left-1 top-1 w-4 h-4 rounded-full bg-white transition-transform ${showInactive ? 'translate-x-4' : ''}`} />
          </div>
          <span className="text-sm font-black text-slate-600 uppercase tracking-widest">{t('admin.inactive')}</span>
        </label>
      </div>

      {/* Users Table */}
      <div className="bg-white rounded-3xl border border-slate-200/60 shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left">
            <thead className="bg-slate-50/50 border-b border-slate-100">
              <tr>
                <th className="px-6 py-4 text-[10px] font-black text-slate-400 uppercase tracking-[0.15em]">{t('profile.name')}</th>
                <th className="px-6 py-4 text-[10px] font-black text-slate-400 uppercase tracking-[0.15em]">{t('admin.role')}</th>
                <th className="px-6 py-4 text-[10px] font-black text-slate-400 uppercase tracking-[0.15em]">{t('admin.status')}</th>
                <th className="px-6 py-4 text-[10px] font-black text-slate-400 uppercase tracking-[0.15em] text-right">{t('common.actions')}</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-50">
              {filteredUsers.map(u => (
                <tr key={u.id} className="hover:bg-slate-50/30 transition-colors group">
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-xl bg-slate-100 flex items-center justify-center text-slate-400">
                        <UserIcon size={20} />
                      </div>
                      <div>
                        <div className="font-black text-slate-900 leading-none mb-1">{u.name}</div>
                        <div className="text-xs font-bold text-slate-400">{u.email}</div>
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-lg text-[10px] font-black uppercase tracking-widest ${
                      u.role === UserRole.ADMIN ? 'bg-slate-800 text-white' :
                      u.role === UserRole.LECTURER ? 'bg-tul-blue text-white' :
                      'bg-purple-100 text-purple-600'
                    }`}>
                      <Shield size={10} />
                      {t(`role.${u.role.toLowerCase()}`)}
                    </span>
                  </td>
                  <td className="px-6 py-4">
                    <button
                      onClick={() => toggleUserStatus(u)}
                      className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-lg text-[10px] font-black uppercase tracking-widest transition-colors ${
                        u.is_active ? 'bg-green-50 text-green-600 hover:bg-green-100' : 'bg-red-50 text-red-600 hover:bg-red-100'
                      }`}
                    >
                      {u.is_active ? <CheckCircle size={10} /> : <XCircle size={10} />}
                      {u.is_active ? t('admin.active') : t('admin.inactive')}
                    </button>
                  </td>
                  <td className="px-6 py-4 text-right">
                    <button
                      onClick={() => openEditModal(u)}
                      className="p-2 text-slate-400 hover:text-tul-blue hover:bg-tul-blue/5 rounded-xl transition-all"
                      title={t('admin.edit_user')}
                    >
                      <Edit2 size={18} />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {filteredUsers.length === 0 && (
          <div className="py-20 text-center text-slate-400 font-bold">
            {t('dashboard.no_results')}
          </div>
        )}
      </div>

      {/* User Form Modal */}
      <Modal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title={editingUser ? t('admin.edit_user') : t('admin.add_user')}
        footer={
          <>
            <Button variant="ghost" onClick={() => setIsModalOpen(false)}>{t('common.cancel')}</Button>
            <Button onClick={handleFormSubmit} isLoading={formLoading}>
              {editingUser ? t('common.save') : t('form.add')}
            </Button>
          </>
        }
      >
        <form onSubmit={handleFormSubmit} className="space-y-6">
          <div className="space-y-4">
            <div>
              <label htmlFor="user-name" className="block text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1.5 ml-1">{t('profile.name')}</label>
              <input
                id="user-name"
                type="text"
                autoFocus
                value={name}
                onChange={e => handleNameChange(e.target.value)}
                onKeyDown={handleKeyDown}
                className="w-full bg-slate-50 border border-slate-200 rounded-xl px-4 py-2.5 text-slate-900 focus:outline-none focus:ring-2 focus:ring-tul-blue/20 focus:border-tul-blue font-bold"
              />
            </div>

            <div>
              <label htmlFor="user-email" className="block text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1.5 ml-1">{t('login.email_label')}</label>
              <div className="relative">
                <input
                  id="user-email"
                  type="text"
                  required
                  disabled={!!editingUser}
                  value={email.includes('@') ? email.split('@')[0] : email}
                  onChange={e => setEmail(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder={t('form.email_placeholder')}
                  className="w-full bg-slate-50 border border-slate-200 rounded-xl px-4 py-2.5 text-slate-900 focus:outline-none focus:ring-2 focus:ring-tul-blue/20 focus:border-tul-blue disabled:opacity-50 font-bold"
                />
                {!editingUser && (
                  <span className="absolute right-4 top-1/2 -translate-y-1/2 text-slate-400 font-bold text-sm pointer-events-none">@tul.cz</span>
                )}
              </div>
            </div>

            <div>
              <label htmlFor="user-github" className="block text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1.5 ml-1">{t('profile.github')}</label>
              <input
                id="user-github"
                type="text"
                value={githubAlias}
                onChange={e => setGithubAlias(e.target.value)}
                onKeyDown={handleKeyDown}
                className="w-full bg-slate-50 border border-slate-200 rounded-xl px-4 py-2.5 text-slate-900 focus:outline-none focus:ring-2 focus:ring-tul-blue/20 focus:border-tul-blue font-bold"
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label htmlFor="user-role" className="block text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1.5 ml-1">{t('admin.role')}</label>
                <select
                  id="user-role"
                  value={role}
                  onChange={e => setRole(e.target.value as UserRole)}
                  className="w-full bg-slate-50 border border-slate-200 rounded-xl px-4 py-2.5 text-slate-900 focus:outline-none focus:ring-2 focus:ring-tul-blue/20 font-bold"
                >
                  <option value={UserRole.STUDENT}>{t('role.student')}</option>
                  <option value={UserRole.LECTURER}>{t('role.lecturer')}</option>
                  <option value={UserRole.ADMIN}>{t('role.admin')}</option>
                </select>
              </div>

              <div>
                <label htmlFor="user-status" className="block text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1.5 ml-1">{t('admin.status')}</label>
                <label className="flex items-center gap-3 cursor-pointer select-none bg-slate-50 border border-slate-200 rounded-xl px-4 py-2.5">
                  <div className="relative">
                    <input
                      id="user-status"
                      type="checkbox"
                      className="sr-only"
                      checked={isActive}
                      onChange={e => setIsActive(e.target.checked)}
                    />
                    <div className={`w-10 h-6 rounded-full transition-colors ${isActive ? 'bg-tul-blue' : 'bg-slate-200'}`} />
                    <div className={`absolute left-1 top-1 w-4 h-4 rounded-full bg-white transition-transform ${isActive ? 'translate-x-4' : ''}`} />
                  </div>
                  <span className="text-sm font-black text-slate-600 uppercase tracking-widest">{isActive ? t('admin.active') : t('admin.inactive')}</span>
                </label>
              </div>
            </div>
          </div>
          {formError && <ErrorMessage message={formError} />}
        </form>
      </Modal>
    </div>
  );
};
