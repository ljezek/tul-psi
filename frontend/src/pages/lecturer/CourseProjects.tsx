import { useEffect, useState, FormEvent, useMemo } from 'react';
import { useParams, Link } from 'react-router';
import { ArrowLeft, Plus, LockOpen, CheckCircle, Clock, AlertCircle, Users, ExternalLink, BookOpen, ListChecks, UserPlus, Settings, Lock, Trash2, X } from 'lucide-react';
import { useLanguage } from '@/contexts/LanguageContext';
import { useAuth } from '@/contexts/AuthContext';
import { getCourse, getProjects, createCourseProject, addProjectMember, unlockProject, lockProject, addCourseLecturer, updateCourse, ApiError, deleteProject, deleteProjectMember } from '@/api';
import { CourseDetail, ProjectPublic, UserRole, CourseUpdate } from '@/types';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { ErrorMessage } from '@/components/ui/ErrorMessage';
import { Modal } from '@/components/ui/Modal';
import { CourseForm } from '@/components/admin/CourseForm';
import { Button } from '@/components/ui/Button';

export const CourseProjects = () => {
  const { id } = useParams<{ id: string }>();
  const { t } = useLanguage();
  const { user } = useAuth();
  
  const [course, setCourse] = useState<CourseDetail | null>(null);
  const [projects, setProjects] = useState<ProjectPublic[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [yearFilter, setYearFilter] = useState<string>('all');
  
  // Add Project Form State
  const [showAddForm, setShowAddForm] = useState(false);
  const [addTitle, setAddTitle] = useState('');
  const [addYear, setAddYear] = useState(new Date().getFullYear());
  const [addOwnerEmail, setAddOwnerEmail] = useState('');
  const [addError, setAddError] = useState<string | null>(null);

  // Add Lecturer Form State
  const [showAddLecturerForm, setShowAddLecturerForm] = useState(false);
  const [lecturerEmail, setLecturerEmail] = useState('');
  const [lecturerError, setLecturerError] = useState<string | null>(null);

  // Add Member State
  const [addingMemberTo, setAddingMemberTo] = useState<number | null>(null);
  const [memberEmail, setMemberEmail] = useState('');
  const [memberError, setMemberError] = useState<string | null>(null);

  // Edit Course State
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [editLoading, setEditLoading] = useState(false);
  const [editError, setEditError] = useState<string | null>(null);
  
  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      const courseId = parseInt(id as string, 10);
      const courseData = await getCourse(courseId);
      setCourse(courseData);
      
      const projectsData = await getProjects({ course: courseData.code });
      setProjects(projectsData);
    } catch (err) {
      if (err instanceof ApiError && typeof err.detail === 'string') {
        setError(err.detail);
      } else {
        setError(t('courseDetail.error_fetching'));
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (id) {
      loadData();
    }
  }, [id]);

  const handleCreateProject = async (e: FormEvent) => {
    e.preventDefault();
    setAddError(null);
    try {
      if (!course) return;
      await createCourseProject(course.id, {
        title: addTitle,
        academic_year: addYear,
        owner_email: addOwnerEmail ? `${addOwnerEmail}@tul.cz` : undefined,
        technologies: [],
      });
      setShowAddForm(false);
      setAddTitle('');
      setAddOwnerEmail('');
      await loadData();
    } catch (err) {
      if (err instanceof ApiError && typeof err.detail === 'string') {
        setAddError(err.detail);
      } else {
        setAddError(t('login.error_unexpected'));
      }
    }
  };

  const handleAddLecturer = async (e: FormEvent) => {
    e.preventDefault();
    setLecturerError(null);
    try {
      if (!course) return;
      const email = lecturerEmail.includes('@') ? lecturerEmail : `${lecturerEmail}@tul.cz`;
      await addCourseLecturer(course.id, { email });
      setShowAddLecturerForm(false);
      setLecturerEmail('');
      await loadData();
    } catch (err) {
      const msg = err instanceof ApiError && typeof err.detail === 'string' ? err.detail : t('login.error_unexpected');
      setLecturerError(msg);
    }
  };

  const handleAddMember = async (e: FormEvent, projectId: number) => {
    e.preventDefault();
    setMemberError(null);
    try {
      const email = memberEmail.includes('@') ? memberEmail : `${memberEmail}@tul.cz`;
      await addProjectMember(projectId, { email });
      setAddingMemberTo(null);
      setMemberEmail('');
      await loadData();
    } catch (err) {
      const msg = err instanceof ApiError && typeof err.detail === 'string' ? err.detail : t('login.error_unexpected');
      setMemberError(msg);
    }
  };

  const handleUnlockResults = async (projectId: number) => {
    if (!window.confirm(t('common.confirm_action'))) return;
    try {
      await unlockProject(projectId);
      await loadData();
    } catch (err) {
      const msg = err instanceof ApiError && typeof err.detail === 'string' ? err.detail : t('login.error_unexpected');
      alert(msg);
    }
  };

  const handleRelockResults = async (projectId: number) => {
    if (!window.confirm(t('admin.confirm_relock'))) return;
    try {
      await lockProject(projectId);
      await loadData();
    } catch (err) {
      const msg = err instanceof ApiError && typeof err.detail === 'string' ? err.detail : t('login.error_unexpected');
      alert(msg);
    }
  };

  const handleDeleteProject = async (projectId: number) => {
    if (!window.confirm(t('common.confirm_action'))) return;
    try {
      await deleteProject(projectId);
      await loadData();
    } catch (err) {
      const msg = err instanceof ApiError && typeof err.detail === 'string' ? err.detail : t('login.error_unexpected');
      alert(msg);
    }
  };

  const handleDeleteMember = async (projectId: number, userId: number) => {
    if (!window.confirm(t('common.confirm_action'))) return;
    try {
      await deleteProjectMember(projectId, userId);
      await loadData();
    } catch (err) {
      const msg = err instanceof ApiError && typeof err.detail === 'string' ? err.detail : t('login.error_unexpected');
      alert(msg);
    }
  };

  const handleUpdateCourse = async (data: CourseUpdate) => {
    if (!course) return;
    setEditLoading(true);
    setEditError(null);
    try {
      await updateCourse(course.id, data);
      setIsEditModalOpen(false);
      await loadData();
    } catch (err) {
      setEditError(err instanceof ApiError && typeof err.detail === 'string' ? err.detail : t('login.error_unexpected'));
    } finally {
      setEditLoading(false);
    }
  };

  const sortedProjects = useMemo(() => {
    return [...projects].sort((a, b) => {
      if (a.academic_year !== b.academic_year) {
        return b.academic_year - a.academic_year;
      }
      return a.title.localeCompare(b.title);
    });
  }, [projects]);

  const isCourseOwner = useMemo(() => {
    if (!user || !course) return false;
    return course.lecturers.some(l => l.email === user.email);
  }, [user, course]);

  const canSeeEvaluations = isCourseOwner; // Admins only see if they are lecturers too

  const availableYears = useMemo(() => 
    Array.from(new Set(projects.map(p => p.academic_year))).sort((a, b) => b - a),
    [projects]
  );

  const filteredProjects = useMemo(() => {
    if (yearFilter === 'all') return sortedProjects;
    return sortedProjects.filter(p => p.academic_year === parseInt(yearFilter, 10));
  }, [sortedProjects, yearFilter]);

  if (loading) return <div className="py-20"><LoadingSpinner /></div>;
  if (error || !course) return <div className="max-w-7xl mx-auto px-4 py-12"><ErrorMessage message={error || t('courseDetail.not_found')} onRetry={loadData} /></div>;

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12 space-y-8 animate-fade-in">
      {/* Back link */}
      <div>
        <Link to="/lecturer" className="inline-flex items-center text-sm font-bold text-slate-400 hover:text-slate-900 transition-colors">
          <ArrowLeft className="w-4 h-4 mr-2" />
          {t('nav.lecturer_panel')}
        </Link>
      </div>

      {/* Course Header */}
      <div className="bg-white rounded-3xl p-8 border border-slate-200/60 shadow-sm space-y-8">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div>
            <Link 
              to={`/courses/${course.id}`}
              className="inline-block bg-tul-blue text-white px-3 py-1 rounded text-xs font-black uppercase tracking-widest hover:bg-blue-700 transition-colors mb-3"
            >
              {course.code}
            </Link>
            <h1 className="text-3xl font-black text-slate-900">{course.name}</h1>
            <div className="flex flex-wrap gap-4 mt-2 text-slate-500 font-bold text-sm">
              <span>{t(`enum.${course.term}`)}</span>
              <span className="text-slate-300">&bull;</span>
              <span>{t(`enum.${course.project_type}`)}</span>
              <span className="text-slate-300">&bull;</span>
              <span>{course.lecturers.map(l => l.name).join(', ')}</span>
            </div>
          </div>
          <div className="flex flex-wrap gap-3">
            <Button
              variant="outline"
              onClick={() => setIsEditModalOpen(true)}
              className="flex items-center gap-2"
            >
              <Settings className="w-4 h-4" />
              {t('admin.edit_course')}
            </Button>
            <button
              onClick={() => setShowAddLecturerForm(!showAddLecturerForm)}
              className="inline-flex items-center px-5 py-2.5 bg-white hover:bg-slate-50 text-slate-700 border border-slate-200 rounded-xl transition-colors font-black text-sm shadow-sm"
            >
              <UserPlus className="w-4 h-4 mr-2 text-slate-400" />
              {t('courseDetail.lecturers')}
            </button>
            <button
              onClick={() => setShowAddForm(!showAddForm)}
              className="inline-flex items-center px-5 py-2.5 bg-tul-blue hover:bg-tul-blue/90 text-white rounded-xl transition-colors font-black text-sm shadow-sm"
            >
              <Plus className="w-4 h-4 mr-2" />
              {t('lecturer.add_project')}
            </button>
          </div>
        </div>

        {/* Add Lecturer Form */}
        {showAddLecturerForm && (
          <div className="bg-slate-50 p-6 rounded-2xl border border-slate-200 mt-6 animate-in slide-in-from-top-4">
            <h2 className="text-lg font-black text-slate-800 mb-4">{t('courseDetail.lecturers')}</h2>
            <form onSubmit={handleAddLecturer} className="flex items-end gap-4">
              <div className="flex-1 max-w-md">
                <label className="block text-xs font-bold text-slate-500 uppercase tracking-widest mb-2">{t('login.email_label')}</label>
                <div className="relative">
                  <input
                    type="text"
                    required
                    value={lecturerEmail}
                    onChange={e => setLecturerEmail(e.target.value.split('@')[0])}
                    placeholder={t('form.email_placeholder')}
                    aria-label={t('login.email_label')}
                    className="w-full bg-white border border-slate-200 rounded-xl px-4 py-2 text-slate-900 focus:outline-none focus:ring-2 focus:ring-tul-blue/20 focus:border-tul-blue"
                  />
                  <span className="absolute right-4 top-1/2 -translate-y-1/2 text-slate-400 font-bold text-sm pointer-events-none">@tul.cz</span>
                </div>
              </div>
              <button type="submit" className="bg-slate-800 hover:bg-slate-900 text-white px-6 py-2.5 rounded-xl text-sm font-black transition-colors shadow-sm h-[42px]">
                {t('form.add')}
              </button>
              <button type="button" onClick={() => { setShowAddLecturerForm(false); setLecturerError(null); }} className="px-4 py-2.5 rounded-xl text-sm font-black transition-colors text-slate-500 hover:bg-slate-100 h-[42px]">
                {t('lecturer.cancel')}
              </button>
            </form>
            {lecturerError && <p className="text-red-500 text-xs font-bold mt-2 ml-1">{lecturerError}</p>}
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 pt-8 border-t border-slate-100">
          <div className="space-y-4">
            <h3 className="text-sm font-black text-slate-900 uppercase tracking-widest flex items-center gap-2">
              <BookOpen size={16} className="text-tul-blue" />
              {t('courseDetail.syllabus')}
            </h3>
            <p className="text-sm text-slate-600 leading-relaxed line-clamp-4">{course.syllabus}</p>
            
            {course.links.length > 0 && (
              <div className="pt-2">
                <h4 className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-2">{t('courseDetail.links')}</h4>
                <div className="flex flex-wrap gap-3">
                  {course.links.map((link, i) => (
                    <a key={i} href={link.url} target="_blank" rel="noopener noreferrer" className="text-xs font-bold text-tul-blue hover:underline flex items-center gap-1">
                      <ExternalLink size={12} />
                      {link.label}
                    </a>
                  ))}
                </div>
              </div>
            )}
          </div>

          <div className="space-y-4">
            <h3 className="text-sm font-black text-slate-900 uppercase tracking-widest flex items-center gap-2">
              <ListChecks size={16} className="text-tul-blue" />
              {t('courseDetail.evaluation_criteria')}
            </h3>
            <div className="grid grid-cols-2 gap-4">
              {course.evaluation_criteria.map(c => (
                <div key={c.code} className="bg-slate-50 p-3 rounded-xl border border-slate-100">
                  <div className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1 leading-tight">{c.description}</div>
                  <div className="text-sm font-black text-slate-700">{c.max_score} {t('label.points')}</div>
                </div>
              ))}
              <div className="bg-tul-blue/[0.03] p-3 rounded-xl border border-tul-blue/10">
                <div className="text-[10px] font-black text-tul-blue/60 uppercase tracking-widest mb-1">{t('courseDetail.min_score')}</div>
                <div className="text-sm font-black text-tul-blue">{course.min_score} {t('label.points')}</div>
              </div>
              {course.peer_bonus_budget !== null && (
                <div className="bg-purple-50 p-3 rounded-xl border border-purple-100">
                  <div className="text-[10px] font-black text-purple-400 uppercase tracking-widest mb-1">{t('courseDetail.peer_bonus')}</div>
                  <div className="text-sm font-black text-purple-600">±{course.peer_bonus_budget} {t('label.points')}</div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Toolbar */}
      <div className="flex items-center gap-2 bg-white rounded-xl p-1 border border-slate-200/60 shadow-sm w-fit">
        <select
          className="bg-transparent text-slate-700 font-bold px-3 py-1.5 focus:outline-none cursor-pointer"
          value={yearFilter}
          onChange={(e) => setYearFilter(e.target.value)}
        >
          <option value="all">{t('dashboard.all_years')}</option>
          {availableYears.map(y => (
            <option key={y} value={y}>{y}</option>
          ))}
        </select>
      </div>

      {/* Add Project Form */}
      {showAddForm && (
        <div className="bg-tul-blue/[0.02] p-8 rounded-3xl border border-tul-blue/20 shadow-sm">
          <h2 className="text-2xl font-black text-slate-800 mb-6">{t('lecturer.add_project')}</h2>
          <form onSubmit={handleCreateProject} className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              <div>
                <label className="block text-xs font-bold text-slate-500 uppercase tracking-widest mb-2">{t('lecturer.project_title')}</label>
                <input
                  type="text"
                  required
                  value={addTitle}
                  onChange={e => setAddTitle(e.target.value)}
                  className="w-full bg-white border border-slate-200 rounded-xl px-4 py-2.5 text-slate-900 focus:outline-none focus:ring-2 focus:ring-tul-blue/20 focus:border-tul-blue"
                />
              </div>
              <div>
                <label className="block text-xs font-bold text-slate-500 uppercase tracking-widest mb-2">{t('dashboard.filter_year')}</label>
                <input
                  type="number"
                  required
                  value={addYear}
                  onChange={e => setAddYear(parseInt(e.target.value, 10))}
                  className="w-full bg-white border border-slate-200 rounded-xl px-4 py-2.5 text-slate-900 focus:outline-none focus:ring-2 focus:ring-tul-blue/20 focus:border-tul-blue"
                />
              </div>
              <div>
                <label className="block text-xs font-bold text-slate-500 uppercase tracking-widest mb-2">{t('lecturer.owner_email')}</label>
                <div className="relative">
                  <input
                    type="text"
                    value={addOwnerEmail}
                    onChange={e => setAddOwnerEmail(e.target.value.split('@')[0])}
                    placeholder={t('form.email_placeholder')}
                    className="w-full bg-white border border-slate-200 rounded-xl px-4 py-2.5 pr-20 text-slate-900 focus:outline-none focus:ring-2 focus:ring-tul-blue/20 focus:border-tul-blue"
                  />
                  <span className="absolute right-4 top-1/2 -translate-y-1/2 text-slate-400 font-bold text-sm pointer-events-none">@tul.cz</span>
                </div>
              </div>
            </div>
            {addError && <p className="text-red-500 text-sm font-bold">{addError}</p>}
            <div className="flex justify-end gap-3">
              <button type="button" onClick={() => setShowAddForm(false)} className="px-6 py-2.5 rounded-xl text-sm font-black transition-colors text-slate-500 hover:bg-slate-100">
                {t('lecturer.cancel')}
              </button>
              <button type="submit" className="bg-tul-blue hover:bg-tul-blue/90 text-white px-6 py-2.5 rounded-xl text-sm font-black transition-colors shadow-sm">
                {t('lecturer.add_project')}
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Projects List */}
      <div className="space-y-12">
        {filteredProjects.length === 0 ? (
          <div className="text-slate-400 font-medium text-center py-12 bg-white rounded-3xl border border-slate-100">{t('dashboard.no_results')}</div>
        ) : (
          filteredProjects.map((project, index) => {
            const userEval = project.project_evaluations?.find(ev => user && ev.lecturer_id === user.id);
            const showYearSeparator = index === 0 || project.academic_year !== filteredProjects[index - 1].academic_year;
            
            // Calculate stats for unlocked projects
            let criteriaAverages: { code: string; avg: number; max_score: number }[] = [];
            let totalLecturerAvg = 0;
            if (project.results_unlocked) {
              const evaluations = project.project_evaluations || [];
              criteriaAverages = course.evaluation_criteria.map(criterion => {
                const scores = evaluations.map(e => e.scores.find(s => s.criterion_code === criterion.code)?.score || 0);
                const avg = scores.length > 0 ? scores.reduce((a, b) => a + b, 0) / scores.length : 0;
                return { code: criterion.code, avg, max_score: criterion.max_score };
              });
              totalLecturerAvg = criteriaAverages.reduce((sum, c) => sum + c.avg, 0);
            }

            return (
              <div key={project.id} className="space-y-6">
                {showYearSeparator && (
                  <div className="flex items-center gap-4 py-4">
                    <div className="h-px bg-slate-200 flex-1" />
                    <span className="bg-slate-100 text-slate-500 px-4 py-1 rounded-full text-xs font-black uppercase tracking-widest">{project.academic_year} / {project.academic_year + 1}</span>
                    <div className="h-px bg-slate-200 flex-1" />
                  </div>
                )}
                
                <div className="group bg-white rounded-3xl border border-slate-200/60 shadow-sm hover:shadow-xl hover:shadow-slate-200/50 hover:border-tul-blue/30 transition-all duration-300 overflow-hidden flex flex-col md:flex-row">
                  <div className="flex-1 p-8 space-y-4">
                    <div className="flex justify-between items-start">
                      <div className="flex gap-2">
                        <span className="bg-slate-50 px-3 py-1.5 rounded-xl border border-slate-100 text-[10px] font-black uppercase tracking-widest text-slate-500">
                          {project.academic_year}
                        </span>
                        {project.results_unlocked && (
                          <span className="text-[10px] font-black text-green-600 bg-green-50 px-3 py-1.5 rounded-xl border border-green-100 uppercase tracking-widest">
                            {t('lecturer.results_unlocked')}
                          </span>
                        )}
                      </div>
                    </div>
                    
                    <h3 className="text-2xl font-black text-slate-800 transition-colors">
                      {project.title}
                    </h3>
                    
                    <div className="flex items-center gap-2">
                      <Users size={14} className="text-slate-400" />
                      <div className="text-xs font-bold text-slate-500 flex flex-wrap gap-x-3 gap-y-2">
                        {!project.results_unlocked ? (
                          project.members.length > 0 ? project.members.map((m) => (
                            <span key={m.id} className="flex items-center gap-1 group/member bg-slate-50 px-2 py-1 rounded-lg border border-slate-100">
                              {m.name || m.email}
                              {(user?.role === UserRole.ADMIN || isCourseOwner) && (
                                <button
                                  onClick={() => handleDeleteMember(project.id, m.id)}
                                  className="text-slate-300 hover:text-red-500 transition-colors opacity-0 group-hover/member:opacity-100"
                                  title={t('common.delete')}
                                >
                                  <X size={12} />
                                </button>
                              )}
                            </span>
                          )) : <span className="italic">{t('lecturer.no_members')}</span>
                        ) : (
                          project.members.map(member => {
                            const receivedFeedback = (project.received_peer_feedback || []).filter(f => f.receiving_student_id === member.id);
                            const memberBonus = receivedFeedback.length > 0 
                                ? receivedFeedback.reduce((sum, f) => sum + f.bonus_points, 0) / receivedFeedback.length
                                : 0;
                            const totalPoints = totalLecturerAvg + memberBonus;
                            const isPass = totalPoints >= course.min_score;

                            return (
                              <div key={member.id} className={`flex items-center gap-2 px-3 py-1.5 rounded-xl border text-[10px] font-black uppercase tracking-widest ${isPass ? 'bg-green-50 text-green-600 border-green-100' : 'bg-red-50 text-red-600 border-red-100'}`}>
                                <span>{member.name}</span>
                                <div className="flex items-center gap-1">
                                  <span>{Math.round(totalPoints * 10) / 10}</span>
                                  <span className="text-purple-600">({Math.round(memberBonus * 10) / 10})</span>
                                </div>
                              </div>
                            );
                          })
                        )}
                      </div>
                    </div>
                    
                    {/* Results Summary (when unlocked) */}
                    <div className="py-2">
                      {project.results_unlocked && (
                        <div className="space-y-4">
                          <div className="flex flex-wrap gap-2">
                            {criteriaAverages.map(c => (
                              <div key={c.code} className="bg-slate-50 px-3 py-1.5 rounded-xl border border-slate-100 text-[10px] font-black uppercase tracking-widest text-slate-500 flex items-center gap-2">
                                <span>{c.code}</span>
                                <span className={c.avg / c.max_score < 0.5 ? 'text-red-500' : c.avg / c.max_score < 0.75 ? 'text-amber-500' : 'text-green-500'}>
                                  {Math.round(c.avg * 10) / 10}
                                </span>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>

                    {!project.results_unlocked && (
                      <div className="pt-2">
                        {addingMemberTo === project.id ? (
                          <div className="space-y-2">
                            <form onSubmit={(e) => handleAddMember(e, project.id)} className="flex items-center gap-2 mt-2 bg-slate-50 p-2 rounded-xl border border-slate-100 max-w-sm">
                              <div className="relative flex-1">
                                <input 
                                  type="text" 
                                  required 
                                  placeholder={t('form.email_placeholder')}
                                  aria-label={t('form.email_placeholder')}
                                  value={memberEmail}
                                  onChange={e => setMemberEmail(e.target.value.split('@')[0])}
                                  className="w-full bg-white border border-slate-200 rounded-lg px-3 py-1.5 pr-16 text-sm text-slate-900 focus:outline-none focus:border-tul-blue focus:ring-1 flex-1"
                                />
                                <span className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 font-bold text-[10px] pointer-events-none">@tul.cz</span>
                              </div>
                              <button type="submit" className="text-xs bg-slate-700 hover:bg-slate-800 text-white px-3 py-1.5 rounded-lg font-bold transition-colors">
                                {t('form.add')}
                              </button>
                              <button type="button" onClick={() => { setAddingMemberTo(null); setMemberError(null); }} className="text-xs text-slate-500 hover:text-slate-700 font-bold">
                                {t('lecturer.cancel')}
                              </button>
                            </form>
                            {memberError && <p className="text-red-500 text-[10px] font-black uppercase tracking-wider ml-2">{memberError}</p>}
                          </div>
                        ) : (
                          <button 
                            onClick={() => setAddingMemberTo(project.id)}
                            className="text-xs font-bold text-tul-blue hover:text-tul-blue/80 transition-colors uppercase tracking-wider flex items-center group/add"
                          >
                            <Plus size={14} className="mr-1 group-hover/add:scale-110 transition-transform"/> {t('lecturer.add_member')}
                          </button>
                        )}
                      </div>
                    )}

                    <div className="flex items-center justify-between gap-4 mt-8 pt-6 border-t border-slate-100">
                      <div className="flex items-center gap-6 flex-wrap">
                        {canSeeEvaluations && (
                          <div className="flex items-center gap-1.5 text-xs font-bold">
                            {userEval ? (
                              userEval.submitted ? (
                                <><CheckCircle className="w-4 h-4 text-green-500" /><span className="text-slate-700">{t('lecturer.eval_submitted')}</span></>
                              ) : (
                                <><Clock className="w-4 h-4 text-amber-500" /><span className="text-slate-700">{t('lecturer.eval_draft')}</span></>
                              )
                            ) : (
                              <><AlertCircle className="w-4 h-4 text-slate-400" /><span className="text-slate-500">{t('lecturer.eval_not_done')}</span></>
                            )}
                          </div>
                        )}

                        {canSeeEvaluations && !project.results_unlocked && (
                          <div className="flex items-center gap-4">
                            <div className="flex items-center gap-2 text-slate-400">
                              <Users size={14} />
                              <span className="text-[10px] font-black uppercase tracking-wider">
                                {t('role.student')}: {project.submitted_student_count || 0}/{project.members.length}
                              </span>
                            </div>
                            <div className="flex items-center gap-2 text-slate-400">
                              <Users size={14} />
                              <span className="text-[10px] font-black uppercase tracking-wider">
                                {t('role.lecturer')}: {project.submitted_lecturer_count || 0}/{course.lecturers.length}
                              </span>
                            </div>
                          </div>
                        )}
                      </div>

                      <div className="flex gap-2">
                        {!project.results_unlocked && (user?.role === UserRole.ADMIN || isCourseOwner) && (
                          <button
                            onClick={() => handleDeleteProject(project.id)}
                            className="p-2.5 bg-white hover:bg-red-50 text-slate-400 hover:text-red-600 rounded-xl transition-colors flex items-center justify-center border border-slate-200 hover:border-red-200"
                            title={t('common.delete')}
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        )}
                        {user?.role === UserRole.ADMIN && project.results_unlocked && (
                          <button
                            onClick={() => handleRelockResults(project.id)}
                            className="p-2.5 bg-red-50 hover:bg-red-100 text-red-600 rounded-xl transition-colors flex items-center justify-center border border-red-200"
                            title={t('admin.relock_results')}
                          >
                            <Lock className="w-4 h-4" />
                          </button>
                        )}
                        {!project.results_unlocked && (user?.role === UserRole.ADMIN || isCourseOwner) && (
                          <button
                            onClick={() => handleUnlockResults(project.id)}
                            className="p-2.5 bg-amber-50 hover:bg-amber-100 text-amber-600 rounded-xl transition-colors flex items-center justify-center border border-amber-200"
                            title={t('lecturer.unlock_results')}
                          >
                            <LockOpen className="w-4 h-4" />
                          </button>
                        )}
                        {project.results_unlocked ? (
                          <Link
                            to={`/lecturer/project/${project.id}/results`}
                            className="px-5 py-2.5 bg-slate-50 hover:bg-tul-blue hover:text-white text-tul-blue rounded-xl transition-colors font-black text-xs border border-slate-200 hover:border-tul-blue uppercase tracking-wider"
                          >
                            {t('student.show_results')}
                          </Link>
                        ) : (
                          canSeeEvaluations && (
                            <Link
                              to={`/lecturer/project/${project.id}/evaluate`}
                              className="px-5 py-2.5 bg-slate-50 hover:bg-tul-blue hover:text-white text-tul-blue rounded-xl transition-colors font-black text-xs border border-slate-200 hover:border-tul-blue uppercase tracking-wider"
                            >
                              {userEval ? t('lecturer.edit_evaluation') : t('lecturer.evaluate')}
                            </Link>
                          )
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            );
          })
        )}
      </div>

      {/* Edit Course Modal */}
      <Modal
        isOpen={isEditModalOpen}
        onClose={() => setIsEditModalOpen(false)}
        title={t('admin.edit_course')}
        size="xl"
      >
        <CourseForm
          initialData={course}
          onSubmit={handleUpdateCourse}
          isLoading={editLoading}
          error={editError}
        />
      </Modal>
    </div>
  );
};
