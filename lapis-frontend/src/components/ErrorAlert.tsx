interface ErrorAlertProps {
  title?: string;
  message: string;
  onClose?: () => void;
}

export default function ErrorAlert({ title = 'Error', message, onClose }: ErrorAlertProps) {
  return (
    <div className="rounded-lg border border-destructive/50 bg-destructive/10 p-4">
      <div className="flex items-start gap-3">
        <svg
          className="h-5 w-5 text-destructive mt-0.5"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
          />
        </svg>
        <div className="flex-1">
          <h3 className="text-sm font-medium text-destructive">{title}</h3>
          <p className="mt-1 text-sm text-destructive/80">{message}</p>
        </div>
        {onClose && (
          <button
            onClick={onClose}
            className="text-destructive/50 hover:text-destructive"
          >
            <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        )}
      </div>
    </div>
  );
}