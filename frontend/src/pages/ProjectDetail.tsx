import { useState, useEffect, useMemo } from 'react';
import { useParams, Link } from 'react-router-dom';
import ReactMarkdown from 'react-markdown';
import { 
  ArrowLeft, 
  ExternalLink, 
  Users, 
  BookOpen, 
  Calendar, 
  Mail,
  CheckCircle,
  Award,
  Edit2,
  UserPlus,
  X,
  Plus
} from 'lucide-react';
import { GitHubLogo } from '@/components/icons/GitHubLogo';
import { useLanguage } from '@/contexts/LanguageContext';
import { useAuth } from '@/contexts/AuthContext';
import { getProject, updateProject, addProjectMember, deleteProjectMember, ApiError } from '@/api';
import { ProjectPublic, UserRole, ProjectUpdate } from '@/types';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { ErrorMessage } from '@/components/ui/ErrorMessage';
import { Button } from '@/components/ui/Button';
import { Modal } from '@/components/ui/Modal';
import { ProjectForm } from '@/components/admin/ProjectForm';
import { CourseEvaluationStatusCard } from '@/components/student/CourseEvaluationStatusCard';

export const ProjectDetail = () => {
  const { id } = useParams<{ id: string }>();
  const { t } = useLanguage();
  const { user } = useAuth();
  const [project, setProject] = useState<ProjectPublic | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Edit Project State
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [editLoading, setEditLoading] = useState(false);
  const [editError, setEditError] = useState<string | null>(null);

  // Add Member State
  const [isAddMemberModalOpen, setIsAddMemberModalOpen] = useState(false);
  const [memberEmail, setMemberEmail] = useState('');
  const [memberLoading, setMemberLoading] = useState(false);
  const [memberError, setMemberError] = useState<string | null>(null);

  const fetchProject = async () => {
    setLoading(true);
    setError(null);

    const projectId = id ? Number(id) : NaN;

    if (!Number.isInteger(projectId) || projectId <= 0) {
      setProject(null);
      setError(t('projectDetail.not_found'));
      setLoading(false);
      return;
    }

    try {
      const data = await getProject(projectId);
      setProject(data);
    } catch (err) {
      setError(t('projectDetail.error_fetching'));
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProject();
  }, [id]);

  const handleUpdateProject = async (data: ProjectUpdate) => {
    if (!project) return;
    setEditLoading(true);
    setEditError(null);
    try {
      const updated = await updateProject(project.id, data);
      setProject(updated);
      setIsEditModalOpen(false);
    } catch (err) {
      setEditError(err instanceof ApiError && typeof err.detail === 'string' ? err.detail : t('login.error_unexpected'));
    } finally {
      setEditLoading(false);
    }
  };

  const handleAddMember = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!project || !memberEmail) return;
    setMemberLoading(true);
    setMemberError(null);
    try {
      const email = memberEmail.includes('@') ? memberEmail : `${memberEmail}@tul.cz`;
      await addProjectMember(project.id, { email });
      await fetchProject();
      setIsAddMemberModalOpen(false);
      setMemberEmail('');
    } catch (err) {
      setMemberError(err instanceof ApiError && typeof err.detail === 'string' ? err.detail : t('login.error_unexpected'));
    } finally {
      setMemberLoading(false);
    }
  };

  const handleDeleteMember = async (userId: number) => {
    if (!project || !window.confirm(t('common.confirm_action'))) return;
    try {
      await deleteProjectMember(project.id, userId);
      await fetchProject();
    } catch (err) {
      console.error(err);
      alert(t('login.error_unexpected'));
    }
  };

  const isMember = user && project?.members.some(m => m.id === user.id);
  const isOwningLecturer = user && project?.course.lecturers.some(l => l.id === user.id);
  const showLecturerControls = user && (user.role === UserRole.ADMIN || (user.role === UserRole.LECTURER && isOwningLecturer));
  const canEdit = showLecturerControls && !project?.results_unlocked;

  if (loading) {
    return <div className="max-w-7xl mx-auto px-4 py-12"><LoadingSpinner className="h-64" /></div>;
  }

  if (error || !project) {
    return (
      <div className="max-w-7xl mx-auto px-4 py-12">
        <ErrorMessage message={error || t('projectDetail.not_found')} onRetry={fetchProject} retryLabel={t('error.retry')} />
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Back Link */}
      <Link 
        to="/" 
        className="inline-flex items-center gap-2 text-sm font-medium text-slate-500 hover:text-tul-blue mb-8 transition-colors"
      >
        <ArrowLeft size={16} />
        {t('project.back_to_projects')}
      </Link>

      {/* Header */}
      <div className="mb-10">
        <div className="flex flex-wrap items-center gap-3 mb-4">
          <Link 
            to={`/courses/${project.course.id}`}
            className="px-3 py-1 bg-tul-blue text-white text-sm font-bold rounded uppercase hover:bg-blue-700 transition-colors"
          >
            {project.course.code}
          </Link>
          <Link 
            to={`/courses/${project.course.id}`}
            className="text-slate-500 font-medium hover:text-tul-blue transition-colors"
          >
            {project.course.name}
          </Link>
          <span className="h-4 w-px bg-slate-200 mx-1"></span>
          <span className="flex items-center gap-1.5 text-slate-500 font-medium">
            <Calendar size={16} className="text-slate-400" />
            {project.academic_year}/{project.academic_year + 1}
          </span>
        </div>
        <h1 className="text-4xl font-extrabold text-slate-900 tracking-tight leading-tight">
          {project.title}
        </h1>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-12">
        {/* Main Content */}
        <div className="lg:col-span-2 space-y-10">
          {/* Description */}
          <section>
            <h2 className="text-xl font-bold text-slate-900 mb-4 flex items-center gap-2">
              <BookOpen size={20} className="text-tul-blue" />
              {t('form.full_desc')}
            </h2>
            <div className="prose prose-slate max-w-none text-slate-700 leading-relaxed">
              {project.description ? (
                <ReactMarkdown>{project.description}</ReactMarkdown>
              ) : (
                <p className="italic text-slate-400">{t('project.no_description')}</p>
              )}
            </div>
          </section>

          {/* Technologies */}
          <section>
            <h2 className="text-xl font-bold text-slate-900 mb-4 flex items-center gap-2">
              <Award size={20} className="text-tul-blue" />
              {t('project.technologies')}
            </h2>
            <div className="flex flex-wrap gap-2">
              {project.technologies.map((tech, idx) => (
                <span 
                  key={idx} 
                  className="px-3 py-1.5 bg-slate-100 text-slate-700 text-sm font-semibold rounded-lg border border-slate-200 uppercase tracking-wider"
                >
                  {tech}
                </span>
              ))}
            </div>
          </section>

          {/* External Links */}
          {(project.github_url || project.live_url) && (
            <section className="pt-6 border-t border-slate-100">
              <div className="flex flex-wrap gap-4">
                {project.github_url && (
                  <a href={project.github_url} target="_blank" rel="noopener noreferrer">
                    <Button variant="outline" className="gap-2">
                      <GitHubLogo size={20} />
                      {t('project.source_code')}
                    </Button>
                  </a>
                )}
                {project.live_url && (
                  <a href={project.live_url} target="_blank" rel="noopener noreferrer">
                    <Button variant="primary" className="gap-2">
                      <ExternalLink size={20} />
                      {t('project.live_demo')}
                    </Button>
                  </a>
                )}
              </div>
            </section>
          )}
        </div>

        {/* Sidebar */}
        <div className="space-y-8">
          {/* Team Members */}
          <div className="bg-white rounded-2xl shadow-sm border border-slate-100 p-6">
            <h2 className="text-lg font-bold text-slate-900 mb-4 flex items-center gap-2">
              <Users size={20} className="text-tul-blue" />
              {t('project.members')}
            </h2>
            <ul className="space-y-4">
              {project.members.map(member => (
                <li key={member.id} className="flex flex-col gap-1 relative group/member">
                  {canEdit && (
                    <button
                      onClick={() => handleDeleteMember(member.id)}
                      className="absolute -top-1 -right-1 p-1 bg-white border border-slate-200 rounded-full text-slate-400 hover:text-red-500 hover:border-red-200 shadow-sm opacity-0 group-hover/member:opacity-100 transition-all"
                      title={t('common.delete')}
                    >
                      <X size={12} />
                    </button>
                  )}
                  <span className="font-semibold text-slate-800">{member.name}</span>
                  <div className="flex items-center gap-3 text-xs text-slate-500">
                    {member.github_alias && (
                      <a 
                        href={`https://github.com/${member.github_alias}`} 
                        target="_blank" 
                        rel="noopener noreferrer"
                        className="flex items-center gap-1 hover:text-tul-blue transition-colors"
                      >
                        <GitHubLogo size={12} />
                        {member.github_alias}
                      </a>
                    )}
                    {member.email && (
                      <a 
                        href={`mailto:${member.email}`}
                        className="flex items-center gap-1 hover:text-tul-blue transition-colors"
                      >
                        <Mail size={12} />
                        {member.email}
                      </a>
                    )}
                  </div>
                </li>
              ))}
            </ul>
          </div>

          {/* Course Info */}
          <div className="bg-slate-50 rounded-2xl border border-slate-100 p-6">
            <h2 className="text-lg font-bold text-slate-900 mb-4">
              {t('project.course_info')}
            </h2>
            <div className="space-y-3 text-sm">
              <div className="flex justify-between">
                <span className="text-slate-500">{t('project.term')}</span>
                <span className="font-medium text-slate-700">{project.course.term}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">{t('project.type')}</span>
                <span className="font-medium text-slate-700">{project.course.project_type}</span>
              </div>
              <div className="pt-3 mt-3 border-t border-slate-200">
                <p className="text-xs text-slate-400 uppercase font-bold mb-2 tracking-widest">
                  {t('role.lecturer')}
                </p>
                <div className="flex flex-col gap-3">
                  {project.course.lecturers.map((l, i) => (
                    <div key={i} className="flex flex-col gap-1">
                      <Link 
                        to={`/courses?lecturer=${encodeURIComponent(l.name)}`}
                        className="font-bold text-slate-700 hover:text-tul-blue transition-colors"
                      >
                        {l.name}
                      </Link>
                      <div className="flex items-center gap-3 text-xs text-slate-500">
                        {l.github_alias && (
                          <a 
                            href={`https://github.com/${l.github_alias}`} 
                            target="_blank" 
                            rel="noopener noreferrer"
                            className="flex items-center gap-1 hover:text-tul-blue transition-colors"
                          >
                            <GitHubLogo size={10} />
                            {l.github_alias}
                          </a>
                        )}
                        {l.email && (
                          <a 
                            href={`mailto:${l.email}`}
                            className="flex items-center gap-1 hover:text-tul-blue transition-colors"
                          >
                            <Mail size={10} />
                            {l.email}
                          </a>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>

          {/* Role-based Action Links */}
          {(isMember || showLecturerControls) && (
            <div className="space-y-6">
              <p className="text-xs text-slate-400 uppercase font-bold px-2 tracking-widest border-b border-slate-100 pb-2">
                {showLecturerControls ? t('project.lecturer_links') : t('project.student_links')}
              </p>
              
              {isMember && (
                <div className="space-y-4">
                  <div className="bg-white rounded-2xl border border-slate-100 p-4 shadow-sm">
                    <CourseEvaluationStatusCard 
                      project={project}
                      user={user}
                    />
                  </div>
                </div>
              )}

              {showLecturerControls && (
                <div className="flex flex-col gap-3">
                  {canEdit && (
                    <>
                      <Button 
                        variant="outline" 
                        className="w-full justify-start gap-3"
                        onClick={() => setIsEditModalOpen(true)}
                      >
                        <Edit2 size={18} className="text-tul-blue" />
                        {t('admin.update_project')}
                      </Button>
                      <Button 
                        variant="outline" 
                        className="w-full justify-start gap-3"
                        onClick={() => setIsAddMemberModalOpen(true)}
                      >
                        <UserPlus size={18} className="text-tul-blue" />
                        {t('lecturer.add_member')}
                      </Button>
                    </>
                  )}
                  <Link to={`/lecturer/project/${project.id}/evaluate`} className="block">
                    <Button variant="outline" className="w-full justify-start gap-3">
                      <CheckCircle size={18} className="text-tul-blue" />
                      {t('project.evaluate')}
                    </Button>
                  </Link>
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Modals */}
      <Modal
        isOpen={isEditModalOpen}
        onClose={() => setIsEditModalOpen(false)}
        title={t('admin.edit_project')}
        size="xl"
      >
        <ProjectForm
          initialData={project}
          onSubmit={handleUpdateProject}
          isLoading={editLoading}
          error={editError}
        />
      </Modal>

      <Modal
        isOpen={isAddMemberModalOpen}
        onClose={() => setIsAddMemberModalOpen(false)}
        title={t('lecturer.add_member')}
      >
        <form onSubmit={handleAddMember} className="space-y-6">
          <div>
            <label htmlFor="member-email" className="block text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1.5 ml-1">
              {t('login.email_label')}
            </label>
            <div className="relative">
              <input
                id="member-email"
                type="text"
                autoFocus
                required
                value={memberEmail}
                onChange={e => setMemberEmail(e.target.value.split('@')[0])}
                placeholder={t('form.email_placeholder')}
                className="w-full bg-slate-50 border border-slate-200 rounded-xl px-4 py-2.5 text-slate-900 focus:outline-none focus:ring-2 focus:ring-tul-blue/20 font-bold"
              />
              <span className="absolute right-4 top-1/2 -translate-y-1/2 text-slate-400 font-bold text-sm pointer-events-none">@tul.cz</span>
            </div>
          </div>
          {memberError && <ErrorMessage message={memberError} />}
          <div className="flex justify-end gap-3 pt-4 border-t border-slate-100">
            <Button variant="ghost" type="button" onClick={() => setIsAddMemberModalOpen(false)}>
              {t('common.cancel')}
            </Button>
            <Button type="submit" isLoading={memberLoading}>
              {t('form.add')}
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
};
