import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { 
  ArrowLeft, 
  Code, 
  ExternalLink, 
  Users, 
  BookOpen, 
  Calendar, 
  Mail,
  CheckCircle,
  BarChart3,
  Award
} from 'lucide-react';
import { useLanguage } from '@/contexts/LanguageContext';
import { useAuth } from '@/contexts/AuthContext';
import { getProject } from '@/api';
import { ProjectPublic, UserRole } from '@/types';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { ErrorMessage } from '@/components/ui/ErrorMessage';
import { Button } from '@/components/ui/Button';

export const ProjectDetail = () => {
  const { id } = useParams<{ id: string }>();
  const { t } = useLanguage();
  const { user } = useAuth();
  const [project, setProject] = useState<ProjectPublic | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchProject = async () => {
    if (!id) return;
    setLoading(true);
    setError(null);
    try {
      const data = await getProject(parseInt(id));
      setProject(data);
    } catch (err) {
      setError(t('projectDetail.error_fetching') || 'Failed to fetch project details');
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
        <ErrorMessage message={error || 'Project not found'} onRetry={fetchProject} retryLabel={t('error.retry')} />
      </div>
    );
  }

  const isMember = user && project.members.some(m => m.id === user.id);
  const isLecturerOrAdmin = user && (user.role === UserRole.LECTURER || user.role === UserRole.ADMIN);

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
          <span className="px-3 py-1 bg-tul-blue text-white text-sm font-bold rounded uppercase">
            {project.course.code}
          </span>
          <span className="text-slate-500 font-medium">
            {project.course.name}
          </span>
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
                      <Code size={20} />
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
                <li key={member.id} className="flex flex-col gap-1">
                  <span className="font-semibold text-slate-800">{member.name}</span>
                  <div className="flex items-center gap-3 text-xs text-slate-500">
                    {member.github_alias && (
                      <a 
                        href={`https://github.com/${member.github_alias}`} 
                        target="_blank" 
                        rel="noopener noreferrer"
                        className="flex items-center gap-1 hover:text-tul-blue transition-colors"
                      >
                        <Code size={12} />
                        {member.github_alias}
                      </a>
                    )}
                    {member.email && (
                      <span className="flex items-center gap-1">
                        <Mail size={12} />
                        {member.email}
                      </span>
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
                <div className="flex flex-col gap-2">
                  {project.course.lecturers.map((l, i) => (
                    <span key={i} className="font-medium text-slate-700">{l.name}</span>
                  ))}
                </div>
              </div>
            </div>
          </div>

          {/* Role-based Action Links */}
          {(isMember || isLecturerOrAdmin) && (
            <div className="space-y-3">
              <p className="text-xs text-slate-400 uppercase font-bold px-2 tracking-widest">
                {isLecturerOrAdmin ? t('project.lecturer_links') : t('project.student_links')}
              </p>
              {isMember && (
                <>
                  <Link to={`/student/project/${project.id}/evaluate`} className="block">
                    <Button variant="outline" className="w-full justify-start gap-3">
                      <CheckCircle size={18} className="text-green-500" />
                      {t('project.evaluate')}
                    </Button>
                  </Link>
                  {project.results_unlocked && (
                    <Link to={`/student/project/${project.id}/results`} className="block">
                      <Button variant="outline" className="w-full justify-start gap-3">
                        <BarChart3 size={18} className="text-tul-blue" />
                        {t('project.view_results')}
                      </Button>
                    </Link>
                  )}
                </>
              )}
              {isLecturerOrAdmin && (
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
