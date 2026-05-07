import React, { useState, useEffect, useMemo, Fragment } from 'react';
import { useParams, Link } from 'react-router-dom';
import ReactMarkdown from 'react-markdown';
import { 
  ArrowLeft, 
  BookOpen, 
  Calendar, 
  User, 
  ExternalLink, 
  ListChecks, 
  ArrowRight,
  FolderKanban,
  Star,
  Mail,
  X,
  Plus,
  Settings
} from 'lucide-react';
import { GitHubLogo } from '@/components/icons/GitHubLogo';
import { useLanguage } from '@/contexts/LanguageContext';
import { useAuth } from '@/contexts/AuthContext';
import { getCourse, getProjects, addCourseLecturer, deleteCourseLecturer, updateProject, ApiError } from '@/api';
import { CourseDetail, ProjectPublic, UserRole, ProjectUpdate } from '@/types';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { ErrorMessage } from '@/components/ui/ErrorMessage';
import { Button } from '@/components/ui/Button';
import { Modal } from '@/components/ui/Modal';
import { ProjectForm } from '@/components/admin/ProjectForm';

export const CourseDetailView = () => {
  const { id } = useParams<{ id: string }>();
  const { t } = useLanguage();
  const { user: currentUser } = useAuth();
  
  const [course, setCourse] = useState<CourseDetail | null>(null);
  const [projects, setProjects] = useState<ProjectPublic[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isAddingLecturer, setIsAddingLecturer] = useState(false);
  const [newLecturerEmail, setNewLecturerEmail] = useState('');
  const [lecturerError, setLecturerError] = useState<string | null>(null);

  // Edit Project Modal State
  const [isEditProjectModalOpen, setIsEditProjectModalOpen] = useState(false);
  const [editingProject, setEditingProject] = useState<ProjectPublic | null>(null);
  const [editProjectLoading, setEditProjectLoading] = useState(false);
  const [editProjectError, setEditProjectError] = useState<string | null>(null);

  const fetchCourseData = async () => {
    setLoading(true);
    setError(null);

    const courseId = id ? Number(id) : NaN;

    if (!Number.isInteger(courseId) || courseId <= 0) {
      setCourse(null);
      setError(t('courseDetail.not_found'));
      setLoading(false);
      return;
    }

    try {
      const courseData = await getCourse(courseId);
      setCourse(courseData);
      
      // Fetch projects for this course
      const projectsData = await getProjects({ course: courseData.code });
      setProjects(projectsData);
    } catch (err) {
      setError(t('courseDetail.error_fetching'));
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCourseData();
  }, [id]);

  const canManageLecturers = useMemo(() => {
    if (!currentUser || !course) return false;
    if (currentUser.role === UserRole.ADMIN) return true;
    return course.lecturers.some(l => l.email === currentUser.email);
  }, [currentUser, course]);

  const canEditProject = (project: ProjectPublic): boolean => {
    if (!currentUser) return false;
    const isLecturerOrAdmin = currentUser.role === UserRole.ADMIN ||
      (course?.lecturers.some(l => l.email === currentUser.email) ?? false);
    const isMember = project.members.some(m => m.id === currentUser.id);
    return (isLecturerOrAdmin || isMember) && !project.results_unlocked;
  };

  const handleAddLecturer = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!course || !newLecturerEmail) return;

    setLecturerError(null);
    try {
      const email = newLecturerEmail.includes('@') ? newLecturerEmail : `${newLecturerEmail}@tul.cz`;
      await addCourseLecturer(course.id, { email });
      setNewLecturerEmail('');
      setIsAddingLecturer(false);
      // Refresh course data
      const updatedCourse = await getCourse(course.id);
      setCourse(updatedCourse);
    } catch (err) {
      setLecturerError(t('error.failed_to_add'));
      console.error(err);
    }
  };

  const handleRemoveLecturer = async (lecturerId: number) => {
    if (!course || !window.confirm(t('course.remove_lecturer_confirm'))) return;

    try {
      await deleteCourseLecturer(course.id, lecturerId);
      // Refresh course data
      const updatedCourse = await getCourse(course.id);
      setCourse(updatedCourse);
    } catch (err) {
      console.error(err);
    }
  };

  const handleOpenEditProject = (project: ProjectPublic) => {
    setEditingProject(project);
    setIsEditProjectModalOpen(true);
  };

  const handleUpdateProject = async (data: ProjectUpdate) => {
    if (!editingProject) return;
    setEditProjectLoading(true);
    setEditProjectError(null);
    try {
      await updateProject(editingProject.id, data);
      setIsEditProjectModalOpen(false);
      // Re-fetch projects to reflect the updated title/details.
      const projectsData = await getProjects({ course: course!.code });
      setProjects(projectsData);
    } catch (_err) {
      setEditProjectError(_err instanceof ApiError && typeof _err.detail === 'string' ? _err.detail : t('login.error_unexpected'));
    } finally {
      setEditProjectLoading(false);
    }
  };

  // Sort projects: Year DESC, Title ASC
  const sortedProjects = useMemo(() => {
    return [...projects].sort((a, b) => {
      if (b.academic_year !== a.academic_year) {
        return b.academic_year - a.academic_year;
      }
      return a.title.localeCompare(b.title);
    });
  }, [projects]);

  if (loading) {
    return <div className="max-w-7xl mx-auto px-4 py-12"><LoadingSpinner className="h-64" /></div>;
  }

  if (error || !course) {
    return (
      <div className="max-w-7xl mx-auto px-4 py-12">
        <ErrorMessage message={error || t('courseDetail.not_found')} onRetry={fetchCourseData} retryLabel={t('error.retry')} />
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Back Link */}
      <Link 
        to="/courses" 
        className="inline-flex items-center gap-2 text-sm font-medium text-slate-500 hover:text-fm-orange mb-8 transition-colors"
      >
        <ArrowLeft size={16} />
        {t('courseDetail.back_to_list')}
      </Link>

      {/* Header */}
      <div className="mb-12">
        <div className="flex flex-wrap items-center gap-3 mb-4">
          <span className="px-3 py-1 bg-fm-orange text-white text-sm font-bold rounded uppercase">
            {course.code}
          </span>
          <span className="flex items-center gap-1.5 text-slate-500 font-medium">
            <Calendar size={16} className="text-slate-400" />
            {t(`enum.${course.term}`)}
          </span>
        </div>
        <h1 className="text-4xl font-extrabold text-slate-900 dark:text-slate-100 tracking-tight leading-tight mb-6">
          {course.name}
        </h1>
        
        {/* Lecturers */}
        <div className="flex flex-wrap gap-4 items-start">
          {course.lecturers.map((lecturer, idx) => (
            <div 
              key={idx} 
              className="flex flex-col gap-2 p-4 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-600 rounded-2xl shadow-sm hover:border-fm-orange transition-all relative group/lecturer"
            >
              {canManageLecturers && course.lecturers.length > 1 && (
                <button
                  onClick={() => handleRemoveLecturer(lecturer.id)}
                  className="absolute -top-2 -right-2 p-1 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-600 rounded-full text-slate-400 hover:text-red-500 hover:border-red-200 shadow-sm opacity-0 group-hover/lecturer:opacity-100 transition-all"
                  title={t('common.delete')}
                >
                  <X size={14} />
                </button>
              )}
              <Link 
                to={`/courses?lecturer=${encodeURIComponent(lecturer.name)}`}
                className="flex items-center gap-2 text-slate-700 dark:text-slate-200 hover:text-fm-orange transition-colors group"
              >
                <User size={18} className="text-slate-400 group-hover:text-fm-orange" />
                <span className="font-bold">{lecturer.name}</span>
              </Link>
              <div className="flex flex-col gap-1 text-[11px]">
                {lecturer.github_alias && (
                  <a 
                    href={`https://github.com/${lecturer.github_alias}`} 
                    target="_blank" 
                    rel="noopener noreferrer"
                    className="flex items-center gap-1.5 text-slate-500 hover:text-fm-orange transition-colors font-medium"
                  >
                    <GitHubLogo size={12} />
                    {lecturer.github_alias}
                  </a>
                )}
                {lecturer.email && (
                  <a 
                    href={`mailto:${lecturer.email}`}
                    className="flex items-center gap-1.5 text-slate-500 hover:text-fm-orange transition-colors font-medium"
                  >
                    <Mail size={12} />
                    {lecturer.email}
                  </a>
                )}
              </div>
            </div>
          ))}

          {canManageLecturers && (
            <div className="flex flex-col gap-2">
              {isAddingLecturer ? (
                <form onSubmit={handleAddLecturer} className="flex items-center gap-2 bg-white dark:bg-slate-800 p-2 border border-fm-orange/20 rounded-2xl shadow-sm">
                  <div className="relative">
                    <Mail size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                    <input
                      type="text"
                      autoFocus
                      value={newLecturerEmail.includes('@') ? newLecturerEmail.split('@')[0] : newLecturerEmail}
                      onChange={e => setNewLecturerEmail(e.target.value)}
                      placeholder={t('form.email_placeholder')}
                      className="pl-8 pr-16 py-1.5 bg-slate-50 dark:bg-slate-700 border border-slate-200 dark:border-slate-600 rounded-xl text-xs font-bold text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-fm-orange/20 w-48"
                    />
                    <span className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 font-bold text-[10px] pointer-events-none">@tul.cz</span>
                  </div>
                  <Button type="submit" size="sm" className="px-3 py-1.5 h-auto text-[10px] uppercase tracking-wider font-black">
                    {t('form.add')}
                  </Button>
                  <button 
                    type="button" 
                    onClick={() => setIsAddingLecturer(false)}
                    className="p-1.5 text-slate-400 hover:text-slate-600 transition-colors"
                  >
                    <X size={16} />
                  </button>
                </form>
              ) : (
                <button
                  onClick={() => setIsAddingLecturer(true)}
                  className="flex items-center gap-2 p-4 bg-slate-50 dark:bg-slate-700 border border-dashed border-slate-300 dark:border-slate-600 rounded-2xl text-slate-500 dark:text-slate-400 hover:text-fm-orange hover:border-fm-orange hover:bg-fm-orange/5 transition-all group"
                >
                  <Plus size={18} className="text-slate-400 group-hover:text-fm-orange" />
                  <span className="text-sm font-bold">{t('course.add_lecturer')}</span>
                </button>
              )}
              {lecturerError && <p className="text-[10px] font-bold text-red-500 ml-2">{lecturerError}</p>}
            </div>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-12">
        {/* Main Content */}
        <div className="lg:col-span-2 space-y-12">
          {/* Syllabus */}
          <section>
            <h2 className="text-2xl font-bold text-slate-900 dark:text-slate-100 mb-6 flex items-center gap-3">
              <BookOpen size={24} className="text-fm-orange" />
              {t('courseDetail.syllabus')}
            </h2>
            <div className="prose prose-slate dark:prose-invert max-w-none text-slate-700 dark:text-slate-300 leading-relaxed bg-white dark:bg-slate-800 p-8 rounded-2xl border border-slate-100 dark:border-slate-700 shadow-sm">
              <ReactMarkdown>
                {course.syllabus || t('project.no_description')}
              </ReactMarkdown>
            </div>
          </section>

          {/* Evaluation Criteria */}
          <section>
            <h2 className="text-2xl font-bold text-slate-900 dark:text-slate-100 mb-6 flex items-center gap-3">
              <ListChecks size={24} className="text-fm-orange" />
              {t('courseDetail.evaluation_criteria')}
            </h2>
            <div className="bg-white dark:bg-slate-800 rounded-2xl border border-slate-100 dark:border-slate-700 shadow-sm overflow-hidden">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="bg-slate-50 dark:bg-slate-700 border-b border-slate-100 dark:border-slate-600">
                    <th className="px-6 py-4 text-xs font-bold text-slate-400 uppercase tracking-widest">{t('course.criterion')}</th>
                    <th className="px-6 py-4 text-xs font-bold text-slate-400 uppercase tracking-widest text-right">{t('lecturer.score')}</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-50 dark:divide-slate-700">
                  {course.evaluation_criteria.map((criterion, idx) => (
                    <tr key={idx} className="hover:bg-slate-50/50 dark:hover:bg-slate-700/50 transition-colors">
                      <td className="px-6 py-4">
                        <div className="font-semibold text-slate-800 dark:text-slate-100">{criterion.description}</div>
                      </td>
                      <td className="px-6 py-4 text-right font-mono font-bold text-slate-700 dark:text-slate-200">
                        {criterion.max_score}
                      </td>
                    </tr>
                  ))}
                  
                  {/* Students peer-bonus body */}
                  {course.peer_bonus_budget != null && (
                    <tr className="bg-blue-50/30 dark:bg-blue-900/20">
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-2 font-bold text-blue-800 dark:text-blue-300">
                          <Star size={16} className="text-blue-500 fill-blue-500" />
                          {t('courseDetail.peer_bonus')}
                        </div>
                      </td>
                      <td className="px-6 py-4 text-right font-mono font-bold text-blue-700 dark:text-blue-400">
                        {course.peer_bonus_budget}
                      </td>
                    </tr>
                  )}

                  <tr className="bg-slate-50/50 dark:bg-slate-700/50 font-bold border-t-2 border-slate-100 dark:border-slate-600">
                    <td className="px-6 py-4 text-slate-900 dark:text-slate-100">{t('courseDetail.min_score')}</td>
                    <td className="px-6 py-4 text-right text-fm-orange">{course.min_score} {t('courseDetail.points')}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </section>

          {/* Projects */}
          <section>
            <h2 className="text-2xl font-bold text-slate-900 dark:text-slate-100 mb-6 flex items-center gap-3">
              <FolderKanban size={24} className="text-fm-orange" />
              {t('courseDetail.projects')}
            </h2>
            {sortedProjects.length > 0 ? (
              <div className="space-y-3">
                {sortedProjects.map((project, index) => {
                  const showDivider = index > 0 && project.academic_year !== sortedProjects[index - 1].academic_year;
                  return (
                    <Fragment key={project.id}>
                      {showDivider && (
                        <div className="pt-4 pb-2">
                          <hr className="border-slate-200" />
                        </div>
                      )}
                      <div className="flex items-center p-3 bg-white dark:bg-slate-800 border border-slate-100 dark:border-slate-700 rounded-xl shadow-sm hover:shadow-md hover:border-fm-orange/20 transition-all group gap-4">
                        <Link 
                          to={`/projects/${project.id}`}
                          className="flex items-center justify-between flex-1 gap-4 min-w-0"
                        >
                          <div className="min-w-0 flex-grow">
                            <h4 className="font-bold text-slate-800 dark:text-slate-100 group-hover:text-fm-orange transition-colors truncate">
                              {project.title}
                            </h4>
                            <div className="flex items-center gap-3 mt-0.5">
                              <span className="text-[10px] text-slate-400 font-medium uppercase tracking-wider whitespace-nowrap">
                                {project.academic_year}/{project.academic_year + 1}
                              </span>
                              <span className="text-[11px] text-slate-500 truncate italic">
                                {project.members.map(m => m.name).join(', ')}
                              </span>
                            </div>
                          </div>
                          <ArrowRight size={18} className="text-slate-300 group-hover:text-fm-orange group-hover:translate-x-1 transition-all flex-shrink-0" />
                        </Link>
                        {canEditProject(project) && (
                          <button
                            onClick={() => handleOpenEditProject(project)}
                            className="p-1.5 text-slate-400 hover:text-fm-orange hover:bg-slate-100 dark:hover:bg-slate-700 rounded-lg transition-all flex-shrink-0"
                            title={t('admin.edit_project')}
                          >
                            <Settings size={14} />
                          </button>
                        )}
                      </div>
                    </Fragment>
                  );
                })}
              </div>
            ) : (
              <p className="text-slate-500 dark:text-slate-400 italic px-4 py-8 border border-dashed border-slate-200 dark:border-slate-700 rounded-2xl text-center">
                {t('courseDetail.no_projects')}
              </p>
            )}
          </section>
        </div>

        {/* Sidebar */}
        <div className="space-y-8">
          {/* Course Metadata Summary */}
          <div className="bg-slate-900 text-white rounded-3xl p-8 shadow-xl shadow-slate-200">
            <h3 className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-8">
              {t('project.course_info')}
            </h3>
            <div className="space-y-8">
              <div>
                <p className="text-xs text-slate-500 mb-2 uppercase font-bold tracking-wider">{t('project.type')}</p>
                <p className="text-lg font-bold">{t(`enum.${course.project_type}`)}</p>
              </div>
              <div>
                <p className="text-xs text-slate-500 mb-2 uppercase font-bold tracking-wider">{t('project.term')}</p>
                <p className="text-lg font-bold">{t(`enum.${course.term}`)}</p>
              </div>
              
              {/* Course Links inside the black box */}
              {course.links && course.links.length > 0 && (
                <div className="pt-8 border-t border-slate-800">
                  <p className="text-xs text-slate-500 mb-4 uppercase font-bold tracking-wider">{t('courseDetail.links')}</p>
                  <div className="flex flex-col gap-3">
                    {course.links.map((link, idx) => (
                      <a 
                        key={idx}
                        href={link.url} 
                        target="_blank" 
                        rel="noopener noreferrer"
                        className="flex items-center justify-between p-3 bg-white/5 border border-white/10 rounded-xl text-slate-300 hover:text-white hover:bg-white/10 transition-all group"
                      >
                        <span className="font-medium text-sm">{link.label}</span>
                        <ExternalLink size={14} className="text-slate-500 group-hover:text-white transition-all" />
                      </a>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Edit Project Modal */}
      <Modal
        isOpen={isEditProjectModalOpen}
        onClose={() => setIsEditProjectModalOpen(false)}
        title={t('admin.edit_project')}
        size="xl"
      >
        <ProjectForm
          initialData={editingProject}
          onSubmit={handleUpdateProject}
          isLoading={editProjectLoading}
          error={editProjectError}
        />
      </Modal>
    </div>
  );
};
