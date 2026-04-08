import { useState, FormEvent } from 'react';
import { Plus, Trash2, Link as LinkIcon, ListChecks } from 'lucide-react';
import { useLanguage } from '@/contexts/LanguageContext';
import { CourseCreate, CourseUpdate, CourseDetail, CourseTerm, ProjectType, EvaluationCriterion, CourseLink } from '@/types';
import { Button } from '@/components/ui/Button';
import { ErrorMessage } from '@/components/ui/ErrorMessage';

interface CourseFormProps {
  initialData?: CourseDetail | null;
  onSubmit: (data: CourseCreate | CourseUpdate) => Promise<void>;
  isLoading: boolean;
  error: string | null;
}

export const CourseForm = ({ initialData, onSubmit, isLoading, error }: CourseFormProps) => {
  const { t } = useLanguage();

  const [code, setCode] = useState(initialData?.code || '');
  const [name, setName] = useState(initialData?.name || '');
  const [syllabus, setSyllabus] = useState(initialData?.syllabus || '');
  const [term, setTerm] = useState<CourseTerm>(initialData?.term || CourseTerm.WINTER);
  const [projectType, setProjectType] = useState<ProjectType>(initialData?.project_type || ProjectType.TEAM);
  const [minScore, setMinScore] = useState(initialData?.min_score || 50);
  const [peerBonusBudget, setPeerBonusBudget] = useState<number | null>(initialData?.peer_bonus_budget ?? null);
  
  const [evaluationCriteria, setEvaluationCriteria] = useState<EvaluationCriterion[]>(
    initialData?.evaluation_criteria || [{ code: 'final', description: 'Final Project', max_score: 100 }]
  );
  
  const [links, setLinks] = useState<CourseLink[]>(initialData?.links || []);

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    const data: CourseCreate | CourseUpdate = {
      code,
      name,
      syllabus: syllabus || null,
      term,
      project_type: projectType,
      min_score: minScore,
      peer_bonus_budget: peerBonusBudget,
      evaluation_criteria: evaluationCriteria,
      links,
    };
    onSubmit(data);
  };

  const addCriterion = () => {
    setEvaluationCriteria([...evaluationCriteria, { code: '', description: '', max_score: 0 }]);
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
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Basic Info */}
        <div className="space-y-4">
          <h3 className="text-sm font-black text-slate-900 uppercase tracking-widest border-b border-slate-100 pb-2">{t('lecturer.academic_years')}</h3>
          
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1.5 ml-1">{t('course.code')}</label>
              <input
                type="text"
                required
                value={code}
                onChange={e => setCode(e.target.value)}
                className="w-full bg-slate-50 border border-slate-200 rounded-xl px-4 py-2.5 text-slate-900 focus:outline-none focus:ring-2 focus:ring-tul-blue/20 font-bold"
              />
            </div>
            <div>
              <label className="block text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1.5 ml-1">{t('course.term')}</label>
              <select
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
            <label className="block text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1.5 ml-1">{t('course.name')}</label>
            <input
              type="text"
              required
              value={name}
              onChange={e => setName(e.target.value)}
              className="w-full bg-slate-50 border border-slate-200 rounded-xl px-4 py-2.5 text-slate-900 focus:outline-none focus:ring-2 focus:ring-tul-blue/20 font-bold"
            />
          </div>

          <div>
            <label className="block text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1.5 ml-1">{t('course.syllabus')}</label>
            <textarea
              value={syllabus}
              onChange={e => setSyllabus(e.target.value)}
              rows={4}
              className="w-full bg-slate-50 border border-slate-200 rounded-xl px-4 py-2.5 text-slate-900 focus:outline-none focus:ring-2 focus:ring-tul-blue/20 font-bold text-sm"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1.5 ml-1">{t('course.project_type')}</label>
              <select
                value={projectType}
                onChange={e => setProjectType(e.target.value as ProjectType)}
                className="w-full bg-slate-50 border border-slate-200 rounded-xl px-4 py-2.5 text-slate-900 focus:outline-none focus:ring-2 focus:ring-tul-blue/20 font-bold"
              >
                <option value={ProjectType.TEAM}>{t('enum.TEAM')}</option>
                <option value={ProjectType.INDIVIDUAL}>{t('enum.INDIVIDUAL')}</option>
              </select>
            </div>
            <div>
              <label className="block text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1.5 ml-1">{t('course.min_score')}</label>
              <input
                type="number"
                required
                min={0}
                value={minScore}
                onChange={e => setMinScore(parseInt(e.target.value, 10))}
                className="w-full bg-slate-50 border border-slate-200 rounded-xl px-4 py-2.5 text-slate-900 focus:outline-none focus:ring-2 focus:ring-tul-blue/20 font-bold"
              />
            </div>
          </div>

          <div>
            <label className="block text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1.5 ml-1">{t('course.peer_bonus')}</label>
            <div className="flex items-center gap-3">
              <input
                type="number"
                min={0}
                disabled={peerBonusBudget === null}
                value={peerBonusBudget || 0}
                onChange={e => setPeerBonusBudget(parseInt(e.target.value, 10))}
                className="flex-1 bg-slate-50 border border-slate-200 rounded-xl px-4 py-2.5 text-slate-900 focus:outline-none focus:ring-2 focus:ring-tul-blue/20 font-bold disabled:opacity-50"
              />
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={peerBonusBudget !== null}
                  onChange={e => setPeerBonusBudget(e.target.checked ? 10 : null)}
                  className="rounded border-slate-300 text-tul-blue focus:ring-tul-blue"
                />
                <span className="text-xs font-bold text-slate-600">{t('admin.active')}</span>
              </label>
            </div>
          </div>
        </div>

        {/* Evaluation Criteria */}
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
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1 ml-1">{t('course.code')}</label>
                    <input
                      type="text"
                      required
                      value={c.code}
                      onChange={e => updateCriterion(i, 'code', e.target.value)}
                      placeholder="e.g. code_quality"
                      className="w-full bg-white border border-slate-200 rounded-lg px-3 py-1.5 text-xs text-slate-900 focus:outline-none focus:ring-2 focus:ring-tul-blue/20 font-bold"
                    />
                  </div>
                  <div>
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
                <div>
                  <label className="block text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1 ml-1">{t('courseDetail.evaluation_criteria')}</label>
                  <input
                    type="text"
                    required
                    value={c.description}
                    onChange={e => updateCriterion(i, 'description', e.target.value)}
                    placeholder="e.g. Code Quality & Architecture"
                    className="w-full bg-white border border-slate-200 rounded-lg px-3 py-1.5 text-xs text-slate-900 focus:outline-none focus:ring-2 focus:ring-tul-blue/20 font-bold"
                  />
                </div>
              </div>
            ))}
          </div>

          {/* Links */}
          <div className="pt-4">
            <div className="flex items-center justify-between border-b border-slate-100 pb-2 mb-4">
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
                    <label className="block text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1 ml-1">Label</label>
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
                    <label className="block text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1 ml-1">URL</label>
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
      </div>

      {error && <ErrorMessage message={error} />}
      
      <div className="flex justify-end gap-3 pt-6 border-t border-slate-100">
        <Button type="submit" isLoading={isLoading} className="px-12">
          {initialData ? t('common.save') : t('form.add')}
        </Button>
      </div>
    </form>
  );
};
