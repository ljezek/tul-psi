import { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { 
  ArrowLeft, 
  Award, 
  CheckCircle, 
  XCircle, 
  User, 
  ThumbsUp, 
  TrendingUp,
  ShieldAlert
} from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import { useLanguage } from '@/contexts/LanguageContext';
import { getProject } from '@/api';
import { ProjectPublic } from '@/types';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { ErrorMessage } from '@/components/ui/ErrorMessage';

import { ProjectHero } from '@/components/project/ProjectHero';
import { MemberInfo } from '@/components/project/MemberInfo';

export const Results = () => {
  // ... rest of state ...
  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-12 space-y-12">
      <ProjectHero 
        project={project}
        backLink={{ to: '/student', label: t('project.back_to_projects') }}
        rightContent={
          <div className="text-right">
            <span className={`px-4 py-1.5 rounded-xl border flex items-center gap-2 font-black text-sm tracking-tight mb-4 ${
              isPass ? 'bg-green-50 border-green-200 text-green-700' : 'bg-red-50 border-red-200 text-red-700'
            }`}>
              {isPass ? <CheckCircle size={18} /> : <XCircle size={18} />}
              {isPass ? t('results.pass') : t('results.fail')}
            </span>
            <span className="text-[10px] font-black text-slate-400 uppercase tracking-widest block mb-1">
              {t('results.total_score')}
            </span>
            <div className="flex items-baseline gap-1 justify-end">
              <span className={`text-5xl font-black ${isPass ? 'text-green-600' : 'text-red-600'}`}>
                {Math.round(finalTotal * 10) / 10}
              </span>
              <span className="text-slate-300 font-bold text-xl">/</span>
              <span className="text-slate-400 font-bold text-xl">{criteria.reduce((s, c) => s + c.max_score, 0) + (project.course.peer_bonus_budget || 0)}</span>
            </div>
          </div>
        }
        bottomContent={
          <div className="flex flex-wrap gap-x-8 gap-y-2">
            <div>
              <span className="text-[10px] font-black text-slate-400 uppercase tracking-widest block">
                {t('results.avg_score')}
              </span>
              <span className="text-lg font-black text-slate-700">
                {Math.round(lecturerTotal * 10) / 10}
              </span>
            </div>
            {project.course.peer_bonus_budget !== null && (
              <div>
                <span className="text-[10px] font-black text-slate-400 uppercase tracking-widest block">
                  {t('results.avg_bonus')}
                </span>
                <span className="text-lg font-black text-purple-600">
                  +{Math.round(avgPeerBonus * 10) / 10}
                </span>
              </div>
            )}
            <div>
              <span className="text-[10px] font-black text-slate-400 uppercase tracking-widest block">
                {t('results.min_required')}
              </span>
              <span className="text-lg font-black text-slate-400">
                {project.course.min_score}
              </span>
            </div>
          </div>
        }
      />

      <div className="space-y-12">
// ...

      <div className="space-y-12">
        {/* Lecturer Feedback */}
        <section className="bg-white rounded-3xl shadow-lg border border-slate-100 overflow-hidden">
          <div className="bg-slate-50 px-8 py-6 border-b border-slate-100 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Award className="text-tul-blue" size={24} />
              <h2 className="text-xl font-black text-slate-800">{t('results.lecturer_eval')}</h2>
            </div>
            <div className="bg-tul-blue/5 text-tul-blue px-4 py-2 rounded-2xl border border-tul-blue/10 text-xs font-black uppercase">
              {t('results.avg_score')}: {Math.round(lecturerTotal * 10) / 10}
            </div>
          </div>
          <div className="p-8 space-y-12">
            {avgScores.map(c => (
              <div key={c.code} className="space-y-6 pb-12 last:pb-0 border-b last:border-0 border-slate-50">
                <div className="flex justify-between items-end">
                  <div>
                    <h3 className="text-xl font-black text-slate-800">{c.description}</h3>
                  </div>
                  <div className="text-right">
                    <span className="text-3xl font-black text-slate-700">{Math.round(c.avg * 10) / 10}</span>
                    <span className="text-slate-300 font-bold mx-1 text-xl">/</span>
                    <span className="text-slate-400 font-bold text-xl">{c.max_score}</span>
                  </div>
                </div>
                {/* Progress Bar */}
                <div className="h-3 w-full bg-slate-100 rounded-full overflow-hidden">
                  <div 
                    className={`h-full transition-all duration-1000 ${
                      (c.avg / c.max_score) > 0.7 ? 'bg-green-500' : (c.avg / c.max_score) > 0.4 ? 'bg-amber-500' : 'bg-red-500'
                    }`}
                    style={{ width: `${(c.avg / c.max_score) * 100}%` }}
                  />
                </div>
                {/* Lecturer Comments */}
                <div className="space-y-4">
                  {evaluations.map((evalItem, idx) => {
                    const score = evalItem.scores.find(s => s.criterion_code === c.code);
                    if (!score?.strengths && !score?.improvements) return null;
                    return (
                      <div key={idx} className="grid grid-cols-1 md:grid-cols-2 gap-6 p-6 rounded-2xl bg-slate-50/30 border border-slate-100">
                        <div className="space-y-3">
                          <div className="flex items-center gap-2 text-[10px] font-black text-green-700 uppercase tracking-widest mb-1">
                            <ThumbsUp size={12} />
                            {t('student.label_strengths')}
                          </div>
                          {score.strengths ? (
                            <div className="prose prose-sm prose-slate max-w-none text-slate-600 italic">
                              <ReactMarkdown>{score.strengths}</ReactMarkdown>
                            </div>
                          ) : (
                            <p className="text-sm text-slate-300 italic">---</p>
                          )}
                        </div>
                        <div className="space-y-3">
                          <div className="flex items-center gap-2 text-[10px] font-black text-orange-700 uppercase tracking-widest mb-1">
                            <TrendingUp size={12} />
                            {t('student.label_improvements')}
                          </div>
                          {score.improvements ? (
                            <div className="prose prose-sm prose-slate max-w-none text-slate-600 italic">
                              <ReactMarkdown>{score.improvements}</ReactMarkdown>
                            </div>
                          ) : (
                            <p className="text-sm text-slate-300 italic">---</p>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* Peer Feedback */}
        {project.course.project_type === 'TEAM' && (
          <section className="bg-white rounded-3xl shadow-lg border border-slate-100 overflow-hidden">
            <div className="bg-slate-50 px-8 py-6 border-b border-slate-100 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <User className="text-purple-600" size={24} />
                <h2 className="text-xl font-black text-slate-800">{t('results.peer_feedback')}</h2>
              </div>
              {project.course.peer_bonus_budget !== null && (
                <div className="bg-purple-50 text-purple-700 px-4 py-2 rounded-2xl border border-purple-100 text-xs font-black uppercase">
                  {t('results.avg_bonus')}: {Math.round(avgPeerBonus * 10) / 10}
                </div>
              )}
            </div>
            <div className="p-8 space-y-8">
              {peerBonus.length > 0 ? (
                <div className="space-y-8">
                  {peerBonus.map((f, idx) => (
                    <div key={idx} className="bg-slate-50/50 rounded-2xl p-8 border border-slate-100 space-y-6">
                      <div className="flex justify-between items-center border-b border-slate-100 pb-4 mb-2">
                        <span className="text-[10px] font-black text-slate-400 uppercase tracking-widest">{t('results.feedback')} #{idx + 1}</span>
                        {project.course.peer_bonus_budget !== null && (
                          <div className="flex items-center gap-2">
                            <span className="text-[10px] font-black text-purple-400 uppercase tracking-widest">{t('student.points_allocation')}</span>
                            <span className="text-lg font-black text-purple-600">+{f.bonus_points} {t('courseDetail.points')}</span>
                          </div>
                        )}
                      </div>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                        <div className="space-y-3">
                          <span className="text-[10px] font-black text-green-700 uppercase tracking-wider flex items-center gap-2">
                            <ThumbsUp size={12} />
                            {t('student.label_strengths')}
                          </span>
                          {f.strengths ? (
                            <div className="prose prose-sm prose-slate max-w-none text-slate-700 leading-relaxed italic">
                              <ReactMarkdown>{f.strengths}</ReactMarkdown>
                            </div>
                          ) : (
                            <p className="text-sm text-slate-300 italic">---</p>
                          )}
                        </div>
                        <div className="space-y-3">
                          <span className="text-[10px] font-black text-orange-700 uppercase tracking-wider flex items-center gap-2">
                            <TrendingUp size={12} />
                            {t('student.label_improvements')}
                          </span>
                          {f.improvements ? (
                            <div className="prose prose-sm prose-slate max-w-none text-slate-700 leading-relaxed italic">
                              <ReactMarkdown>{f.improvements}</ReactMarkdown>
                            </div>
                          ) : (
                            <p className="text-sm text-slate-300 italic">---</p>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-12 bg-slate-50 rounded-3xl border border-dashed border-slate-200">
                  <p className="text-slate-400 italic">{t('feedback.no_feedback')}</p>
                </div>
              )}
            </div>
          </section>
        )}
      </div>
    </div>
  );
};
