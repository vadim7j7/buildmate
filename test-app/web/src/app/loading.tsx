/**
 * Loading state shown while the page is fetching data.
 */
export default function Loading() {
  return (
    <main className="min-h-screen bg-gray-100 py-12">
      <div className="max-w-lg mx-auto">
        <h1 className="text-4xl font-thin text-center text-gray-800 mb-8">
          todos
        </h1>

        <div className="bg-white rounded-lg shadow-lg overflow-hidden">
          <div className="px-4 py-4 border-b border-gray-200">
            <div className="h-6 bg-gray-200 rounded animate-pulse" />
          </div>

          <div className="divide-y divide-gray-200">
            {[1, 2, 3].map((i) => (
              <div key={i} className="flex items-center gap-3 px-4 py-3">
                <div className="h-5 w-5 rounded bg-gray-200 animate-pulse" />
                <div className="flex-1 h-5 bg-gray-200 rounded animate-pulse" />
              </div>
            ))}
          </div>

          <div className="px-4 py-3 border-t border-gray-200">
            <div className="h-4 w-24 bg-gray-200 rounded animate-pulse" />
          </div>
        </div>
      </div>
    </main>
  );
}
