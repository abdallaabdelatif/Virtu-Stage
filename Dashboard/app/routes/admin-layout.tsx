import { Outlet } from 'react-router';
import { PageLayout } from '../components/PageLayout';
import { ProtectedRoute } from '../components/ProtectedRoute';

export default function AdminLayout() {
  return (
    <ProtectedRoute allowedRoles={['admin']}>
      <PageLayout>
        <Outlet />
      </PageLayout>
    </ProtectedRoute>
  );
}
