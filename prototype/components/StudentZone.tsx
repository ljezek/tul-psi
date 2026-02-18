import React, { useState } from 'react';
import { Project, Student, Feedback } from '../types';
import { Button } from './Button';
import { MessageSquare, User, Send, ThumbsUp, TrendingUp } from 'lucide-react';
import { useLanguage } from '../LanguageContext';

interface StudentZoneProps {
  currentStudentId: string;
  projects: Project[];
  students: Student[];
  feedbacks: Feedback[];
  onAddFeedback: (feedback: Feedback) => void;
}

export const StudentZone: React.FC<StudentZoneProps> = ({ 
  currentStudentId, 
  projects, 
  students, 
  feedbacks,
  onAddFeedback 
}) => {
  const { t } = useLanguage();
  // Find project where the current student is an author
  const myProjects = projects.filter(p => p.authorIds.includes(currentStudentId));
  const [selectedProjectId, setSelectedProjectId] = useState<string>(myProjects[0]?.id || '');
  
  // Form State
  const [strengths, setStrengths] = useState('');
  const [improvements, setImprovements] = useState('');
  const [targetStudentId, setTargetStudentId] = useState<string>('');

  if (myProjects.length === 0) {
    return (
      <div className="text-center py-20 bg-white rounded-2xl shadow-sm border border-slate-200">
        <h2 className="text-xl font-bold text-slate-800">{t('student.no_project')}</h2>
        <p className="text-slate-500 mt-2">{t('student.contact_teacher')}</p>
      </div>
    );
  }

  const activeProject = projects.find(p => p.id === selectedProjectId);
  const teammates = activeProject 
    ? students.filter(s => activeProject.authorIds.includes(s.id) && s.id !== currentStudentId)
    : [];

  const handleFeedbackSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!targetStudentId || !strengths || !improvements) return;

    const newFeedback: Feedback = {
      id: `f${Date.now()}`,
      projectId: selectedProjectId,
      fromStudentId: currentStudentId,
      toStudentId: targetStudentId,
      strengths: strengths,
      improvements: improvements,
      createdAt: new Date().toISOString().split('T')[0]
    };

    onAddFeedback(newFeedback);
    setStrengths('');
    setImprovements('');
    setTargetStudentId('');
    alert(t('student.success_sent'));
  };

  const mySentFeedbacks = feedbacks.filter(f => f.fromStudentId === currentStudentId);

  return (
    <div className="max-w-5xl mx-auto grid grid-cols-1 lg:grid-cols-3 gap-8">
      {/* Left Column: Project Selector & Context */}
      <div className="lg:col-span-1 space-y-6">
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
          <h2 className="text-lg font-bold text-slate-900 mb-4 flex items-center gap-2">
            <User className="text-tul-blue" size={20} /> {t('student.my_team')}
          </h2>
          
          <div className="mb-4">
            <label className="block text-xs font-semibold text-slate-500 uppercase mb-2">{t('student.active_project')}</label>
            <select 
              className="w-full border border-slate-300 rounded-lg p-2 text-sm"
              value={selectedProjectId}
              onChange={(e) => {
                setSelectedProjectId(e.target.value);
                setTargetStudentId('');
              }}
            >
              {myProjects.map(p => (
                <option key={p.id} value={p.id}>{p.title}</option>
              ))}
            </select>
          </div>

          <div className="space-y-3">
             <h3 className="text-sm font-medium text-slate-700">{t('student.team_members')}:</h3>
             {teammates.length > 0 ? (
               teammates.map(mate => (
                 <div 
                   key={mate.id} 
                   className={`p-3 rounded-lg border cursor-pointer transition-colors flex items-center gap-3 ${targetStudentId === mate.id ? 'bg-blue-50 border-blue-200 ring-1 ring-blue-300' : 'bg-slate-50 border-slate-100 hover:border-blue-200'}`}
                   onClick={() => setTargetStudentId(mate.id)}
                 >
                    <div className="w-8 h-8 rounded-full bg-blue-200 flex items-center justify-center text-blue-700 text-xs font-bold">
                      {mate.name.charAt(0)}
                    </div>
                    <div>
                      <p className="text-sm font-medium text-slate-900">{mate.name}</p>
                      <p className="text-xs text-slate-500">{t('student.click_evaluate')}</p>
                    </div>
                 </div>
               ))
             ) : (
               <p className="text-sm text-slate-400 italic">{t('student.alone')}</p>
             )}
          </div>
        </div>
      </div>

      {/* Right Column: Feedback Form */}
      <div className="lg:col-span-2 space-y-6">
        <div className="bg-white rounded-xl shadow-lg border border-slate-200 overflow-hidden">
          <div className="bg-slate-50 p-4 border-b border-slate-200 flex justify-between items-center">
            <h2 className="font-bold text-slate-800 flex items-center gap-2">
              <MessageSquare size={18} /> Peer Feedback
            </h2>
            {targetStudentId && (
              <span className="text-sm bg-blue-100 text-tul-blue px-2 py-1 rounded">
                {t('student.evaluating')}: {students.find(s => s.id === targetStudentId)?.name}
              </span>
            )}
          </div>
          
          <div className="p-6">
            {!targetStudentId ? (
              <div className="text-center py-12 text-slate-400">
                <p>{t('student.select_colleague')}</p>
              </div>
            ) : (
              <form onSubmit={handleFeedbackSubmit} className="space-y-6">
                
                {/* Strengths Section */}
                <div className="bg-green-50/50 p-4 rounded-xl border border-green-100">
                  <label className="block text-sm font-bold text-green-800 mb-2 flex items-center gap-2">
                    <ThumbsUp size={16} /> {t('student.strengths')}
                  </label>
                  <textarea
                    className="w-full border border-green-200 rounded-lg p-3 h-24 focus:ring-2 focus:ring-green-500 focus:border-green-500 resize-none bg-white"
                    placeholder={t('student.strengths_ph')}
                    value={strengths}
                    onChange={e => setStrengths(e.target.value)}
                    required
                  />
                </div>

                {/* Improvements Section */}
                <div className="bg-orange-50/50 p-4 rounded-xl border border-orange-100">
                  <label className="block text-sm font-bold text-orange-800 mb-2 flex items-center gap-2">
                    <TrendingUp size={16} /> {t('student.improvements')}
                  </label>
                  <textarea
                    className="w-full border border-orange-200 rounded-lg p-3 h-24 focus:ring-2 focus:ring-orange-500 focus:border-orange-500 resize-none bg-white"
                    placeholder={t('student.improvements_ph')}
                    value={improvements}
                    onChange={e => setImprovements(e.target.value)}
                    required
                  />
                </div>

                <div className="flex justify-between items-center pt-2">
                   <p className="text-xs text-slate-500">
                    {t('student.disclaimer')}
                  </p>
                  <Button type="submit" className="gap-2">
                    <Send size={16} /> {t('student.submit')}
                  </Button>
                </div>
              </form>
            )}
          </div>
        </div>

        {/* History */}
        {mySentFeedbacks.length > 0 && (
           <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6 opacity-75">
             <h3 className="text-sm font-bold text-slate-500 uppercase tracking-wide mb-4">{t('student.sent_history')}</h3>
             <div className="space-y-4">
               {mySentFeedbacks.map(f => {
                 const receiver = students.find(s => s.id === f.toStudentId);
                 return (
                   <div key={f.id} className="border border-slate-200 rounded-lg p-4">
                     <div className="flex justify-between items-center mb-3 border-b border-slate-100 pb-2">
                       <span className="font-semibold text-sm text-slate-800">{t('student.for')}: {receiver?.name}</span>
                       <span className="text-xs text-slate-400">{f.createdAt}</span>
                     </div>
                     <div className="grid gap-3">
                        <div>
                            <span className="text-xs font-bold text-green-700 block mb-1">{t('student.label_strengths')}:</span>
                            <p className="text-sm text-slate-600">{f.strengths}</p>
                        </div>
                        <div>
                            <span className="text-xs font-bold text-orange-700 block mb-1">{t('student.label_improvements')}:</span>
                            <p className="text-sm text-slate-600">{f.improvements}</p>
                        </div>
                     </div>
                   </div>
                 );
               })}
             </div>
           </div>
        )}
      </div>
    </div>
  );
};