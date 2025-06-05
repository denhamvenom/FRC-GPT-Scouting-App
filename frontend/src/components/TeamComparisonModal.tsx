import React, { useState } from "react";

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
  const [question, setQuestion] = useState("");
  const [result, setResult] = useState<Team[] | null>(null);
  const [summary, setSummary] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const compareTeams = async () => {
    setIsLoading(true);
    setResult(null);
    setSummary(null);
    try {
      const simplePriorities = prioritiesMap[pickPosition].map((p) => ({
        id: p.id,
        weight: p.weight,
        reason: p.reason || null,
      }));
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
            question,
          }),
        },
      );
      if (!response.ok) {
        const err = await response.json();
        throw new Error(err.detail || "Failed to compare teams");
      }
      const data = await response.json();
      setResult(data.ordered_teams || []);
      setSummary(data.summary || null);
    } catch (err) {
      console.error("Error comparing teams:", err);
    } finally {
      setIsLoading(false);
    }
  };

  const apply = () => {
    if (result) {
      onApply(result);
      onClose();
    }
  };

  if (!isOpen) return null;
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded p-4 w-full max-w-lg space-y-4">
        <h3 className="text-lg font-semibold">Compare Selected Teams</h3>
        <div className="space-y-2">
          <label className="block text-sm font-medium">Pick Strategy</label>
          <select
            value={pickPosition}
            onChange={(e) =>
              setPickPosition(e.target.value as "first" | "second" | "third")
            }
            className="border p-1 rounded w-full"
          >
            <option value="first">1st Pick</option>
            <option value="second">2nd Pick</option>
            <option value="third">3rd Pick</option>
          </select>
        </div>
        <div className="space-y-2">
          <label className="block text-sm font-medium">Optional Question</label>
          <textarea
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            className="border p-1 rounded w-full"
            rows={3}
          />
        </div>
        <div className="flex justify-end space-x-2">
          <button onClick={onClose} className="px-3 py-1 bg-gray-300 rounded">
            Cancel
          </button>
          <button
            onClick={compareTeams}
            disabled={isLoading}
            className="px-3 py-1 bg-blue-600 text-white rounded"
          >
            {isLoading ? "Comparing..." : "Compare"}
          </button>
        </div>
        {result && (
          <div className="space-y-2 border-t pt-3 mt-3">
            {summary && <p className="text-sm">{summary}</p>}
            <ol className="list-decimal list-inside space-y-1">
              {result.map((team) => (
                <li key={team.team_number} className="text-sm">
                  {team.team_number} – {team.nickname}
                </li>
              ))}
            </ol>
            <div className="flex justify-end">
              <button
                onClick={apply}
                className="px-3 py-1 bg-green-600 text-white rounded"
              >
                Apply Order
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default TeamComparisonModal;
