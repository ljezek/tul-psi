import { Link } from 'react-router-dom';
import { CheckCircle, Clock, ClipboardCheck, BarChart3, XCircle } from 'lucide-react';
import { ProjectPublic, UserPublic } from '@/types';
import { useLanguage } from '@/contexts/LanguageContext';
import { Button } from '@/components/ui/Button';

interface CourseEvaluationStatusCardProps {
  project: ProjectPublic;
  user: UserPublic | null;
  className?: string;
  isCompact?: boolean;
}

export const CourseEvaluationStatusCard = ({ 
  project, 
  user, 
  className = '',
  isCompact = false
}: CourseEvaluationStatusCardProps) => {
  const { t } = useLanguage();

  if (!user || !project.members.some(m => m.id === user.id)) {
    return null;
  }

  const userEval = project.course_evaluations?.[0];
  const isSubmitted = userEval?.submitted || false;
  const hasDraft = userEval !== undefined;
  
  const labelSize = isCompact ? 'text-[9px]' : 'text-[10px]';
  const statusSize = isCompact ? 'text-[11px]' : 'text-xs';
  const iconSize = isCompact ? 14 : 16;
  const buttonSize = isCompact ? 'sm' : 'md';

  const isPass = project.total_points != null && project.total_points >= project.course.min_score;
  const maxPoints = project.course.evaluation_criteria.reduce((sum, c) => sum + c.max_score, 0) + (project.course.peer_bonus_budget || 0);

  const totalLecturers = project.course.lecturers.length;
  const totalStudents = project.members.length;
  const submittedLecturers = project.submitted_lecturer_count || 0;
  const submittedStudents = project.submitted_student_count || 0;

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Evaluation Status */}
      <div className={isCompact ? "flex items-center justify-between" : "flex flex-col gap-3"}>
        <div className="flex flex-col gap-1">
          <span className={`${labelSize} font-black text-slate-400 uppercase tracking-widest`}>
            {t('student.evaluation_status')}
          </span>
          {isSubmitted ? (
            <span className={`inline-flex items-center gap-1.5 text-green-600 ${statusSize} font-bold`}>
              <CheckCircle size={iconSize} />
              {t('student.submitted')}
            </span>
          ) : hasDraft ? (
            <span className={`inline-flex items-center gap-1.5 text-amber-500 ${statusSize} font-bold`}>
              <Clock size={iconSize} />
              {t('student.draft')}
            </span>
          ) : (
            <span className={`inline-flex items-center gap-1.5 text-slate-400 ${statusSize} font-bold`}>
              <Clock size={iconSize} />
              {t('student.not_started')}
            </span>
          )}
        </div>
        
        {!project.results_unlocked && (
          <Link to={`/student/project/${project.id}/evaluate`} className={isCompact ? '' : 'block w-full'}>
            <Button variant="outline" size={buttonSize} className={`rounded-xl border-slate-200 text-slate-600 hover:bg-slate-50 font-bold ${isCompact ? 'text-[10px] h-7 px-2 gap-1' : 'w-full text-sm py-2 gap-2'}`}>
              <ClipboardCheck size={isCompact ? iconSize : 18} />
              {hasDraft ? t('student.edit_evaluation') : t('student.create_evaluation')}
            </Button>
          </Link>
        )}
      </div>

      {/* Results Status */}
      <div className={isCompact ? "flex items-center justify-between" : "flex flex-col gap-3"}>
        <div className="flex flex-col gap-1">
          <div className="flex items-center justify-between">
            <span className={`${labelSize} font-black text-slate-400 uppercase tracking-widest`}>
              {t('student.results_status')}
            </span>
            {project.results_unlocked && (
              <span className={`inline-flex items-center gap-1.5 ${isPass ? 'text-green-600' : 'text-red-600'} ${isCompact ? 'text-[9px]' : 'text-[10px]'} font-black uppercase tracking-wider bg-slate-50 px-2 py-0.5 rounded-lg border border-slate-100`}>
                {isPass ? <CheckCircle size={12} /> : <XCircle size={12} />}
                {isPass ? t('results.pass') : t('results.fail')}
              </span>
            )}
          </div>
          
          {project.results_unlocked ? (
            <div className="flex items-center gap-2 mt-1">
              <span className={`font-black ${statusSize} text-slate-700`}>
                {project.total_points != null ? Math.round(project.total_points * 10) / 10 : 0}/{maxPoints} {t('label.points')}
              </span>
              <span className="text-slate-300 font-bold">•</span>
              <span className="text-slate-400 text-[10px] font-bold">
                ({t('label.min_required')} {project.course.min_score})
              </span>
            </div>
          ) : (
            <div className="space-y-2 mt-1 relative group/hint cursor-help">
              <span className={`inline-flex items-center gap-1.5 text-slate-400 ${statusSize} font-bold`}>
                <Clock size={iconSize} />
                {t('lecturer.pending_status')
                  .replace('{s_curr}', submittedStudents.toString())
                  .replace('{s_total}', totalStudents.toString())
                  .replace('{l_curr}', submittedLecturers.toString())
                  .replace('{l_total}', totalLecturers.toString())
                }
              </span>
              <div className="absolute bottom-full left-0 mb-2 w-64 bg-slate-800 text-white text-[10px] p-2 rounded-lg opacity-0 group-hover/hint:opacity-100 transition-opacity pointer-events-none z-10 shadow-xl font-bold">
                {t('student.unlock_hint')}
              </div>
            </div>
          )}
        </div>

        {project.results_unlocked && (
          <Link to={`/student/project/${project.id}/results`} className={isCompact ? '' : 'block w-full'}> 
            <Button variant="outline" size={buttonSize} className={`rounded-xl border-tul-blue text-tul-blue hover:bg-tul-blue/5 font-black tracking-wider ${isCompact ? 'text-[10px] h-7 px-2 gap-1' : 'w-full text-xs py-2 gap-2'}`}>
              <BarChart3 size={isCompact ? iconSize : 18} />
              {t('student.show_results')}
            </Button>
          </Link>
        )}
      </div>
    </div>
  );
};
