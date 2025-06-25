import React, { useState, useRef, useEffect } from "react";
import ModalHeader from './ModalHeader';
import TeamSelectionPanel from './TeamSelectionPanel';
import ChatAnalysisPanel from './ChatAnalysisPanel';
import StatisticalComparisonPanel from './StatisticalComparisonPanel';
import { useTeamComparisonAPI } from '../hooks/useTeamComparisonAPI';

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

interface ComparisonData {
  teams: Array<{
    team_number: number;
    nickname: string;
    stats: Record<string, number>;
  }>;
  metrics: string[];
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
  const [comparisonData, setComparisonData] = useState<ComparisonData | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [hasInitialAnalysis, setHasInitialAnalysis] = useState(false);
  const chatEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [chatHistory]);

  // API integration hook
  const { performAnalysis: performAPIAnalysis } = useTeamComparisonAPI({
    setResult,
    setComparisonData,
    setChatHistory,
    setIsLoading,
    setHasInitialAnalysis
  });

  const performAnalysis = async (question?: string) => {
    const simplePriorities = prioritiesMap[pickPosition].map((p) => ({
      id: p.id,
      weight: p.weight,
      reason: p.reason || null,
    }));
    
    await performAPIAnalysis(
      teamNumbers,
      datasetPath,
      yourTeamNumber,
      pickPosition,
      simplePriorities,
      chatHistory,
      question
    );
  };

  const handleInitialAnalysis = () => {
    performAnalysis();
  };

  const handleQuestionSubmit = (question: string) => {
    performAnalysis(question);
    setCurrentQuestion("");
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
    setComparisonData(null);
    setHasInitialAnalysis(false);
  };

  const handlePickPositionChange = (position: "first" | "second" | "third") => {
    setPickPosition(position);
    resetAnalysis();
  };


  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg w-full max-w-7xl h-5/6 flex flex-col">
        <ModalHeader onClose={onClose} />
        
        <div className="flex-1 flex min-h-0">
          <TeamSelectionPanel
            teamNumbers={teamNumbers}
            pickPosition={pickPosition}
            onPickPositionChange={handlePickPositionChange}
            result={result}
            hasInitialAnalysis={hasInitialAnalysis}
            isLoading={isLoading}
            onStartAnalysis={handleInitialAnalysis}
            onApply={apply}
            onReset={resetAnalysis}
            onClearChat={() => setChatHistory(chatHistory.slice(0, 1))}
            chatHistoryLength={chatHistory.length}
          />
          
          <ChatAnalysisPanel
            chatHistory={chatHistory}
            currentQuestion={currentQuestion}
            onQuestionChange={setCurrentQuestion}
            onQuestionSubmit={handleQuestionSubmit}
            isLoading={isLoading}
            hasInitialAnalysis={hasInitialAnalysis}
            result={result}
            chatEndRef={chatEndRef}
          />
          
          <StatisticalComparisonPanel
            comparisonData={comparisonData}
          />
        </div>
      </div>
    </div>
  );
};

export default TeamComparisonModal;
