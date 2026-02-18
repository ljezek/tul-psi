import React, { useState } from 'react';
import { Subject, Project, Student, Feedback } from '../types';
import { Button } from './Button';
import { PlusCircle, Save, BookOpen, Monitor, MessageSquare, ArrowRight, User } from 'lucide-react';
import { useLanguage } from '../LanguageContext';

interface AdminPanelProps {
  subjects: Subject[];
  students: Student[];
  projects: Project[];
  feedbacks: Feedback[];
  onAddSubject: (subject: Subject) => void;
  onAddProject: (project: Project) => void;
  onAddStudent: (student: Student) => void;
}

export const AdminPanel: React.FC<AdminPanelProps> = ({ 
  subjects, 
  students, 
  projects,
  feedbacks,
  onAddSubject, 
  onAddProject, 
  onAddStudent 
}) => {
  const [activeTab, setActiveTab] = useState<'subject' | 'project' | 'feedback'>('project');
  const { t } = useLanguage();
  
  // Subject Form State
  const [subjectForm, setSubjectForm] = useState({ code: '', name: '' });
  
  // Project Form State
  const [projectForm, setProjectForm] = useState<Partial<Project>>({
    title: '',
    description: '',
    fullDescription: '',
    academicYear: '2023/2024',
    subjectId: '',
    tags: [],
    authorIds: []
  });
  const [tagInput, setTagInput] = useState('');

  // Manual Student Form State
  const [newStudentName, setNewStudentName] = useState('');
  const [newStudentEmail, setNewStudentEmail] = useState('');

  const handleSubjectSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!subjectForm.code || !subjectForm.name) return;
    
    onAddSubject({
      id: `s${Date.now()}`,
      ...subjectForm
    });
    setSubjectForm({ code: '', name: '' });
    alert(t('form.success_subject'));
  };

  const handleProjectSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!projectForm.title || !projectForm.subjectId) return;

    onAddProject({
      id: `p${Date.now()}`,
      title: projectForm.title!,
      description: projectForm.description || '',
      fullDescription: projectForm.fullDescription || '',
      academicYear: projectForm.academicYear || '2023/2024',
      subjectId: projectForm.subjectId!,
      tags: tagInput.split(',').map(t => t.trim()).filter(Boolean),
      authorIds: projectForm.authorIds || [],
      githubUrl: projectForm.githubUrl,
      liveUrl: projectForm.liveUrl,
      imageUrl: 'https://picsum.photos/400/300' // Default placeholder
    } as Project);

    setProjectForm({ title: '', description: '', fullDescription: '', academicYear: '2023/2024', subjectId: '', tags: [], authorIds: [] });
    setTagInput('');
    alert(t('form.success_project'));
  };

  const toggleAuthor = (studentId: string) => {
    const current = projectForm.authorIds || [];
    const updated = current.includes(studentId)
      ? current.filter(id => id !== studentId)
      : [...current, studentId];
    setProjectForm({ ...projectForm, authorIds: updated });
  };

  const handleAddManualStudent = () => {
    if (!newStudentName || !newStudentEmail) return;

    const newStudent: Student = {
      id: `u${Date.now()}`,
      name: newStudentName,
      email: newStudentEmail
    };

    onAddStudent(newStudent);
    
    // Automatically select the new student
    const currentAuthors = projectForm.authorIds || [];
    setProjectForm({
      ...projectForm,
      authorIds: [...currentAuthors, newStudent.id]
    });

    setNewStudentName('');
    setNewStudentEmail('');
  };

  // Helper to get name
  const getStudentName = (id: string) => students.find(s => s.id === id)?.name || 'Neznámý student';

  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-8 text-center">
        <h1 className="text-3xl font-bold text-slate-900 mb-2">{t('admin.title')}</h1>
        <p className="text-slate-500">{t('admin.subtitle')}</p>
      </div>

      <div className="bg-white rounded-2xl shadow-lg overflow-hidden border border-slate-200">
        <div className="flex border-b border-slate-200">
          <button 
            onClick={() => setActiveTab('project')}
            className={`flex-1 py-4 text-center font-medium flex items-center justify-center gap-2 transition-colors ${activeTab === 'project' ? 'bg-blue-50 text-tul-blue border-b-2 border-tul-blue' : 'text-slate-600 hover:bg-slate-50'}`}
          >
            <Monitor size={18} /> {t('admin.tab_project')}
          </button>
          <button 
            onClick={() => setActiveTab('subject')}
            className={`flex-1 py-4 text-center font-medium flex items-center justify-center gap-2 transition-colors ${activeTab === 'subject' ? 'bg-blue-50 text-tul-blue border-b-2 border-tul-blue' : 'text-slate-600 hover:bg-slate-50'}`}
          >
            <BookOpen size={18} /> {t('admin.tab_subject')}
          </button>
          <button 
            onClick={() => setActiveTab('feedback')}
            className={`flex-1 py-4 text-center font-medium flex items-center justify-center gap-2 transition-colors ${activeTab === 'feedback' ? 'bg-blue-50 text-tul-blue border-b-2 border-tul-blue' : 'text-slate-600 hover:bg-slate-50'}`}
          >
            <MessageSquare size={18} /> {t('admin.tab_feedback')}
          </button>
        </div>

        <div className="p-8">
          {activeTab === 'project' && (
            <form onSubmit={handleProjectSubmit} className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">{t('form.project_title')}</label>
                  <input 
                    type="text" 
                    required
                    className="w-full border border-slate-300 rounded-lg p-2.5 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    value={projectForm.title}
                    onChange={e => setProjectForm({...projectForm, title: e.target.value})}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">{t('form.subject')}</label>
                  <select 
                    required
                    className="w-full border border-slate-300 rounded-lg p-2.5 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white text-slate-900"
                    value={projectForm.subjectId}
                    onChange={e => setProjectForm({...projectForm, subjectId: e.target.value})}
                  >
                    <option value="">{t('form.select_subject')}</option>
                    {subjects.map(s => <option key={s.id} value={s.id}>{s.name} ({s.code})</option>)}
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">{t('form.short_desc')}</label>
                <input 
                  type="text" 
                  maxLength={150}
                  className="w-full border border-slate-300 rounded-lg p-2.5 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  value={projectForm.description}
                  onChange={e => setProjectForm({...projectForm, description: e.target.value})}
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">{t('form.full_desc')}</label>
                <textarea 
                  rows={4}
                  className="w-full border border-slate-300 rounded-lg p-2.5 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  value={projectForm.fullDescription}
                  onChange={e => setProjectForm({...projectForm, fullDescription: e.target.value})}
                />
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">{t('form.tags')}</label>
                  <input 
                    type="text" 
                    placeholder="React, AI, Python..."
                    className="w-full border border-slate-300 rounded-lg p-2.5 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    value={tagInput}
                    onChange={e => setTagInput(e.target.value)}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">{t('form.academic_year')}</label>
                  <input
                    type="text"
                    placeholder="např. 2023/2024"
                    className="w-full border border-slate-300 rounded-lg p-2.5 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    value={projectForm.academicYear}
                    onChange={e => setProjectForm({...projectForm, academicYear: e.target.value})}
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">{t('form.assign_students')}</label>
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 border border-slate-200 rounded-lg p-4 bg-slate-50 max-h-40 overflow-y-auto">
                  {students.map(s => (
                    <label key={s.id} className="flex items-center gap-2 cursor-pointer hover:bg-white p-1 rounded">
                      <input 
                        type="checkbox" 
                        checked={projectForm.authorIds?.includes(s.id)}
                        onChange={() => toggleAuthor(s.id)}
                        className="rounded text-blue-600 focus:ring-blue-500"
                      />
                      <span className="text-sm text-slate-700">{s.name}</span>
                    </label>
                  ))}
                </div>
                
                {/* Manual Student Addition */}
                <div className="mt-3 pt-3 border-t border-slate-100">
                   <label className="block text-xs font-semibold text-slate-500 uppercase mb-2">{t('form.manual_student')}</label>
                   <div className="flex flex-col sm:flex-row gap-2">
                       <input 
                           type="text" 
                           placeholder={t('form.name_placeholder')}
                           className="flex-1 border border-slate-300 rounded-lg p-2 text-sm focus:ring-2 focus:ring-blue-500 outline-none"
                           value={newStudentName}
                           onChange={e => setNewStudentName(e.target.value)}
                       />
                       <input 
                           type="email" 
                           placeholder={t('form.email_placeholder')}
                           className="flex-1 border border-slate-300 rounded-lg p-2 text-sm focus:ring-2 focus:ring-blue-500 outline-none"
                           value={newStudentEmail}
                           onChange={e => setNewStudentEmail(e.target.value)}
                       />
                       <Button type="button" variant="secondary" size="sm" onClick={handleAddManualStudent} disabled={!newStudentName || !newStudentEmail}>
                           <PlusCircle size={16} className="mr-1"/> {t('form.add')}
                       </Button>
                   </div>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">GitHub URL</label>
                  <input 
                    type="url" 
                    className="w-full border border-slate-300 rounded-lg p-2.5 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    value={projectForm.githubUrl || ''}
                    onChange={e => setProjectForm({...projectForm, githubUrl: e.target.value})}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">Live Demo URL</label>
                  <input 
                    type="url" 
                    className="w-full border border-slate-300 rounded-lg p-2.5 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    value={projectForm.liveUrl || ''}
                    onChange={e => setProjectForm({...projectForm, liveUrl: e.target.value})}
                  />
                </div>
              </div>

              <div className="pt-4 flex justify-end">
                <Button type="submit" size="lg" className="gap-2">
                  <Save size={18} /> {t('form.save_project')}
                </Button>
              </div>
            </form>
          )}

          {activeTab === 'subject' && (
            <form onSubmit={handleSubjectSubmit} className="space-y-6 max-w-md mx-auto py-8">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">{t('form.subject_code')}</label>
                <input 
                  type="text" 
                  placeholder="např. WAP"
                  required
                  className="w-full border border-slate-300 rounded-lg p-2.5 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 uppercase"
                  value={subjectForm.code}
                  onChange={e => setSubjectForm({...subjectForm, code: e.target.value.toUpperCase()})}
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">{t('form.subject_name')}</label>
                <input 
                  type="text" 
                  placeholder="např. Webové aplikace"
                  required
                  className="w-full border border-slate-300 rounded-lg p-2.5 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  value={subjectForm.name}
                  onChange={e => setSubjectForm({...subjectForm, name: e.target.value})}
                />
              </div>
              <Button type="submit" className="w-full gap-2">
                <PlusCircle size={18} /> {t('admin.tab_subject')}
              </Button>
            </form>
          )}

          {activeTab === 'feedback' && (
             <div className="space-y-8">
               {projects.map(project => {
                 const projectFeedbacks = feedbacks.filter(f => f.projectId === project.id);
                 if (projectFeedbacks.length === 0) return null;

                 return (
                   <div key={project.id} className="border border-slate-200 rounded-xl overflow-hidden">
                     <div className="bg-slate-50 px-6 py-4 border-b border-slate-200">
                       <h3 className="font-bold text-lg text-slate-800">{project.title}</h3>
                       <span className="text-sm text-slate-500">{projectFeedbacks.length} {t('feedback.count_suffix')}</span>
                     </div>
                     <div className="divide-y divide-slate-100">
                       {projectFeedbacks.map(f => (
                         <div key={f.id} className="p-6">
                            <div className="flex items-center gap-3 mb-4 text-sm">
                                <div className="flex items-center gap-1 font-medium text-blue-700 bg-blue-50 px-2 py-1 rounded">
                                    <User size={14}/> {getStudentName(f.fromStudentId)}
                                </div>
                                <ArrowRight size={14} className="text-slate-300"/>
                                <div className="flex items-center gap-1 font-medium text-slate-700 bg-slate-100 px-2 py-1 rounded">
                                    <User size={14}/> {getStudentName(f.toStudentId)}
                                </div>
                                <span className="text-slate-400 ml-auto">{f.createdAt}</span>
                            </div>
                            
                            <div className="grid md:grid-cols-2 gap-4">
                                <div className="bg-green-50/50 p-3 rounded-lg border border-green-100">
                                    <h4 className="text-xs font-bold text-green-700 uppercase mb-2">{t('student.label_strengths')}</h4>
                                    <p className="text-sm text-slate-700">{f.strengths}</p>
                                </div>
                                <div className="bg-orange-50/50 p-3 rounded-lg border border-orange-100">
                                    <h4 className="text-xs font-bold text-orange-700 uppercase mb-2">{t('student.label_improvements')}</h4>
                                    <p className="text-sm text-slate-700">{f.improvements}</p>
                                </div>
                            </div>
                         </div>
                       ))}
                     </div>
                   </div>
                 );
               })}
               {feedbacks.length === 0 && (
                   <div className="text-center py-12 text-slate-500">
                       {t('feedback.no_feedback')}
                   </div>
               )}
             </div>
          )}
        </div>
      </div>
    </div>
  );
};