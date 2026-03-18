import { ShieldOff } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

interface AccessDeniedProps {
  message?: string;
  showBack?: boolean;
}

export function AccessDenied({
  message = 'You do not have permission to access this resource.',
  showBack = true,
}: AccessDeniedProps) {
  const navigate = useNavigate();

  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] px-6 text-center">
      <div className="w-16 h-16 rounded-2xl bg-red-50 flex items-center justify-center mb-5">
        <ShieldOff className="w-7 h-7 text-red-500" />
      </div>
      <p className="text-5xl font-bold text-gray-100 mb-2 select-none">403</p>
      <h1 className="text-lg font-semibold text-gray-800">Access Denied</h1>
      <p className="text-sm text-gray-400 mt-1.5 max-w-sm">{message}</p>
      {showBack && (
        <button
          onClick={() => navigate(-1)}
          className="mt-6 px-4 py-2 rounded-xl border border-gray-200 text-sm font-medium text-gray-600 hover:bg-gray-50 transition-colors"
        >
          Go Back
        </button>
      )}
    </div>
  );
}
