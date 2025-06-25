import React from 'react';

interface Team {
  team_number: number;
  nickname: string;
  score: number;
  reasoning: string;
}

interface ChatMessage {
  type: 'question' | 'answer';
  content: string;
  timestamp: Date;
}

interface ChatAnalysisPanelProps {
  chatHistory: ChatMessage[];
  currentQuestion: string;
  onQuestionChange: (question: string) => void;
  onQuestionSubmit: (question: string) => void;
  isLoading: boolean;
  hasInitialAnalysis: boolean;
  result: Team[] | null;
  chatEndRef: React.RefObject<HTMLDivElement>;
}

const ChatAnalysisPanel: React.FC<ChatAnalysisPanelProps> = ({
  chatHistory,
  currentQuestion,
  onQuestionChange,
  onQuestionSubmit,
  isLoading,
  hasInitialAnalysis,
  result,
  chatEndRef
}) => {
  const handleQuestionSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (currentQuestion.trim()) {
      onQuestionSubmit(currentQuestion.trim());
    }
  };

  return (
    <div className="flex-1 flex flex-col border-r border-gray-200">
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
              onChange={(e) => onQuestionChange(e.target.value)}
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
  );
};

export default ChatAnalysisPanel;