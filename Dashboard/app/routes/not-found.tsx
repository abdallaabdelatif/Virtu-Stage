import { useNavigate } from 'react-router';
import { useAuth } from '../context/AuthContext';
import { PageLayout } from '../components/PageLayout';
import { Button } from '../components/Button';

export default function NotFound() {
  const navigate = useNavigate();
  const { isAuthenticated } = useAuth();

  const content = (
    <div className="flex flex-col items-center justify-center min-h-[70vh] text-center">
      <h1 className="text-8xl font-black text-transparent bg-clip-text bg-gradient-to-br from-brand to-[#d9d9d9] mb-4">
        404
      </h1>
      <h2 className="text-3xl font-bold text-white mb-4">Page Not Found</h2>
      <p className="text-[#d9d9d9] max-w-md mb-8">
        The page you are looking for doesn't exist or has been moved.
      </p>

      <Button
        onClick={() => navigate(isAuthenticated ? '/dashboard' : '/')}
        variant="primary"
      >
        {isAuthenticated ? 'Go to Dashboard' : 'Go to Login'}
      </Button>
    </div>
  );

  if (isAuthenticated) {
    return <PageLayout>{content}</PageLayout>;
  }

  return (
    <div className="min-h-screen bg-[#0a0c10] flex items-center justify-center px-4">
      {content}
    </div>
  );
}
