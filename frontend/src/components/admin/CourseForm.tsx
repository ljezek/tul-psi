import { useState, FormEvent } from 'react';
import { Plus, Trash2, Link as LinkIcon, ListChecks, Info, User } from 'lucide-react';
import { useLanguage } from '@/contexts/LanguageContext';
import { useAuth } from '@/contexts/AuthContext';
import { CourseCreate, CourseUpdate, CourseDetail, CourseTerm, ProjectType, EvaluationCriterion, CourseLink } from '@/types';
import { Button } from '@/components/ui/Button';
import { ErrorMessage } from '@/components/ui/ErrorMessage';

export interface CourseFormProps {
  initialData?: CourseDetail | null;
  onSubmit: (data: CourseCreate | CourseUpdate) => Promise<void>;
  isLoading: boolean;
  error: string | null;
}

export const CourseForm = ({ initialData, onSubmit, isLoading, error }: CourseFormProps) => {
  const { t } = useLanguage();
  const { user: currentUser } = useAuth();

  const [code, setCode] = useState(initialData?.code || '');
  const [name, setName] = useState(initialData?.name || '');
  const [syllabus, setSyllabus] = useState(initialData?.syllabus || '');
  const [term, setTerm] = useState<CourseTerm>(initialData?.term || CourseTerm.WINTER);
  const [projectType, setProjectType] = useState<ProjectType>(initialData?.project_type || ProjectType.INDIVIDUAL);
  const [minScore, setMinScore] = useState(initialData?.min_score || 40);
  const [peerBonusBudget, setPeerBonusBudget] = useState<number>(initialData?.peer_bonus_budget ?? 0);
  
  const [evaluationCriteria, setEvaluationCriteria] = useState<EvaluationCriterion[]>(
    initialData?.evaluation_criteria || [
      { code: 'docs', description: t('course.default_criterion_docs'), max_score: 20 },
      { code: 'code', description: t('course.default_criterion_code'), max_score: 20 },
      { code: 'test', description: t('course.default_criterion_test'), max_score: 20 }
    ]
  );
  
  const [links, setLinks] = useState<CourseLink[]>(initialData?.links || []);

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    
    // Auto-calculate codes for criteria
    const processedCriteria = evaluationCriteria.map(c => {
      if (c.code && c.code !== 'new') return c;
      const firstWord = c.description.trim().split(/\s+/)[0].toLowerCase().replace(/[^a-z0-9]/g, '');
      return { ...c, code: firstWord || 'criterion' };
    });

    const data = {
      code,
      name,
      syllabus: syllabus || null,
      term,
      project_type: projectType,
      min_score: minScore,
      peer_bonus_budget: projectType === ProjectType.TEAM && peerBonusBudget > 0 ? peerBonusBudget : null,
      evaluation_criteria: processedCriteria,
      links,
    } as CourseCreate | CourseUpdate;
    
    onSubmit(data);
  };

  const addCriterion = () => {
    setEvaluationCriteria([...evaluationCriteria, { code: 'new', description: '', max_score: 20 }]);
  };

  const updateCriterion = (index: number, field: keyof EvaluationCriterion, value: string | number) => {
    const next = [...evaluationCriteria];
    next[index] = { ...next[index], [field]: value };
    setEvaluationCriteria(next);
  };

  const removeCriterion = (index: number) => {
    setEvaluationCriteria(evaluationCriteria.filter((_, i) => i !== index));
  };

  const addLink = () => {
    setLinks([...links, { label: '', url: '' }]);
  };

  const updateLink = (index: number, field: keyof CourseLink, value: string) => {
    const next = [...links];
    next[index] = { ...next[index], [field]: value };
    setLinks(next);
  };

  const removeLink = (index: number) => {
    setLinks(links.filter((_, i) => i !== index));
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-8">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        {/* Left Column: Basic Info & Links */}
        <div className="space-y-6">
          <div className="space-y-4">
            <h3 className="text-sm font-black text-slate-900 uppercase tracking-widest border-b border-slate-100 pb-2">{t('course.info')}</h3>
            
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label htmlFor="course-code" className="block text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1.5 ml-1">{t('course.code')}</label>
                <input
                  id="course-code"
                  type="text"
                  required
                  value={code}
                  onChange={e => setCode(e.target.value)}
                  className="w-full bg-slate-50 border border-slate-200 rounded-xl px-4 py-2.5 text-slate-900 focus:outline-none focus:ring-2 focus:ring-tul-blue/20 font-bold"
                />
              </div>
              <div>
                <label htmlFor="course-term" className="block text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1.5 ml-1">{t('course.term')}</label>
                <select
                  id="course-term"
                  value={term}
                  onChange={e => setTerm(e.target.value as CourseTerm)}
                  className="w-full bg-slate-50 border border-slate-200 rounded-xl px-4 py-2.5 text-slate-900 focus:outline-none focus:ring-2 focus:ring-tul-blue/20 font-bold"
                >
                  <option value={CourseTerm.WINTER}>{t('enum.WINTER')}</option>
                  <option value={CourseTerm.SUMMER}>{t('enum.SUMMER')}</option>
                </select>
              </div>
            </div>

            <div>
              <label htmlFor="course-name" className="block text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1.5 ml-1">{t('course.name')}</label>
              <input
                id="course-name"
                type="text"
                required
                value={name}
                onChange={e => setName(e.target.value)}
                className="w-full bg-slate-50 border border-slate-200 rounded-xl px-4 py-2.5 text-slate-900 focus:outline-none focus:ring-2 focus:ring-tul-blue/20 font-bold"
              />
            </div>

            <div>
              <label htmlFor="course-syllabus" className="block text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1.5 ml-1">
                {t('course.syllabus')}
                <span className="ml-2 lowercase font-normal opacity-60">({t('form.markdown_supported')})</span>
              </label>
              <textarea
                id="course-syllabus"
                value={syllabus}
                onChange={e => setSyllabus(e.target.value)}
                rows={3}
                className="w-full bg-slate-50 border border-slate-200 rounded-xl px-4 py-2.5 text-slate-900 focus:outline-none focus:ring-2 focus:ring-tul-blue/20 font-bold text-sm"
              />
            </div>
          </div>

          {/* Links Section */}
          <div className="space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 pb-2">
              <h3 className="text-sm font-black text-slate-900 uppercase tracking-widest flex items-center gap-2">
                <LinkIcon size={16} className="text-tul-blue" />
                {t('course.links')}
              </h3>
              <button
                type="button"
                onClick={addLink}
                className="p-1 hover:bg-tul-blue/10 text-tul-blue rounded-lg transition-colors"
                title={t('course.add_link')}
              >
                <Plus size={20} />
              </button>
            </div>
            <div className="space-y-3">
              {links.map((link, i) => (
                <div key={i} className="flex gap-2 items-end group">
                  <div className="flex-1">
                    <input
                      type="text"
                      required
                      value={link.label}
                      onChange={e => updateLink(i, 'label', e.target.value)}
                      placeholder="e.g. eLearning"
                      className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 text-xs text-slate-900 focus:outline-none focus:ring-2 focus:ring-tul-blue/20 font-bold"
                    />
                  </div>
                  <div className="flex-[2]">
                    <input
                      type="url"
                      required
                      value={link.url}
                      onChange={e => updateLink(i, 'url', e.target.value)}
                      placeholder="https://..."
                      className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 text-xs text-slate-900 focus:outline-none focus:ring-2 focus:ring-tul-blue/20 font-bold"
                    />
                  </div>
                  <button
                    type="button"
                    onClick={() => removeLink(i)}
                    className="p-2.5 text-slate-400 hover:text-red-500 transition-colors"
                  >
                    <Trash2 size={16} />
                  </button>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Right Column: Project Type, Scores & Criteria */}
        <div className="space-y-6">
          <div className="space-y-4">
            <h3 className="text-sm font-black text-slate-900 uppercase tracking-widest border-b border-slate-100 pb-2">{t('project.type')} & {t('lecturer.score')}</h3>
            
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label htmlFor="course-project-type" className="block text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1.5 ml-1">{t('course.project_type')}</label>
                <select
                  id="course-project-type"
                  value={projectType}
                  onChange={e => {
                    const newType = e.target.value as ProjectType;
                    setProjectType(newType);
                    if (newType === ProjectType.TEAM && peerBonusBudget === 0) {
                      setPeerBonusBudget(10);
                    }
                  }}
                  className="w-full bg-slate-50 border border-slate-200 rounded-xl px-4 py-2.5 text-slate-900 focus:outline-none focus:ring-2 focus:ring-tul-blue/20 font-bold"
                >
                  <option value={ProjectType.TEAM}>{t('enum.TEAM')}</option>
                  <option value={ProjectType.INDIVIDUAL}>{t('enum.INDIVIDUAL')}</option>
                </select>
              </div>
              <div>
                <label htmlFor="course-min-score" className="block text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1.5 ml-1">{t('course.min_score')}</label>
                <input
                  id="course-min-score"
                  type="number"
                  required
                  min={0}
                  value={minScore}
                  onChange={e => setMinScore(parseInt(e.target.value, 10))}
                  className="w-full bg-slate-50 border border-slate-200 rounded-xl px-4 py-2.5 text-slate-900 focus:outline-none focus:ring-2 focus:ring-tul-blue/20 font-bold"
                />
              </div>
            </div>

            {projectType === ProjectType.TEAM && (
              <div className={`p-4 rounded-2xl border transition-colors ${peerBonusBudget > 0 ? 'bg-purple-50 border-purple-100' : 'bg-slate-50 border-slate-200'}`}>
                <label htmlFor="course-peer-bonus" className={`block text-[10px] font-black uppercase tracking-widest mb-1.5 ml-1 ${peerBonusBudget > 0 ? 'text-purple-400' : 'text-slate-400'}`}>
                  {t('course.peer_bonus')}
                </label>
                <div className="flex items-center gap-4">
                  <input
                    id="course-peer-bonus"
                    type="number"
                    min={0}
                    value={peerBonusBudget}
                    onChange={e => setPeerBonusBudget(parseInt(e.target.value, 10) || 0)}
                    className="w-24 bg-white border border-slate-200 rounded-xl px-4 py-2 text-slate-900 focus:outline-none focus:ring-2 focus:ring-tul-blue/20 font-bold"
                  />
                  <div className="flex-1 flex items-start gap-2 text-[10px] font-bold text-slate-500 leading-tight">
                    <Info size={14} className="shrink-0 text-slate-400 mt-0.5" />
                    {t('course.peer_bonus_hint')}
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Evaluation Criteria Section */}
          <div className="space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 pb-2">
              <h3 className="text-sm font-black text-slate-900 uppercase tracking-widest flex items-center gap-2">
                <ListChecks size={16} className="text-tul-blue" />
                {t('course.criteria')}
              </h3>
              <button
                type="button"
                onClick={addCriterion}
                className="p-1 hover:bg-tul-blue/10 text-tul-blue rounded-lg transition-colors"
                title={t('course.add_criterion')}
              >
                <Plus size={20} />
              </button>
            </div>

            <div className="space-y-3">
              {evaluationCriteria.map((c, i) => (
                <div key={i} className="bg-slate-50 p-4 rounded-2xl border border-slate-200 space-y-3 relative group">
                  <button
                    type="button"
                    onClick={() => removeCriterion(i)}
                    className="absolute top-2 right-2 p-1.5 text-slate-400 hover:text-red-500 hover:bg-red-50 rounded-lg transition-all"
                  >
                    <Trash2 size={14} />
                  </button>
                  <div className="flex gap-3">
                    <div className="flex-[3]">
                      <label className="block text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1 ml-1">{t('course.criterion')}</label>
                      <input
                        type="text"
                        required
                        value={c.description}
                        onChange={e => updateCriterion(i, 'description', e.target.value)}
                        placeholder="e.g. Code Quality"
                        className="w-full bg-white border border-slate-200 rounded-lg px-3 py-1.5 text-xs text-slate-900 focus:outline-none focus:ring-2 focus:ring-tul-blue/20 font-bold"
                      />
                    </div>
                    <div className="flex-1">
                      <label className="block text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1 ml-1">{t('lecturer.score')}</label>
                      <input
                        type="number"
                        required
                        min={1}
                        value={c.max_score}
                        onChange={e => updateCriterion(i, 'max_score', parseInt(e.target.value, 10))}
                        className="w-full bg-white border border-slate-200 rounded-lg px-3 py-1.5 text-xs text-slate-900 focus:outline-none focus:ring-2 focus:ring-tul-blue/20 font-bold"
                      />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {error && <ErrorMessage message={error} />}
      
      <div className="flex justify-end gap-3 pt-6 border-t border-slate-100">
        <Button variant="ghost" type="button" onClick={() => window.history.back()}>{t('common.cancel')}</Button>
        <Button type="submit" isLoading={isLoading} className="px-12">
          {initialData ? t('common.save') : t('form.add')}
        </Button>
      </div>
    </form>
  );
};
