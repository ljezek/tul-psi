import { useState, useEffect, useMemo, Fragment } from 'react';
import { useParams, Link } from 'react-router-dom';
import { 
  ArrowLeft, 
  BookOpen, 
  ListChecks, 
  FolderKanban,
  Star,
  ExternalLink
} from 'lucide-react';
import { useLanguage } from '@/contexts/LanguageContext';
import { getCourse, getProjects } from '@/api';
import { CourseDetail, ProjectPublic } from '@/types';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { ErrorMessage } from '@/components/ui/ErrorMessage';

import { CourseHero } from '@/components/course/CourseHero';
import { ProjectCard } from '@/components/project/ProjectCard';

export const CourseDetailView = () => {
  const { id } = useParams<{ id: string }>();
  const { t } = useLanguage();
  
  const [course, setCourse] = useState<CourseDetail | null>(null);
  const [projects, setProjects] = useState<ProjectPublic[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

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
        className="inline-flex items-center gap-2 text-sm font-medium text-slate-500 hover:text-tul-blue mb-8 transition-colors"
      >
        <ArrowLeft size={16} />
        {t('courseDetail.back_to_list')}
      </Link>

      {/* Hero */}
      <CourseHero course={course} className="mb-12" />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-12">
        {/* Main Content */}
        <div className="lg:col-span-2 space-y-12">
          {/* Syllabus */}
          <section>
            <h2 className="text-2xl font-bold text-slate-900 mb-6 flex items-center gap-3">
              <BookOpen size={24} className="text-tul-blue" />
              {t('courseDetail.syllabus')}
            </h2>
            <div className="prose prose-slate max-w-none text-slate-700 leading-relaxed whitespace-pre-wrap bg-white p-8 rounded-2xl border border-slate-100 shadow-sm">
              {course.syllabus || t('project.no_description')}
            </div>
          </section>

          {/* Evaluation Criteria */}
          <section>
            <h2 className="text-2xl font-bold text-slate-900 mb-6 flex items-center gap-3">
              <ListChecks size={24} className="text-tul-blue" />
              {t('courseDetail.evaluation_criteria')}
            </h2>
            <div className="bg-white rounded-2xl border border-slate-100 shadow-sm overflow-hidden">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="bg-slate-50 border-b border-slate-100">
                    <th className="px-6 py-4 text-xs font-bold text-slate-400 uppercase tracking-widest">{t('lecturer.criterion')}</th>
                    <th className="px-6 py-4 text-xs font-bold text-slate-400 uppercase tracking-widest text-right">{t('lecturer.score')}</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-50">
                  {course.evaluation_criteria.map((criterion, idx) => (
                    <tr key={idx} className="hover:bg-slate-50/50 transition-colors">
                      <td className="px-6 py-4">
                        <div className="font-semibold text-slate-800">{criterion.description}</div>
                      </td>
                      <td className="px-6 py-4 text-right font-mono font-bold text-slate-700">
                        {criterion.max_score}
                      </td>
                    </tr>
                  ))}
                  
                  {/* Students peer-bonus body */}
                  {course.peer_bonus_budget != null && (
                    <tr className="bg-blue-50/30">
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-2 font-bold text-blue-800">
                          <Star size={16} className="text-blue-500 fill-blue-500" />
                          {t('courseDetail.peer_bonus')}
                        </div>
                      </td>
                      <td className="px-6 py-4 text-right font-mono font-bold text-blue-700">
                        {course.peer_bonus_budget}
                      </td>
                    </tr>
                  )}

                  <tr className="bg-slate-50/50 font-bold border-t-2 border-slate-100">
                    <td className="px-6 py-4 text-slate-900">{t('courseDetail.min_score')}</td>
                    <td className="px-6 py-4 text-right text-tul-blue">{course.min_score} {t('courseDetail.points')}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </section>

          {/* Projects */}
          <section>
            <h2 className="text-2xl font-bold text-slate-900 mb-6 flex items-center gap-3">
              <FolderKanban size={24} className="text-tul-blue" />
              {t('courseDetail.projects')}
            </h2>
            {sortedProjects.length > 0 ? (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {sortedProjects.map((project, index) => {
                  const showYearSeparator = index > 0 && project.academic_year !== sortedProjects[index - 1].academic_year;
                  return (
                    <Fragment key={project.id}>
                      {showYearSeparator && (
                        <div className="col-span-full pt-4 pb-2">
                          <hr className="border-slate-200" />
                        </div>
                      )}
                      <ProjectCard 
                        project={project} 
                        href={`/projects/${project.id}`} 
                        showCourseBadge={false}
                        showLinks={false}
                        className="!shadow-none !border-slate-100 hover:!border-tul-blue/20"
                      />
                    </Fragment>
                  );
                })}
              </div>
            ) : (
              <p className="text-slate-500 italic px-4 py-8 border border-dashed border-slate-200 rounded-2xl text-center">
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
    </div>
  );
};
