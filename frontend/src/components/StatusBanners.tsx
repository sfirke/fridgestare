type StatusBannersProps = {
  statusMessage: string;
  errorMessage: string;
};

export function StatusBanners({ statusMessage, errorMessage }: StatusBannersProps) {
  return (
    <>
      {statusMessage ? (
        <p className="status-banner" role="status">
          {statusMessage}
        </p>
      ) : null}
      {errorMessage ? (
        <p className="error-banner" role="alert">
          {errorMessage}
        </p>
      ) : null}
    </>
  );
}
