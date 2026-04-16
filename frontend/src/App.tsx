import { Suspense, lazy } from 'react';
import { createBrowserRouter, createRoutesFromElements, RouterProvider, Route } from 'react-router-dom';
import { LanguageProvider } from '@/contexts/LanguageContext';
import { AuthProvider } from '@/contexts/AuthContext';
import { MainLayout } from '@/layouts/MainLayout';
import { ProtectedRoute } from '@/components/ProtectedRoute';
import { UserRole } from '@/types';

// Pages - Lazy loaded
const Dashboard = lazy(() => import('@/pages/Dashboard').then(m => ({ default: m.Dashboard })));
const CourseList = lazy(() => import('@/pages/CourseList').then(m => ({ default: m.CourseList })));
const CourseDetailView = lazy(() => import('@/pages/CourseDetail').then(m => ({ default: m.CourseDetailView })));
const Login = lazy(() => import('@/pages/Login').then(m => ({ default: m.Login })));
const ProjectDetail = lazy(() => import('@/pages/ProjectDetail').then(m => ({ default: m.ProjectDetail })));
const Profile = lazy(() => import('@/pages/Profile').then(m => ({ default: m.Profile })));
const StudentHome = lazy(() => import('@/pages/student/StudentHome').then(m => ({ default: m.StudentHome })));
const CourseEvaluation = lazy(() => import('@/pages/student/CourseEvaluation').then(m => ({ default: m.CourseEvaluation })));
const Results = lazy(() => import('@/pages/student/Results').then(m => ({ default: m.Results })));
const LecturerHome = lazy(() => import('@/pages/lecturer/LecturerHome').then(m => ({ default: m.LecturerHome })));
const CourseProjects = lazy(() => import('@/pages/lecturer/CourseProjects').then(m => ({ default: m.CourseProjects })));
const ProjectEvaluation = lazy(() => import('@/pages/lecturer/ProjectEvaluation').then(m => ({ default: m.ProjectEvaluation })));
const ProjectResults = lazy(() => import('@/pages/lecturer/ProjectResults').then(m => ({ default: m.ProjectResults })));
const UserManagement = lazy(() => import('@/pages/admin/UserManagement').then(m => ({ default: m.UserManagement })));

// Loading component
const PageLoader = () => (
  <div className="flex items-center justify-center min-h-[400px]">
    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
  </div>
);

const router = createBrowserRouter(
  createRoutesFromElements(
    <Route element={<MainLayout />}>
      <Route path="/" element={<Suspense fallback={<PageLoader />}><Dashboard /></Suspense>} />
      <Route path="/courses" element={<Suspense fallback={<PageLoader />}><CourseList /></Suspense>} />
      <Route path="/courses/:id" element={<Suspense fallback={<PageLoader />}><CourseDetailView /></Suspense>} />
      <Route path="/login" element={<Suspense fallback={<PageLoader />}><Login /></Suspense>} />
      <Route path="/projects/:id" element={<Suspense fallback={<PageLoader />}><ProjectDetail /></Suspense>} />
      
      <Route element={<ProtectedRoute allowedRoles={[UserRole.STUDENT, UserRole.LECTURER, UserRole.ADMIN]} />}>
        <Route path="/profile" element={<Suspense fallback={<PageLoader />}><Profile /></Suspense>} />
      </Route>
      
      <Route element={<ProtectedRoute allowedRoles={[UserRole.STUDENT]} />}>
        <Route path="/student" element={<Suspense fallback={<PageLoader />}><StudentHome /></Suspense>} />
        <Route path="/student/project/:id/evaluate" element={<Suspense fallback={<PageLoader />}><CourseEvaluation /></Suspense>} />
        <Route path="/student/project/:id/results" element={<Suspense fallback={<PageLoader />}><Results /></Suspense>} />
      </Route>
      
      <Route element={<ProtectedRoute allowedRoles={[UserRole.LECTURER, UserRole.ADMIN]} />}>
        <Route path="/lecturer" element={<Suspense fallback={<PageLoader />}><LecturerHome /></Suspense>} />
        <Route path="/lecturer/course/:id" element={<Suspense fallback={<PageLoader />}><CourseProjects /></Suspense>} />
        <Route path="/lecturer/project/:id/evaluate" element={<Suspense fallback={<PageLoader />}><ProjectEvaluation /></Suspense>} />
        <Route path="/lecturer/project/:id/results" element={<Suspense fallback={<PageLoader />}><ProjectResults /></Suspense>} />
      </Route>
      <Route element={<ProtectedRoute allowedRoles={[UserRole.ADMIN]} />}>
        <Route path="/admin/users" element={<Suspense fallback={<PageLoader />}><UserManagement /></Suspense>} />
      </Route>

    </Route>
  )
);

function App() {
  return (
    <LanguageProvider>
      <AuthProvider>
        <RouterProvider router={router} />
      </AuthProvider>
    </LanguageProvider>
  );
}

export default App;
