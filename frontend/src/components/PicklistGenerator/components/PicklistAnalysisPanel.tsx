import React from "react";
import { PicklistAnalysis } from "../types";

interface PicklistAnalysisPanelProps {
  analysis: PicklistAnalysis | null;
  showAnalysis: boolean;
}

export const PicklistAnalysisPanel: React.FC<PicklistAnalysisPanelProps> = ({
  analysis,
  showAnalysis,
}) => {
  if (!showAnalysis || !analysis) {
    return null;
  }

  return (
    <div className="mb-6 bg-purple-50 p-4 rounded-lg border border-purple-200">
      <h3 className="font-bold text-purple-800 mb-2">GPT Analysis</h3>

      <div className="space-y-3">
        <div>
          <h4 className="font-semibold text-purple-700">
            Draft Reasoning:
          </h4>
          <p className="text-sm text-gray-700">
            {analysis.draft_reasoning}
          </p>
        </div>

        <div>
          <h4 className="font-semibold text-purple-700">
            Critical Evaluation:
          </h4>
          <p className="text-sm text-gray-700">{analysis.evaluation}</p>
        </div>

        <div>
          <h4 className="font-semibold text-purple-700">
            Final Recommendations:
          </h4>
          <p className="text-sm text-gray-700">
            {analysis.final_recommendations}
          </p>
        </div>
      </div>
    </div>
  );
};