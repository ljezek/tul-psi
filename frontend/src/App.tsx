import { createBrowserRouter, createRoutesFromElements, RouterProvider, Route } from 'react-router-dom';
import { LanguageProvider } from '@/contexts/LanguageContext';
import { AuthProvider } from '@/contexts/AuthContext';
import { MainLayout } from '@/layouts/MainLayout';
import { ProtectedRoute } from '@/components/ProtectedRoute';
import { UserRole } from '@/types';

// Pages
import { Dashboard } from '@/pages/Dashboard';
import { CourseList } from '@/pages/CourseList';
import { CourseDetailView } from '@/pages/CourseDetail';
import { Login } from '@/pages/Login';
import { ProjectDetail } from '@/pages/ProjectDetail';
import { Profile } from '@/pages/Profile';
import { StudentHome } from '@/pages/student/StudentHome';
import { CourseEvaluation } from '@/pages/student/CourseEvaluation';
import { Results } from '@/pages/student/Results';
import { LecturerHome } from '@/pages/lecturer/LecturerHome';
import { CourseProjects } from '@/pages/lecturer/CourseProjects';
import { ProjectEvaluation } from '@/pages/lecturer/ProjectEvaluation';

const router = createBrowserRouter(
  createRoutesFromElements(
    <Route element={<MainLayout />}>
      <Route path="/" element={<Dashboard />} />
      <Route path="/courses" element={<CourseList />} />
      <Route path="/courses/:id" element={<CourseDetailView />} />
      <Route path="/login" element={<Login />} />
      <Route path="/projects/:id" element={<ProjectDetail />} />
      
      <Route element={<ProtectedRoute allowedRoles={[UserRole.STUDENT, UserRole.LECTURER, UserRole.ADMIN]} />}>
        <Route path="/profile" element={<Profile />} />
      </Route>
      
      <Route element={<ProtectedRoute allowedRoles={[UserRole.STUDENT]} />}>
        <Route path="/student" element={<StudentHome />} />
        <Route path="/student/project/:id/evaluate" element={<CourseEvaluation />} />
        <Route path="/student/project/:id/results" element={<Results />} />
      </Route>
      
      <Route element={<ProtectedRoute allowedRoles={[UserRole.LECTURER, UserRole.ADMIN]} />}>
        <Route path="/lecturer" element={<LecturerHome />} />
        <Route path="/lecturer/course/:id" element={<CourseProjects />} />
        <Route path="/lecturer/project/:id/evaluate" element={<ProjectEvaluation />} />
        <Route path="/lecturer/project/:id/results" element={<Results />} />
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
