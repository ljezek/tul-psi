import { Project, Subject, Student, Feedback } from './types';

export const MOCK_SUBJECTS: Subject[] = [
  { id: 's1', code: 'TIP', name: 'Týmový inovační projekt' },
  { id: 's2', code: 'WAP', name: 'Webové aplikace' },
  { id: 's3', code: 'PIS', name: 'Podnikové informační systémy' },
  { id: 's4', code: 'ROB', name: 'Robotika' },
];

export const MOCK_STUDENTS: Student[] = [
  { id: 'u1', name: 'Jan Novák', email: 'jan.novak@tul.cz' }, // Mock logged in student
  { id: 'u2', name: 'Petr Svoboda', email: 'petr.svoboda@tul.cz' },
  { id: 'u3', name: 'Eva Dvořáková', email: 'eva.dvorakova@tul.cz' },
  { id: 'u4', name: 'Marie Černá', email: 'marie.cerna@tul.cz' },
  { id: 'u5', name: 'Tomáš Kučera', email: 'tomas.kucera@tul.cz' },
];

export const MOCK_PROJECTS: Project[] = [
  {
    id: 'p1',
    title: 'Autonomní vozítko pro skladové prostory',
    description: 'Návrh a implementace robota sledujícího čáru s detekcí překážek.',
    fullDescription: 'Tento projekt se zaměřuje na vytvoření nízkonákladového autonomního vozítka využívajícího platformu Arduino a senzory pro sledování čáry a ultrazvukové senzory pro detekci překážek. Cílem je optimalizovat logistiku v malých skladech. Součástí je i webové rozhraní pro monitoring stavu baterie a polohy.',
    academicYear: '2023/2024',
    subjectId: 's4',
    tags: ['C++', 'Arduino', 'IoT', 'Hardware'],
    authorIds: ['u1', 'u2'],
    githubUrl: 'https://github.com/example/robot',
    liveUrl: 'https://youtube.com/demo',
    imageUrl: 'https://picsum.photos/400/300?random=1'
  },
  {
    id: 'p2',
    title: 'Katalog Projektů FM TUL',
    description: 'Webová aplikace pro správu a prezentaci studentských prací.',
    fullDescription: 'Moderní webová platforma postavená na Reactu a TypeScriptu. Umožňuje studentům odevzdávat projekty, lektorům je hodnotit a veřejnosti prohlížet výsledky práce studentů FM. Aplikace využívá Tailwind CSS pro styling a je plně responzivní.',
    academicYear: '2023/2024',
    subjectId: 's2',
    tags: ['React', 'TypeScript', 'Tailwind', 'UX/UI'],
    authorIds: ['u3', 'u4'],
    githubUrl: 'https://github.com/example/catalog',
    liveUrl: 'https://katalog-fm.tul.cz',
    imageUrl: 'https://picsum.photos/400/300?random=2'
  },
  {
    id: 'p3',
    title: 'Analýza sentimentu v recenzích',
    description: 'Využití NLP pro klasifikaci zákaznických recenzí e-shopu.',
    fullDescription: 'Projekt zkoumá možnosti využití neuronových sítí pro automatickou detekci sentimentu (pozitivní/negativní/neutrální) v českém textu. Vytvořený model dosahuje přesnosti 85% na testovací sadě dat.',
    academicYear: '2022/2023',
    subjectId: 's1',
    tags: ['Python', 'AI', 'NLP', 'Data Science'],
    authorIds: ['u5', 'u1'],
    githubUrl: 'https://github.com/example/nlp',
    imageUrl: 'https://picsum.photos/400/300?random=3'
  }
];

export const MOCK_FEEDBACKS: Feedback[] = [
  {
    id: 'f1',
    projectId: 'p1',
    fromStudentId: 'u1',
    toStudentId: 'u2',
    strengths: 'Skvělá práce na hardwarové části, výborné znalosti elektroniky.',
    improvements: 'Dokumentace by mohla být detailnější, chybí schémata zapojení.',
    createdAt: '2024-05-20'
  }
];

// The currently logged in mock student
export const CURRENT_STUDENT_ID = 'u1';