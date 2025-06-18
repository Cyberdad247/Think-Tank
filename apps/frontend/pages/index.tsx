import { useState, useRef, FormEvent } from 'react';

interface VoteTally {
  [key: string]: number;
}

const HomePage: React.FC = () => {
  const [query, setQuery] = useState('');
  const [reasoningTrace, setReasoningTrace] = useState<string[]>([]);
  const [finalAnswer, setFinalAnswer] = useState<string | null>(null);
  const [voteTally, setVoteTally] = useState<VoteTally | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const eventSourceRef = useRef<EventSource | null>(null);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;

    // Reset all states for a new query
    setReasoningTrace([]);
    setFinalAnswer(null);
    setVoteTally(null);
    setIsLoading(true);

    // Establish SSE connection to the debate stream endpoint
    eventSourceRef.current = new EventSource(`/api/debate/stream?query=${encodeURIComponent(query)}`);

    eventSourceRef.current.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === 'progress') {
          setReasoningTrace((prev) => [...prev, data.payload.trace_step]);
        } else if (data.type === 'final') {
          setFinalAnswer(data.payload.answer);
          setVoteTally(data.payload.votes);
          setReasoningTrace((prev) => [...prev, data.payload.full_trace]); // Append full trace at the end
          setIsLoading(false); // Debate concluded
          eventSourceRef.current?.close();
        }
      } catch (error) {
        console.error('Failed to parse SSE message or unknown event type:', error);
      }
    };

    eventSourceRef.current.onerror = (error) => {
      console.error('EventSource failed:', error);
      eventSourceRef.current?.close();
      setIsLoading(false);
    };

    eventSourceRef.current.onopen = () => {
      console.log('SSE connection opened for debate stream.');
    };
  };

  return (
    <div className="min-h-screen bg-gray-100 flex items-center justify-center p-4">
      <div className="w-full max-w-2xl bg-white rounded-lg shadow-md p-6">
        <h1 className="text-2xl font-bold text-center text-gray-800 mb-6">Think-Tank Debate</h1>

        <form onSubmit={handleSubmit} className="flex flex-col space-y-4">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Enter your debate query..."
            className="w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            disabled={isLoading}
          />
          <button
            type="submit"
            className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50"
            disabled={isLoading}
          >
            {isLoading ? 'Debating...' : 'Start Debate'}
          </button>
        </form>

        <div className="mt-6 p-4 bg-gray-50 border border-gray-200 rounded-md h-96 overflow-y-auto">
          {isLoading && reasoningTrace.length === 0 && finalAnswer === null && (
            <p className="text-gray-700">Waiting for debate to start...</p>
          )}

          {reasoningTrace.length > 0 && (
            <div className="mb-4">
              <h2 className="text-xl font-semibold text-gray-800 mb-2">Reasoning Trace:</h2>
              {reasoningTrace.map((step, index) => (
                <p key={index} className="text-gray-700 whitespace-pre-wrap mb-1">
                  {step}
                </p>
              ))}
            </div>
          )}

          {finalAnswer && (
            <div className="mb-4">
              <h2 className="text-xl font-semibold text-gray-800 mb-2">Final Answer:</h2>
              <p className="text-gray-900 whitespace-pre-wrap font-medium">{finalAnswer}</p>
            </div>
          )}

          {voteTally && (
            <div>
              <h2 className="text-xl font-semibold text-gray-800 mb-2">Vote Tally:</h2>
              <ul className="list-disc list-inside text-gray-700">
                {Object.entries(voteTally).map(([option, count]) => (
                  <li key={option}>
                    {option}: {count} votes
                  </li>
                ))}
              </ul>
            </div>
          )}

          {!isLoading && reasoningTrace.length === 0 && finalAnswer === null && (
            <p className="text-gray-700">Enter a query to start a debate.</p>
          )}
        </div>
      </div>
    </div>
  );
};

export default HomePage;