import { Outlet } from 'react-router';
import { PageLayout } from '../components/PageLayout';
import { ProtectedRoute } from '../components/ProtectedRoute';

export default function ProtectedLayout() {
  return (
    <ProtectedRoute>
      <PageLayout>
        <Outlet />
      </PageLayout>
    </ProtectedRoute>
  );
}
