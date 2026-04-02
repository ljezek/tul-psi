export interface LoadingSpinnerProps {
  className?: string;
}

export const LoadingSpinner = ({ className = '' }: LoadingSpinnerProps) => {
  return (
    <div className={`flex justify-center items-center ${className}`}>
      <div className="animate-spin rounded-full border-4 border-slate-200 border-t-tul-blue h-8 w-8"></div>
    </div>
  );
};
