interface ErrorStateProps {
  message: string;
}

export const ErrorState = ({ message }: ErrorStateProps) => (
  <div className="rounded-2xl border border-rose-200 bg-rose-50 px-4 py-10 text-center text-rose-700">{message}</div>
);
