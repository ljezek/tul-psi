import React, { useState, useEffect } from 'react';
import { Project, Student, Feedback, PeerEvaluation } from '../types';
import { Button } from './Button';
import { MessageSquare, User, Send, ThumbsUp, TrendingUp, Info, Award } from 'lucide-react';
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
  
  const activeProject = projects.find(p => p.id === selectedProjectId);
  const teammates = activeProject 
    ? students.filter(s => activeProject.authorIds.includes(s.id) && s.id !== currentStudentId)
    : [];

  // Form State
  const [subjectStrengths, setSubjectStrengths] = useState('');
  const [subjectImprovements, setSubjectImprovements] = useState('');
  
  // Peer evaluations state
  const [peerEvals, setPeerEvals] = useState<Record<string, { strengths: string, improvements: string, points: number }>>({});

  // Initialize peer evaluations when teammates change
  useEffect(() => {
    const initialEvals: Record<string, { strengths: string, improvements: string, points: number }> = {};
    teammates.forEach(mate => {
      initialEvals[mate.id] = {
        strengths: '',
        improvements: '',
        points: 10
      };
    });
    setPeerEvals(initialEvals);
    setSubjectStrengths('');
    setSubjectImprovements('');
  }, [selectedProjectId, teammates.length]);

  if (myProjects.length === 0) {
    return (
      <div className="text-center py-20 bg-white rounded-2xl shadow-sm border border-slate-200">
        <h2 className="text-xl font-bold text-slate-800">{t('student.no_project')}</h2>
        <p className="text-slate-500 mt-2">{t('student.contact_teacher')}</p>
      </div>
    );
  }

  const totalPointsAvailable = teammates.length * 10;
  const currentTotalPoints: number = (Object.values(peerEvals) as { points: number }[]).reduce((sum: number, e) => sum + e.points, 0);

  const handlePointChange = (targetId: string, newValue: number) => {
    const oldValue = peerEvals[targetId]?.points || 0;
    const diff = newValue - oldValue;
    
    if (diff === 0) return;

    const newEvals = { ...peerEvals };
    newEvals[targetId] = { ...newEvals[targetId], points: newValue };

    // Adjust other teammates to keep the total constant
    const otherIds = teammates.map(t => t.id).filter(id => id !== targetId);
    
    if (otherIds.length > 0) {
      let remainingDiff = diff;
      
      // Try to distribute the difference among others
      // If diff is positive (we added points), we need to subtract from others
      // If diff is negative (we removed points), we need to add to others
      
      // We'll do it in a loop to handle cases where some reach 0 or 20
      let iterations = 0;
      while (Math.abs(remainingDiff) > 0.01 && iterations < 10) {
        const eligibleOthers = otherIds.filter(id => {
          if (remainingDiff > 0) return newEvals[id].points > 0;
          return newEvals[id].points < 20;
        });

        if (eligibleOthers.length === 0) break;

        const perPersonDiff = remainingDiff / eligibleOthers.length;
        eligibleOthers.forEach(id => {
          const currentVal = newEvals[id].points;
          let nextVal = currentVal - perPersonDiff;
          
          if (nextVal < 0) {
            remainingDiff -= (currentVal - 0);
            nextVal = 0;
          } else if (nextVal > 20) {
            remainingDiff -= (currentVal - 20);
            nextVal = 20;
          } else {
            remainingDiff -= perPersonDiff;
          }
          newEvals[id] = { ...newEvals[id], points: Math.round(nextVal * 100) / 100 };
        });
        iterations++;
      }
    }

    // Final pass to ensure integers and exact sum
    // (Sliders usually use integers, let's stick to that for simplicity)
    const roundedEvals: Record<string, { strengths: string; improvements: string; points: number }> = {};
    let sum = 0;
    teammates.forEach((t, index) => {
      if (index === teammates.length - 1) {
        roundedEvals[t.id] = { ...newEvals[t.id], points: totalPointsAvailable - sum };
      } else {
        const p = Math.round(newEvals[t.id].points);
        roundedEvals[t.id] = { ...newEvals[t.id], points: p };
        sum += p;
      }
    });

    setPeerEvals(roundedEvals);
  };

  const handleFeedbackSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    const peerEvaluations: PeerEvaluation[] = teammates.map(mate => ({
      toStudentId: mate.id,
      strengths: peerEvals[mate.id].strengths,
      improvements: peerEvals[mate.id].improvements,
      points: peerEvals[mate.id].points
    }));

    const newFeedback: Feedback = {
      id: `f${Date.now()}`,
      projectId: selectedProjectId,
      fromStudentId: currentStudentId,
      subjectStrengths,
      subjectImprovements,
      peerEvaluations,
      createdAt: new Date().toISOString().split('T')[0]
    };

    onAddFeedback(newFeedback);
    alert(t('student.success_sent'));
    
    // Reset form
    setSubjectStrengths('');
    setSubjectImprovements('');
    const resetPeerEvals: Record<string, { strengths: string; improvements: string; points: number }> = {};
    teammates.forEach(m => {
      resetPeerEvals[m.id] = { strengths: '', improvements: '', points: 10 };
    });
    setPeerEvals(resetPeerEvals);
  };

  // Received feedback from peers (text only)
  const receivedPeerFeedback = feedbacks.filter(f => 
    f.projectId === selectedProjectId && 
    f.peerEvaluations.some(pe => pe.toStudentId === currentStudentId)
  ).map(f => {
    const evalForMe = f.peerEvaluations.find(pe => pe.toStudentId === currentStudentId);
    return {
      id: f.id,
      date: f.createdAt,
      strengths: evalForMe?.strengths || '',
      improvements: evalForMe?.improvements || ''
    };
  });

  return (
    <div className="space-y-8">
      <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-6">
          <h2 className="text-xl font-bold text-slate-900 flex items-center gap-2">
            <MessageSquare className="text-tul-blue" size={24} /> {t('student.subject_eval')}
          </h2>
          <div className="flex items-center gap-3">
            <label className="text-sm font-semibold text-slate-500 uppercase">{t('student.active_project')}:</label>
            <select 
              className="border border-slate-300 rounded-lg p-2 text-sm bg-slate-50 font-medium"
              value={selectedProjectId}
              onChange={(e) => setSelectedProjectId(e.target.value)}
            >
              {myProjects.map(p => (
                <option key={p.id} value={p.id}>{p.title}</option>
              ))}
            </select>
          </div>
        </div>

        <form onSubmit={handleFeedbackSubmit} className="space-y-8">
          {/* Subject Evaluation */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-2">
              <label className="block text-sm font-bold text-slate-700 flex items-center gap-2">
                <ThumbsUp size={16} className="text-green-600" /> {t('student.subject_strengths')}
              </label>
              <textarea
                className="w-full border border-slate-200 rounded-xl p-4 h-32 focus:ring-2 focus:ring-tul-blue focus:border-tul-blue resize-none shadow-sm"
                placeholder={t('student.strengths_ph')}
                value={subjectStrengths}
                onChange={e => setSubjectStrengths(e.target.value)}
                required
              />
            </div>
            <div className="space-y-2">
              <label className="block text-sm font-bold text-slate-700 flex items-center gap-2">
                <TrendingUp size={16} className="text-orange-600" /> {t('student.subject_improvements')}
              </label>
              <textarea
                className="w-full border border-slate-200 rounded-xl p-4 h-32 focus:ring-2 focus:ring-tul-blue focus:border-tul-blue resize-none shadow-sm"
                placeholder={t('student.improvements_ph')}
                value={subjectImprovements}
                onChange={e => setSubjectImprovements(e.target.value)}
                required
              />
            </div>
          </div>

          {/* Peer Feedback Section */}
          {teammates.length > 0 && (
            <div className="pt-6 border-t border-slate-100">
              <div className="flex items-center justify-between mb-6">
                <h3 className="text-lg font-bold text-slate-900 flex items-center gap-2">
                  <User className="text-purple-600" size={20} /> {t('student.peer_eval')}
                </h3>
                <div className="bg-purple-50 text-purple-700 px-3 py-1 rounded-full text-xs font-bold flex items-center gap-2">
                  <Award size={14} /> {t('student.points_remaining')}: {totalPointsAvailable - currentTotalPoints} / {totalPointsAvailable}
                </div>
              </div>

              <div className="space-y-8">
                {teammates.map(mate => (
                  <div key={mate.id} className="bg-slate-50 rounded-2xl p-6 border border-slate-200 space-y-6">
                    <div className="flex items-center gap-3 mb-2">
                      <div className="w-10 h-10 rounded-full bg-purple-100 flex items-center justify-center text-purple-700 font-bold">
                        {mate.name.charAt(0)}
                      </div>
                      <div>
                        <h4 className="font-bold text-slate-900">{mate.name}</h4>
                        <p className="text-xs text-slate-500">{mate.email}</p>
                      </div>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <textarea
                        className="w-full border border-slate-200 rounded-lg p-3 h-24 text-sm focus:ring-2 focus:ring-purple-500 bg-white"
                        placeholder={t('student.strengths_ph')}
                        value={peerEvals[mate.id]?.strengths || ''}
                        onChange={e => setPeerEvals({
                          ...peerEvals,
                          [mate.id]: { ...peerEvals[mate.id], strengths: e.target.value }
                        })}
                        required
                      />
                      <textarea
                        className="w-full border border-slate-200 rounded-lg p-3 h-24 text-sm focus:ring-2 focus:ring-purple-500 bg-white"
                        placeholder={t('student.improvements_ph')}
                        value={peerEvals[mate.id]?.improvements || ''}
                        onChange={e => setPeerEvals({
                          ...peerEvals,
                          [mate.id]: { ...peerEvals[mate.id], improvements: e.target.value }
                        })}
                        required
                      />
                    </div>

                    <div className="space-y-3">
                      <div className="flex justify-between items-center">
                        <label className="text-xs font-bold text-slate-500 uppercase tracking-wider">{t('student.points_allocation')}</label>
                        <span className="text-lg font-black text-purple-600">{peerEvals[mate.id]?.points || 0}</span>
                      </div>
                      <input 
                        type="range" 
                        min="0" 
                        max="20" 
                        step="1"
                        value={peerEvals[mate.id]?.points || 10}
                        onChange={(e) => handlePointChange(mate.id, parseInt(e.target.value))}
                        className="w-full h-2 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-purple-600"
                      />
                      <div className="flex justify-between text-[10px] text-slate-400 font-bold">
                        <span>0</span>
                        <span>10</span>
                        <span>20</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="flex flex-col md:flex-row justify-between items-center gap-4 pt-4">
            <div className="flex items-start gap-2 text-slate-500 max-w-md">
              <Info size={16} className="mt-0.5 shrink-0" />
              <p className="text-xs leading-relaxed">
                {t('student.disclaimer')} {t('student.anonymous_notice')}
              </p>
            </div>
            <Button type="submit" size="lg" className="w-full md:w-auto gap-2 shadow-md hover:shadow-lg transition-all">
              <Send size={18} /> {t('student.submit')}
            </Button>
          </div>
        </form>
      </div>

      {/* Received Feedback Section */}
      <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
        <h2 className="text-xl font-bold text-slate-900 mb-6 flex items-center gap-2">
          <ThumbsUp className="text-green-600" size={24} /> {t('student.received_feedback')}
        </h2>
        
        {receivedPeerFeedback.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {receivedPeerFeedback.map(f => (
              <div key={f.id} className="border border-slate-100 bg-slate-50/50 rounded-2xl p-5 space-y-4">
                <div className="flex justify-between items-center border-b border-slate-100 pb-2">
                  <span className="text-xs font-bold text-slate-400 uppercase tracking-widest">Feedback</span>
                  <span className="text-xs text-slate-400">{f.date}</span>
                </div>
                <div className="space-y-3">
                  <div>
                    <span className="text-[10px] font-black text-green-700 uppercase tracking-wider block mb-1">{t('student.label_strengths')}</span>
                    <p className="text-sm text-slate-700 leading-relaxed italic">"{f.strengths}"</p>
                  </div>
                  <div>
                    <span className="text-[10px] font-black text-orange-700 uppercase tracking-wider block mb-1">{t('student.label_improvements')}</span>
                    <p className="text-sm text-slate-700 leading-relaxed italic">"{f.improvements}"</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-12 bg-slate-50 rounded-xl border border-dashed border-slate-200">
            <p className="text-slate-400 italic">{t('feedback.no_feedback')}</p>
          </div>
        )}
      </div>
    </div>
  );
};
