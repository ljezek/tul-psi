import React, { useEffect, useState, FormEvent } from 'react';
import { useParams, Link } from 'react-router';
import { ArrowLeft, Plus, LockOpen, CheckCircle, Clock, AlertCircle, Users, XCircle } from 'lucide-react';
import { useLanguage } from '@/contexts/LanguageContext';
import { useAuth } from '@/contexts/AuthContext';
import { getCourse, getProjects, createCourseProject, addProjectMember, unlockProject, getProject, getProjectEvaluation } from '@/api';
import { CourseDetail, ProjectPublic } from '@/types';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { ErrorMessage } from '@/components/ui/ErrorMessage';

const getErrorMsg = (err: unknown, defaultMsg: string): string => {
  const errorObj = err as { detail?: string | Array<{ msg?: string }> };
  if (typeof errorObj?.detail === 'string') return errorObj.detail;
  if (Array.isArray(errorObj?.detail)) return errorObj.detail.map(e => e.msg).filter(Boolean).join(', ');
  return defaultMsg;
};

export const CourseProjects = () => {
  const { id } = useParams<{ id: string }>();
  const { t } = useLanguage();
  
  const [course, setCourse] = useState<CourseDetail | null>(null);
  const [projects, setProjects] = useState<ProjectPublic[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [yearFilter, setYearFilter] = useState<string>('all');
  
  // Local Evaluations State
  const [evalStatuses, setEvalStatuses] = useState<Record<number, { submitted: boolean } | null>>({});

  // Add Project Form
  const [showAddForm, setShowAddForm] = useState(false);
  const [addTitle, setAddTitle] = useState('');
  const [addYear, setAddYear] = useState(new Date().getFullYear());
  const [addOwnerEmail, setAddOwnerEmail] = useState('');
  const [addError, setAddError] = useState<string | null>(null);

  // Add Member State
  const [addingMemberTo, setAddingMemberTo] = useState<number | null>(null);
  const [memberEmail, setMemberEmail] = useState('');
  
  const loadData = async () => {
    try {
      setLoading(true);
      const courseId = parseInt(id as string, 10);
      const courseData = await getCourse(courseId);
      setCourse(courseData);
      
      const projectsData = await getProjects({ course: courseData.code });
      
      const [fullProjects, statuses] = await Promise.all([
        Promise.all(projectsData.map(async (p) => {
          if (p.results_unlocked) return await getProject(p.id);
          return p;
        })),
        Promise.all(projectsData.map(async (p) => {
          if (p.results_unlocked) return [p.id, null] as const;
          try {
            const ev = await getProjectEvaluation(p.id);
            return [p.id, { submitted: ev.submitted }] as const;
          } catch (e: any) {
            return [p.id, null] as const;
          }
        }))
      ]);
      
      setProjects(fullProjects);
      
      const statusMap: Record<number, { submitted: boolean } | null> = {};
      statuses.forEach(([pid, st]) => { statusMap[pid] = st; });
      setEvalStatuses(statusMap);
    } catch (err) {
      setError(getErrorMsg(err, t('courseDetail.error_fetching')));
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
        owner_email: addOwnerEmail || undefined,
        technologies: [],
      });
      setShowAddForm(false);
      setAddTitle('');
      setAddOwnerEmail('');
      await loadData();
    } catch (err) {
      setAddError(getErrorMsg(err, 'Error creating project'));
    }
  };

  const handleAddMember = async (e: FormEvent, projectId: number) => {
    e.preventDefault();
    try {
      await addProjectMember(projectId, { email: memberEmail });
      setAddingMemberTo(null);
      setMemberEmail('');
      await loadData();
    } catch (err) {
      alert(getErrorMsg(err, 'Error adding member'));
    }
  };

  const handleUnlockResults = async (projectId: number) => {
    if (!window.confirm(t('common.confirm_action'))) return;
    try {
      await unlockProject(projectId);
      await loadData();
    } catch (err) {
      alert(getErrorMsg(err, 'Error unlocking results'));
    }
  };

  if (loading) return <div className="py-20"><LoadingSpinner /></div>;
  if (error || !course) return <div className="max-w-7xl mx-auto px-4 py-12"><ErrorMessage message={error || 'Course not found'} /></div>;

  // Derive academic years
  const availableYears = Array.from(new Set(projects.map(p => p.academic_year))).sort((a, b) => b - a);
  let filteredProjects = projects;
  if (yearFilter !== 'all') {
    filteredProjects = projects.filter(p => p.academic_year === parseInt(yearFilter, 10));
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12 space-y-8 animate-fade-in">
      {/* Back link */}
      <div>
        <Link to="/lecturer" className="inline-flex items-center text-sm font-bold text-slate-400 hover:text-slate-900 transition-colors uppercase tracking-wider">
          <ArrowLeft className="w-4 h-4 mr-2" />
          {t('nav.lecturer_panel')}
        </Link>
      </div>

      {/* Course Header */}
      <div className="bg-white rounded-3xl p-8 border border-slate-200/60 shadow-sm">
        <h1 className="text-3xl font-black text-slate-900 mb-2">{course.code} – {course.name}</h1>
        <div className="flex flex-wrap gap-4 text-slate-500 font-bold text-sm">
          <span>{t(`enum.${course.term}`)}</span>
          <span className="text-slate-300">&bull;</span>
          <span>{t(`enum.${course.project_type}`)}</span>
          <span className="text-slate-300">&bull;</span>
          <span>{course.lecturers.map(l => l.name).join(', ')}</span>
        </div>
      </div>

      {/* Toolbar */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-2 bg-white rounded-xl p-1 border border-slate-200/60 shadow-sm">
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

        <button
          onClick={() => setShowAddForm(!showAddForm)}
          className="inline-flex items-center px-5 py-2.5 bg-tul-blue hover:bg-tul-blue/90 text-white rounded-xl transition-colors font-black text-sm shadow-sm"
        >
          <Plus className="w-4 h-4 mr-2" />
          {t('lecturer.add_project')}
        </button>
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
                <input
                  type="email"
                  value={addOwnerEmail}
                  onChange={e => setAddOwnerEmail(e.target.value)}
                  placeholder="name@tul.cz"
                  className="w-full bg-white border border-slate-200 rounded-xl px-4 py-2.5 text-slate-900 focus:outline-none focus:ring-2 focus:ring-tul-blue/20 focus:border-tul-blue"
                />
              </div>
            </div>
            {addError && <p className="text-red-500 text-sm font-bold">{addError}</p>}
            <div className="flex justify-end">
              <button type="submit" className="bg-tul-blue hover:bg-tul-blue/90 text-white px-6 py-2.5 rounded-xl text-sm font-black transition-colors shadow-sm">
                {t('lecturer.add_project')}
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Projects List */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {filteredProjects.length === 0 ? (
          <div className="col-span-1 lg:col-span-2 text-slate-400 font-medium text-center py-12">{t('dashboard.no_results')}</div>
        ) : (
          filteredProjects.map(project => {
            const userEval = evalStatuses[project.id];
            
            return (
              <div key={project.id} className="group bg-white rounded-3xl border border-slate-200/60 shadow-sm hover:shadow-xl hover:shadow-slate-200/50 hover:border-tul-blue/30 transition-all duration-300 overflow-hidden flex flex-col p-8">
                <div className="space-y-4 flex-1">
                  <div className="flex justify-between items-start">
                    <span className="bg-slate-50 px-3 py-1.5 rounded-xl border border-slate-100 text-[10px] font-black uppercase tracking-widest text-slate-500">
                      {project.academic_year}
                    </span>
                    {project.results_unlocked && (
                      <span className="text-[10px] font-black text-green-600 bg-green-50 px-3 py-1.5 rounded-xl border border-green-100 uppercase tracking-widest">
                        {t('lecturer.results_unlocked')}
                      </span>
                    )}
                  </div>
                  
                  <h3 className="text-2xl font-black text-slate-800 line-clamp-2 transition-colors">
                    {project.title}
                  </h3>
                  
                  <div className="flex items-center gap-2">
                    <Users size={14} className="text-slate-400" />
                    <div className="text-xs font-bold text-slate-500 flex flex-wrap gap-x-2">
                      {project.members.length > 0 ? project.members.map((m, idx) => (
                        <span key={m.id}>{m.name || m.email}{idx < project.members.length - 1 ? ',' : ''}</span>
                      )) : <span className="italic">žádní členové</span>}
                    </div>
                  </div>
                  
                  {addingMemberTo === project.id ? (
                    <form onSubmit={(e) => handleAddMember(e, project.id)} className="flex items-center gap-2 mt-4 bg-slate-50 p-2 rounded-xl border border-slate-100">
                      <input 
                        type="email" 
                        required 
                        placeholder={t('form.email_placeholder')}
                        value={memberEmail}
                        onChange={e => setMemberEmail(e.target.value)}
                        className="bg-white border border-slate-200 rounded-lg px-3 py-1.5 text-sm text-slate-900 focus:outline-none focus:border-tul-blue focus:ring-1 flex-1"
                      />
                      <button type="submit" className="text-xs bg-slate-700 hover:bg-slate-800 text-white px-3 py-1.5 rounded-lg font-bold transition-colors">
                        {t('form.add')}
                      </button>
                      <button type="button" onClick={() => setAddingMemberTo(null)} className="text-xs text-slate-500 hover:text-slate-700 font-bold">
                        Zrušit
                      </button>
                    </form>
                  ) : (
                    <button 
                      onClick={() => setAddingMemberTo(project.id)}
                      disabled={project.results_unlocked ?? false}
                      className={`text-xs font-bold transition-colors uppercase tracking-wider flex items-center mt-2 group/add ${
                        project.results_unlocked ? 'text-slate-300 cursor-not-allowed' : 'text-tul-blue hover:text-tul-blue/80'
                      }`}
                    >
                      <Plus size={14} className="mr-1 group-hover/add:scale-110 transition-transform"/> {t('lecturer.add_member')}
                    </button>
                  )}
                </div>

                {project.results_unlocked && (() => {
                  const isPass = project.total_points != null && course != null && project.total_points >= course.min_score;
                  const maxPoints = course ? course.evaluation_criteria.reduce((sum, c) => sum + c.max_score, 0) + (course.peer_bonus_budget || 0) : 0;
                  const criteria = course?.evaluation_criteria || [];
                  const evaluations = project.project_evaluations || [];
                  const avgScores = criteria.map(criterion => {
                    const scores = evaluations.map(e => e.scores.find(s => s.criterion_code === criterion.code)?.score || 0);
                    const avg = scores.length > 0 ? scores.reduce((a, b) => a + b, 0) / scores.length : 0;
                    return { ...criterion, avg };
                  });
                  const peerBonus = project.received_peer_feedback || [];
                  const avgPeerBonus = peerBonus.length > 0 
                    ? peerBonus.reduce((sum, f) => sum + f.bonus_points, 0) / peerBonus.length 
                    : 0;

                  return (
                    <div className="mt-6 bg-slate-50 rounded-2xl p-5 border border-slate-100 flex flex-col gap-4">
                      <div className="flex items-center justify-between">
                        <span className="text-[10px] font-black text-slate-400 uppercase tracking-widest">{t('student.results_status')}</span>
                        <span className={`inline-flex items-center gap-1.5 ${isPass ? 'text-green-600' : 'text-red-600'} text-[10px] font-black uppercase tracking-wider bg-white px-2 py-0.5 rounded-lg border border-slate-100`}>
                          {isPass ? <CheckCircle size={12} /> : <XCircle size={12} />}
                          {isPass ? t('results.pass') : t('results.fail')}
                        </span>
                      </div>
                      <div className="flex flex-wrap gap-x-6 gap-y-4">
                        {avgScores.map(c => (
                          <div key={c.code} className="flex flex-col">
                            <span className="text-[10px] font-black text-slate-400 uppercase tracking-widest">{c.code}</span>
                            <span className="text-sm font-black text-slate-700">{Math.round(c.avg * 10) / 10} <span className="text-xs text-slate-400">/ {c.max_score}</span></span>
                          </div>
                        ))}
                        {course?.peer_bonus_budget !== null && (
                          <div className="flex flex-col">
                            <span className="text-[10px] font-black text-slate-400 uppercase tracking-widest">{t('results.avg_bonus')}</span>
                            <span className="text-sm font-black text-purple-600">+{Math.round(avgPeerBonus * 10) / 10}</span>
                          </div>
                        )}
                        <div className="flex flex-col border-l border-slate-200 pl-6 ml-auto">
                          <span className="text-[10px] font-black text-slate-400 uppercase tracking-widest">{t('results.total_score')}</span>
                          <span className={`text-sm font-black ${isPass ? 'text-green-600' : 'text-red-600'}`}>
                            {project.total_points != null ? Math.round(project.total_points * 10) / 10 : 0} <span className="text-xs text-slate-400">/ {maxPoints}</span>
                          </span>
                        </div>
                      </div>
                    </div>
                  );
                })()}

                <div className="flex items-center justify-between gap-4 mt-8 pt-6 border-t border-slate-100">
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
                        {t('lecturer.evaluate')}
                      </Link>
                    )}
                  </div>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};
