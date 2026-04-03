export interface LoadingSpinnerProps {
  className?: string;
  label?: string;
}

export const LoadingSpinner = ({
  className = '',
  label = 'Loading…',
}: LoadingSpinnerProps) => {
  return (
    <div
      className={`flex justify-center items-center ${className}`}
      role="status"
      aria-live="polite"
    >
      <div
        className="animate-spin rounded-full border-4 border-slate-200 border-t-tul-blue h-8 w-8"
        aria-hidden="true"
      ></div>
      <span className="sr-only">{label}</span>
    </div>
  );
};
