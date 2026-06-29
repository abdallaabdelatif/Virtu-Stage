import axios from 'axios';

export function getApiErrorMessage(
  error: unknown,
  fallback = 'Something went wrong. Please try again.',
) {
  if (!axios.isAxiosError(error)) {
    return error instanceof Error ? error.message : fallback;
  }

  const detail = error.response?.data?.detail;
  if (typeof detail === 'string') return detail;

  if (Array.isArray(detail)) {
    const messages = detail
      .map((item) => (typeof item?.msg === 'string' ? item.msg : null))
      .filter(Boolean);
    if (messages.length) return messages.join(', ');
  }

  if (error.code === 'ECONNABORTED') {
    return 'The server took too long to respond.';
  }
  if (!error.response) {
    return 'Unable to connect to the server.';
  }
  return fallback;
}
