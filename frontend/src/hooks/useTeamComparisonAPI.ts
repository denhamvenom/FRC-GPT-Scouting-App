import { useState } from 'react';

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

interface UseTeamComparisonAPIProps {
  setResult: (result: Team[] | null) => void;
  setComparisonData: (data: ComparisonData | null) => void;
  setChatHistory: React.Dispatch<React.SetStateAction<ChatMessage[]>>;
  setIsLoading: (loading: boolean) => void;
  setHasInitialAnalysis: (hasAnalysis: boolean) => void;
}

export const useTeamComparisonAPI = ({
  setResult,
  setComparisonData,
  setChatHistory,
  setIsLoading,
  setHasInitialAnalysis
}: UseTeamComparisonAPIProps) => {
  const performAnalysis = async (
    teamNumbers: number[],
    datasetPath: string,
    yourTeamNumber: number,
    pickPosition: "first" | "second" | "third",
    priorities: MetricPriority[],
    chatHistory: ChatMessage[],
    question?: string
  ) => {
    setIsLoading(true);
    try {
      const simplePriorities = priorities.map((p) => ({
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
      
      // Update comparison data if available
      if (data.comparison_data) {
        console.log('Comparison data received:', data.comparison_data);
        setComparisonData(data.comparison_data);
      } else {
        console.log('No comparison_data in response:', data);
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

  return { performAnalysis };
};