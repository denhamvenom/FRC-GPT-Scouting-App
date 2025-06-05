import React, { useState, useRef, useEffect } from "react";

interface Team {
  team_number: number;
  nickname: string;
  score: number;
  reasoning: string;
}

interface MetricPriority {
  id: string;
  weight: number;
  reason?: string | null;
}

interface PrioritiesMap {
  first: MetricPriority[];
  second: MetricPriority[];
  third: MetricPriority[];
}

interface ChatMessage {
  type: 'question' | 'answer';
  content: string;
  timestamp: Date;
}

interface TeamComparisonModalProps {
  isOpen: boolean;
  onClose: () => void;
  teamNumbers: number[];
  datasetPath: string;
  yourTeamNumber: number;
  prioritiesMap: PrioritiesMap;
  onApply: (teams: Team[]) => void;
}

const TeamComparisonModal: React.FC<TeamComparisonModalProps> = ({
  isOpen,
  onClose,
  teamNumbers,
  datasetPath,
  yourTeamNumber,
  prioritiesMap,
  onApply,
}) => {
  const [pickPosition, setPickPosition] = useState<
    "first" | "second" | "third"
  >("first");
  const [currentQuestion, setCurrentQuestion] = useState("");
  const [chatHistory, setChatHistory] = useState<ChatMessage[]>([]);
  const [result, setResult] = useState<Team[] | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [hasInitialAnalysis, setHasInitialAnalysis] = useState(false);
  const chatEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [chatHistory]);

  const performAnalysis = async (question?: string) => {
    setIsLoading(true);
    try {
      const simplePriorities = prioritiesMap[pickPosition].map((p) => ({
        id: p.id,
        weight: p.weight,
        reason: p.reason || null,
      }));
      
      // Prepare chat history for API (only include previous messages, not the current question)
      const chatHistoryForAPI = question ? chatHistory.map(msg => ({
        type: msg.type,
        content: msg.content,
        timestamp: msg.timestamp.toISOString()
      })) : undefined;
      
      const response = await fetch(
        "http://localhost:8000/api/picklist/compare-teams",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            unified_dataset_path: datasetPath,
            team_numbers: teamNumbers,
            your_team_number: yourTeamNumber,
            pick_position: pickPosition,
            priorities: simplePriorities,
            question: question || undefined,
            chat_history: chatHistoryForAPI,
          }),
        },
      );
      
      if (!response.ok) {
        const err = await response.json();
        throw new Error(err.detail || "Failed to compare teams");
      }
      
      const data = await response.json();
      
      console.log('Team comparison response:', data); // Debug logging
      
      // Only update result if we got new team rankings (initial analysis)
      if (data.ordered_teams) {
        setResult(data.ordered_teams);
      }
      
      if (data.summary) {
        if (question) {
          setChatHistory(prev => [
            ...prev,
            { type: 'question', content: question, timestamp: new Date() },
            { type: 'answer', content: data.summary, timestamp: new Date() }
          ]);
        } else {
          setChatHistory([
            { type: 'answer', content: data.summary, timestamp: new Date() }
          ]);
        }
      } else {
        // If no summary, add a fallback message
        const fallbackMessage = question 
          ? "Analysis completed but no detailed response was provided."
          : "Teams have been ranked, but no analysis summary was provided.";
        
        if (question) {
          setChatHistory(prev => [
            ...prev,
            { type: 'question', content: question, timestamp: new Date() },
            { type: 'answer', content: fallbackMessage, timestamp: new Date() }
          ]);
        } else {
          setChatHistory([
            { type: 'answer', content: fallbackMessage, timestamp: new Date() }
          ]);
        }
      }
      
      setHasInitialAnalysis(true);
    } catch (err) {
      console.error("Error comparing teams:", err);
      const errorMessage = err instanceof Error ? err.message : "An error occurred";
      setChatHistory(prev => [
        ...prev,
        { type: 'answer', content: `Error: ${errorMessage}`, timestamp: new Date() }
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleInitialAnalysis = () => {
    performAnalysis();
  };

  const handleQuestionSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (currentQuestion.trim()) {
      performAnalysis(currentQuestion.trim());
      setCurrentQuestion("");
    }
  };

  const apply = () => {
    if (result) {
      onApply(result);
      onClose();
    }
  };

  const resetAnalysis = () => {
    setChatHistory([]);
    setResult(null);
    setHasInitialAnalysis(false);
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg w-full max-w-6xl h-5/6 flex flex-col">
        {/* Header */}
        <div className="border-b border-gray-200 p-4 flex justify-between items-center">
          <h3 className="text-xl font-semibold">Team Comparison & Re-Ranking</h3>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 text-2xl"
          >
            ×
          </button>
        </div>

        {/* Main Content */}
        <div className="flex-1 flex min-h-0">
          {/* Left Panel - Team Selection & Controls */}
          <div className="w-1/3 border-r border-gray-200 p-4 flex flex-col">
            <div className="space-y-4">
              {/* Selected Teams */}
              <div>
                <h4 className="font-medium text-gray-900 mb-2">Selected Teams</h4>
                <div className="space-y-2">
                  {teamNumbers.map((teamNum, index) => (
                    <div
                      key={teamNum}
                      className="bg-blue-50 border border-blue-200 rounded p-2 flex items-center justify-between"
                    >
                      <span className="font-medium">Team {teamNum}</span>
                      {result && (
                        <span className="text-sm text-gray-600">
                          #{result.findIndex(t => t.team_number === teamNum) + 1}
                        </span>
                      )}
                    </div>
                  ))}
                </div>
              </div>

              {/* Pick Strategy */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Pick Strategy
                </label>
                <select
                  value={pickPosition}
                  onChange={(e) => {
                    setPickPosition(e.target.value as "first" | "second" | "third");
                    resetAnalysis();
                  }}
                  className="w-full border border-gray-300 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="first">1st Pick Strategy</option>
                  <option value="second">2nd Pick Strategy</option>
                  <option value="third">3rd Pick Strategy</option>
                </select>
              </div>

              {/* Initial Analysis Button */}
              {!hasInitialAnalysis && (
                <button
                  onClick={handleInitialAnalysis}
                  disabled={isLoading}
                  className="w-full bg-blue-600 text-white py-2 px-4 rounded hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isLoading ? "Analyzing..." : "Start Analysis"}
                </button>
              )}

              {/* Re-Ranking Results */}
              {result && (
                <div className="border-t border-gray-200 pt-4">
                  <h4 className="font-medium text-gray-900 mb-2">Suggested Ranking</h4>
                  <ol className="space-y-1">
                    {result.map((team, index) => (
                      <li
                        key={team.team_number}
                        className="flex items-center justify-between bg-gray-50 rounded p-2"
                      >
                        <span className="font-medium">
                          {index + 1}. Team {team.team_number}
                        </span>
                        {team.nickname && (
                          <span className="text-sm text-gray-600 truncate ml-2">
                            {team.nickname}
                          </span>
                        )}
                      </li>
                    ))}
                  </ol>
                </div>
              )}

              {/* Apply Button */}
              {result && (
                <div className="border-t border-gray-200 pt-4 mt-auto space-y-2">
                  <button
                    onClick={apply}
                    className="w-full bg-green-600 text-white py-2 px-4 rounded hover:bg-green-700 font-medium"
                  >
                    Apply New Ranking
                  </button>
                  <button
                    onClick={resetAnalysis}
                    className="w-full bg-gray-300 text-gray-700 py-2 px-4 rounded hover:bg-gray-400"
                  >
                    Reset Analysis
                  </button>
                  {chatHistory.length > 1 && (
                    <button
                      onClick={() => setChatHistory(chatHistory.slice(0, 1))}
                      className="w-full bg-yellow-500 text-white py-1 px-4 rounded hover:bg-yellow-600 text-sm"
                    >
                      Clear Chat (Keep Initial Analysis)
                    </button>
                  )}
                </div>
              )}
            </div>
          </div>

          {/* Right Panel - Chat Analysis */}
          <div className="flex-1 flex flex-col">
            {/* Chat Header */}
            <div className="border-b border-gray-200 p-3">
              <h4 className="font-medium text-gray-900">GPT Analysis</h4>
              <p className="text-sm text-gray-600">Comparative team analysis and insights</p>
            </div>

            {/* Chat History */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-gray-50">
              {chatHistory.length === 0 && !isLoading && !hasInitialAnalysis && (
                <div className="text-center text-gray-500 mt-8">
                  <div className="bg-white rounded-lg p-6 shadow-sm border">
                    <p className="font-medium">Ready for Analysis</p>
                    <p className="text-sm mt-2">
                      Click "Start Analysis" to get GPT's comparative assessment of the selected teams
                    </p>
                  </div>
                </div>
              )}

              {chatHistory.length === 0 && hasInitialAnalysis && !isLoading && (
                <div className="text-center text-red-500 mt-8">
                  <div className="bg-white rounded-lg p-6 shadow-sm border border-red-200">
                    <p className="font-medium">No Analysis Response</p>
                    <p className="text-sm mt-2">
                      Analysis completed but no response received. Try again.
                    </p>
                  </div>
                </div>
              )}
              
              {chatHistory.map((message, index) => (
                <div
                  key={index}
                  className={`flex ${
                    message.type === 'question' ? 'justify-end' : 'justify-start'
                  }`}
                >
                  <div
                    className={`max-w-3xl rounded-lg p-4 shadow-sm ${
                      message.type === 'question'
                        ? 'bg-blue-600 text-white'
                        : 'bg-white text-gray-900 border'
                    }`}
                  >
                    {message.type === 'answer' ? (
                      <div>
                        <div className="font-medium text-sm text-gray-600 mb-2">GPT Analysis:</div>
                        <div className="whitespace-pre-wrap leading-relaxed">{message.content}</div>
                      </div>
                    ) : (
                      <div>
                        <div className="font-medium text-xs text-blue-100 mb-1">Your Question:</div>
                        <div>{message.content}</div>
                      </div>
                    )}
                    <div
                      className={`text-xs mt-2 pt-2 border-t ${
                        message.type === 'question' 
                          ? 'text-blue-100 border-blue-500' 
                          : 'text-gray-400 border-gray-200'
                      }`}
                    >
                      {message.timestamp.toLocaleTimeString()}
                    </div>
                  </div>
                </div>
              ))}
              
              {isLoading && (
                <div className="flex justify-start">
                  <div className="bg-white rounded-lg p-4 shadow-sm border">
                    <div className="flex items-center space-x-3">
                      <div className="animate-spin h-5 w-5 border-2 border-blue-600 border-t-transparent rounded-full"></div>
                      <div>
                        <div className="font-medium text-gray-900">GPT is analyzing...</div>
                        <div className="text-sm text-gray-600">Comparing teams and generating insights</div>
                      </div>
                    </div>
                  </div>
                </div>
              )}
              
              <div ref={chatEndRef} />
            </div>

            {/* Question Input - Always show if we have results */}
            {result && (
              <div className="border-t border-gray-200 p-4 bg-white">
                <form onSubmit={handleQuestionSubmit} className="flex space-x-2">
                  <input
                    type="text"
                    value={currentQuestion}
                    onChange={(e) => setCurrentQuestion(e.target.value)}
                    placeholder="Ask a follow-up question about these teams..."
                    className="flex-1 border border-gray-300 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    disabled={isLoading}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' && !e.shiftKey) {
                        e.preventDefault();
                        handleQuestionSubmit(e);
                      }
                    }}
                  />
                  <button
                    type="submit"
                    disabled={isLoading || !currentQuestion.trim()}
                    className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-1"
                  >
                    {isLoading ? (
                      <>
                        <div className="animate-spin h-4 w-4 border-2 border-white border-t-transparent rounded-full"></div>
                        <span>Asking...</span>
                      </>
                    ) : (
                      <span>Ask</span>
                    )}
                  </button>
                </form>
                <div className="text-xs text-gray-500 mt-1">
                  Press Enter to send • {chatHistory.length} messages in conversation
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default TeamComparisonModal;
