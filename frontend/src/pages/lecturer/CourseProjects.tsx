import { useEffect, useState, FormEvent, useMemo } from 'react';
import { useParams, Link } from 'react-router';
import { ArrowLeft, Plus, LockOpen, CheckCircle, Clock, AlertCircle, Users, UserPlus } from 'lucide-react';
import { useLanguage } from '@/contexts/LanguageContext';
import { useAuth } from '@/contexts/AuthContext';
import { getCourse, getProjects, createCourseProject, addProjectMember, unlockProject, addCourseLecturer, ApiError } from '@/api';
import { CourseDetail, ProjectPublic } from '@/types';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { ErrorMessage } from '@/components/ui/ErrorMessage';

import { CourseHero } from '@/components/course/CourseHero';
import { ProjectCard } from '@/components/project/ProjectCard';

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

  const sortedProjects = useMemo(() => {
    return [...projects].sort((a, b) => {
      if (a.academic_year !== b.academic_year) {
        return b.academic_year - a.academic_year;
      }
      return a.title.localeCompare(b.title);
    });
  }, [projects]);

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

      {/* Course Hero */}
      <CourseHero 
        course={course} 
        variant="lecturer" 
        showDetails={true}
        actions={
          <>
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
          </>
        }
      />

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
              criteriaAverages = (course.evaluation_criteria || []).map(criterion => {
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
                
                <ProjectCard 
                  project={project} 
                  variant="lecturer"
                  headerActions={
                    project.results_unlocked && (
                      <span className="text-[10px] font-black text-green-600 bg-green-50 px-3 py-1.5 rounded-xl border border-green-100 uppercase tracking-widest">
                        {t('lecturer.results_unlocked')}
                      </span>
                    )
                  }
                  footer={
                    <div className="flex items-center justify-between gap-4 mt-8 pt-6 border-t border-slate-100">
                      <div className="flex items-center gap-6 flex-wrap">
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

                        {!project.results_unlocked && (
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
                        {!project.results_unlocked && (
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
                          <Link
                            to={`/lecturer/project/${project.id}/evaluate`}
                            className="px-5 py-2.5 bg-slate-50 hover:bg-tul-blue hover:text-white text-tul-blue rounded-xl transition-colors font-black text-xs border border-slate-200 hover:border-tul-blue uppercase tracking-wider"
                          >
                            {userEval ? t('lecturer.edit_evaluation') : t('lecturer.evaluate')}
                          </Link>
                        )}
                      </div>
                    </div>
                  }
                >
                  {project.results_unlocked && (
                    <div className="flex items-center gap-2 mb-4">
                      {project.members.map(member => {
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
                      })}
                    </div>
                  )}

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
                </ProjectCard>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};
