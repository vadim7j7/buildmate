'use client';

type ErrorProps = {
  error: Error & { digest?: string };
  reset: () => void;
};

/**
 * Error boundary for the todo application.
 */
export default function Error({ error, reset }: ErrorProps) {
  return (
    <main className="min-h-screen bg-gray-100 py-12">
      <div className="max-w-lg mx-auto">
        <h1 className="text-4xl font-thin text-center text-gray-800 mb-8">
          todos
        </h1>

        <div className="bg-white rounded-lg shadow-lg overflow-hidden p-8">
          <div className="text-center">
            <div className="inline-flex items-center justify-center w-12 h-12 rounded-full bg-red-100 mb-4">
              <svg
                xmlns="http://www.w3.org/2000/svg"
                className="h-6 w-6 text-red-600"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
                />
              </svg>
            </div>

            <h2 className="text-xl font-medium text-gray-900 mb-2">
              Something went wrong
            </h2>

            <p className="text-gray-500 mb-6">{error.message}</p>

            <button
              onClick={reset}
              className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
            >
              Try again
            </button>
          </div>
        </div>
      </div>
    </main>
  );
}
