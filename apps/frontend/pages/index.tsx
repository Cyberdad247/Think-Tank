import { useState, useRef, FormEvent, useEffect } from 'react';

interface VoteTally {
  [key: string]: number;
}

const HomePage: React.FC = () => {
  const [query, setQuery] = useState('');
  const [reasoningTrace, setReasoningTrace] = useState<string[]>([]);
  const [finalAnswer, setFinalAnswer] = useState<string | null>(null);
  const [voteTally, setVoteTally] = useState<VoteTally | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [sseError, setSseError] = useState<string | null>(null);
  const eventSourceRef = useRef<EventSource | null>(null);

  useEffect(() => {
    if (!isLoading && finalAnswer === null && reasoningTrace.length > 0 && sseError === null) {
      setSseError("The debate concluded unexpectedly. No final answer was provided.");
    }
  }, [isLoading, finalAnswer, sseError, reasoningTrace]);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;

    setReasoningTrace([]);
    setFinalAnswer(null);
    setVoteTally(null);
    setSseError(null);
    setIsLoading(true);

    if (eventSourceRef.current) {
      eventSourceRef.current.close();
    }

    eventSourceRef.current = new EventSource(`/api/debate/stream?query=${encodeURIComponent(query)}`);

    eventSourceRef.current.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        // Assuming data.type and data.payload are always present as per your example
        if (data.type === 'progress') {
          setReasoningTrace((prev) => [...prev, data.payload.trace_step]);
        } else if (data.type === 'final') {
          setFinalAnswer(data.payload.answer);
          setVoteTally(data.payload.votes);
          // If full_trace is part of the final payload, append it
          if (data.payload.full_trace) {
            setReasoningTrace((prev) => [...prev, data.payload.full_trace]);
          }
          setIsLoading(false);
          eventSourceRef.current?.close();
        } else if (data.type === 'error') { // Handle explicit error messages from backend stream
          setSseError(data.payload.message || "An error occurred during the debate process.");
          setIsLoading(false);
          eventSourceRef.current?.close();
        }
      } catch (error) {
        console.error('Failed to parse SSE message or unknown event type:', error);
        setSseError("Error processing data from the server.");
        setIsLoading(false);
        eventSourceRef.current?.close();
      }
    };

    eventSourceRef.current.onerror = (error) => {
      console.error('EventSource failed:', error);
      // Check if it's not already a more specific error from onmessage
      if (!sseError) {
        setSseError("Connection to debate stream failed. Please try again later.");
      }
      setIsLoading(false);
      eventSourceRef.current?.close();
    };

    eventSourceRef.current.onopen = () => {
      console.log('SSE connection opened for debate stream.');
      setSseError(null); // Clear any previous connection errors on successful open
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

        {sseError && (
          <div className="mt-4 p-3 bg-red-100 border border-red-400 text-red-700 rounded-md">
            <p>{sseError}</p>
          </div>
        )}

        <div className="mt-6 p-4 bg-gray-50 border border-gray-200 rounded-md h-96 overflow-y-auto">
          {isLoading && reasoningTrace.length === 0 && !finalAnswer && !sseError && (
            <p className="text-gray-700">Waiting for debate to start...</p>
          )}
          {isLoading && sseError && ( /* Show a message if loading but an error has occurred */
            <p className="text-gray-700">Attempting to process debate, but an issue occurred...</p>
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

          {/* Initial state message or if debate ended without error but also without answer and trace */}
          {!isLoading && !finalAnswer && reasoningTrace.length === 0 && !sseError && (
            <p className="text-gray-700">Enter a query to start a debate.</p>
          )}
        </div>
      </div>
    </div>
  );
};

export default HomePage;