import { useEffect } from 'react';
import { useNavigate, useParams } from 'react-router';

export default function SessionDetailRedirect() {
  const { id } = useParams();
  const navigate = useNavigate();

  useEffect(() => {
    if (id) {
      navigate(`/session-analytics/${id}`, { replace: true });
    } else {
      navigate('/sessions', { replace: true });
    }
  }, [id, navigate]);

  return null;
}
