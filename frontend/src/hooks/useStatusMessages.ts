import { useCallback, useState } from 'react';

export type StatusMessages = {
  statusMessage: string;
  errorMessage: string;
  reset: () => void;
  setStatus: (message: string) => void;
  setError: (message: string) => void;
  /**
   * Run an async action, reporting its outcome in the banners.
   *
   * Every handler in this app repeated the same reset / try / setStatus / catch /
   * setError block; centralizing it keeps error reporting consistent and makes the
   * handlers read as what they actually do.
   */
  run: <T>(action: () => Promise<T>, options: RunOptions) => Promise<T | undefined>;
};

type RunOptions = {
  success?: string;
  failure: string;
};

export function useStatusMessages(): StatusMessages {
  const [statusMessage, setStatusMessage] = useState('');
  const [errorMessage, setErrorMessage] = useState('');

  const reset = useCallback(() => {
    setStatusMessage('');
    setErrorMessage('');
  }, []);

  const setStatus = useCallback((message: string) => {
    setErrorMessage('');
    setStatusMessage(message);
  }, []);

  const setError = useCallback((message: string) => {
    setStatusMessage('');
    setErrorMessage(message);
  }, []);

  const run = useCallback(
    async <T,>(action: () => Promise<T>, options: RunOptions): Promise<T | undefined> => {
      reset();
      try {
        const result = await action();
        if (options.success) {
          setStatusMessage(options.success);
        }
        return result;
      } catch (error) {
        setErrorMessage(error instanceof Error ? error.message : options.failure);
        return undefined;
      }
    },
    [reset],
  );

  return { statusMessage, errorMessage, reset, setStatus, setError, run };
}
