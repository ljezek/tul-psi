import { Link } from 'react-router-dom';
import { CheckCircle, Clock, ClipboardCheck, BarChart3 } from 'lucide-react';
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

  const myEval = (project.course_evaluations || []).find(e => e.student_id == user?.id);
  const isSubmitted = myEval?.submitted === true;

  const labelSize = isCompact ? 'text-[9px]' : 'text-[10px]';
  const statusSize = isCompact ? 'text-[10px]' : 'text-xs';
  const iconSize = isCompact ? 12 : 14;
  const buttonSize = isCompact ? 'sm' : 'md';

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
              {isSubmitted ? t('student.update_evaluation') : t('student.create_evaluation')}
            </Button>
          </Link>
        )}
      </div>

      {/* Results Status */}
      <div className={isCompact ? "flex items-center justify-between" : "flex flex-col gap-3"}>
        <div className="flex flex-col gap-1">
          <span className={`${labelSize} font-black text-slate-400 uppercase tracking-widest`}>
            {t('student.results_status')}
          </span>
          {project.results_unlocked ? (
            <span className={`inline-flex items-center gap-1.5 text-green-600 ${statusSize} font-bold`}>
              <CheckCircle size={iconSize} />
              {t('student.results_available')}
            </span>
          ) : (
            <div className="flex flex-col gap-1">
              <span className={`inline-flex items-center gap-1.5 text-slate-400 ${statusSize} font-bold`}>
                <Clock size={iconSize} />
                {t('student.results_pending')}
              </span>
              <div className={`${isCompact ? 'text-[8px]' : 'text-[10px]'} font-bold text-slate-400/80`}>
                {t('student.lecturers')}: {project.submitted_lecturer_count ?? 0}/{project.course.lecturers.length}, {t('student.students')}: {project.submitted_student_count ?? 0}/{project.members.length}
              </div>
            </div>
          )}
        </div>

        {project.results_unlocked && (
          <Link to={`/student/project/${project.id}/results`} className={isCompact ? '' : 'block w-full mt-3'}>
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
