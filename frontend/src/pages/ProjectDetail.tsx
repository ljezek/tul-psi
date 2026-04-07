import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { 
  BookOpen, 
  CheckCircle,
  Award,
  ExternalLink
} from 'lucide-react';
import { GitHubLogo } from '@/components/icons/GitHubLogo';
import { useLanguage } from '@/contexts/LanguageContext';
import { useAuth } from '@/contexts/AuthContext';
import { getProject } from '@/api';
import { ProjectPublic, UserRole } from '@/types';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { ErrorMessage } from '@/components/ui/ErrorMessage';
import { Button } from '@/components/ui/Button';
import { CourseEvaluationStatusCard } from '@/components/student/CourseEvaluationStatusCard';

import { ProjectHero } from '@/components/project/ProjectHero';
import { MemberInfo } from '@/components/project/MemberInfo';

export const ProjectDetail = () => {
  const { id } = useParams<{ id: string }>();
  const { t } = useLanguage();
  const { user } = useAuth();
  const [project, setProject] = useState<ProjectPublic | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

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

  const isMember = user && project.members.some(m => m.id === user.id);
  const isOwningLecturer = user && project.course.lecturers.some(l => l.id === user.id);
  const showLecturerControls = user && (user.role === UserRole.ADMIN || (user.role === UserRole.LECTURER && isOwningLecturer));

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-12">
      <ProjectHero 
        project={project} 
        backLink={{ to: '/', label: t('project.back_to_projects') }}
      />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-12">
        {/* Main Content */}
        <div className="lg:col-span-2 space-y-10">
          {/* Description */}
          <section>
            <h2 className="text-xl font-bold text-slate-900 mb-4 flex items-center gap-2">
              <BookOpen size={20} className="text-tul-blue" />
              {t('form.full_desc')}
            </h2>
            <div className="prose prose-slate max-w-none text-slate-700 leading-relaxed whitespace-pre-wrap">
              {project.description || t('project.no_description')}
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
              <Award size={20} className="text-tul-blue" />
              {t('project.members')}
            </h2>
            <MemberInfo members={project.members} variant="list" />
          </div>

          {/* Course Info */}
          <div className="bg-slate-50 rounded-2xl border border-slate-100 p-6">
            <h2 className="text-lg font-bold text-slate-900 mb-4">
              {t('project.course_info')}
            </h2>
            <div className="space-y-3 text-sm">
              <div className="flex justify-between">
                <span className="text-slate-500">{t('project.term')}</span>
                <span className="font-medium text-slate-700">{t(`enum.${project.course.term}`)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">{t('project.type')}</span>
                <span className="font-medium text-slate-700">{t(`enum.${project.course.project_type}`)}</span>
              </div>
              <div className="pt-3 mt-3 border-t border-slate-200">
                <p className="text-xs text-slate-400 uppercase font-bold mb-4 tracking-widest">
                  {t('role.lecturer')}
                </p>
                <MemberInfo members={project.course.lecturers} variant="list" className="space-y-4" />
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
                <Link to={`/lecturer/project/${project.id}/evaluate`} className="block">
                  <Button variant="outline" className="w-full justify-start gap-3">
                    <CheckCircle size={18} className="text-tul-blue" />
                    {t('project.evaluate')}
                  </Button>
                </Link>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
