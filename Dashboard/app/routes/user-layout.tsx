import { Outlet } from 'react-router';
import { PageLayout } from '../components/PageLayout';
import { ProtectedRoute } from '../components/ProtectedRoute';

export default function UserLayout() {
  return (
    <ProtectedRoute allowedRoles={['user']}>
      <PageLayout>
        <Outlet />
      </PageLayout>
    </ProtectedRoute>
  );
}
