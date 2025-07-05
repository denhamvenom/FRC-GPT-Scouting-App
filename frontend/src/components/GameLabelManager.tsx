import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useGameLabels } from '../hooks/useGameLabels';

interface GameLabel {
  label: string;
  category: string;
  description: string;
  data_type: string;
  typical_range: string;
  usage_context: string;
}

const CATEGORIES = [
  'autonomous',
  'teleop',
  'endgame',
  'defense',
  'reliability',
  'strategic'
];

const DATA_TYPES = [
  'count',
  'rating',
  'boolean',
  'time'
];

function GameLabelManager() {
  const navigate = useNavigate();
  const { 
    labels, 
    isLoading, 
    error, 
    saveLabels, 
    loadLabels 
  } = useGameLabels();
  
  const [editingLabels, setEditingLabels] = useState<GameLabel[]>([]);
  const [isEditing, setIsEditing] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState<string | null>(null);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [isSaving, setIsSaving] = useState(false);
  
  // Load labels on component mount
  useEffect(() => {
    loadLabels();
  }, []);
  
  // Update editing state when labels change
  useEffect(() => {
    if (labels.length > 0) {
      setEditingLabels([...labels]);
    }
  }, [labels]);
  
  const handleEditLabel = (index: number, field: keyof GameLabel, value: string) => {
    const updatedLabels = [...editingLabels];
    updatedLabels[index] = { ...updatedLabels[index], [field]: value };
    setEditingLabels(updatedLabels);
  };
  
  const handleAddLabel = () => {
    const newLabel: GameLabel = {
      label: '',
      category: 'autonomous',
      description: '',
      data_type: 'count',
      typical_range: '',
      usage_context: ''
    };
    setEditingLabels([...editingLabels, newLabel]);
    setIsEditing(true);
  };
  
  const handleRemoveLabel = (index: number) => {
    const updatedLabels = editingLabels.filter((_, i) => i !== index);
    setEditingLabels(updatedLabels);
  };
  
  const handleSave = async () => {
    // Validate labels
    const validLabels = editingLabels.filter(label => 
      label.label.trim() !== '' && 
      label.description.trim() !== ''
    );
    
    if (validLabels.length === 0) {
      setSaveError('Please add at least one valid label with name and description');
      return;
    }
    
    setIsSaving(true);
    setSaveError(null);
    setSaveSuccess(null);
    
    try {
      const success = await saveLabels(validLabels);
      if (success) {
        setSaveSuccess(`Successfully saved ${validLabels.length} scouting labels`);
        setIsEditing(false);
        // Reload labels to show updated data
        await loadLabels();
      } else {
        setSaveError('Failed to save labels');
      }
    } catch (err) {
      setSaveError(`Error saving labels: ${err instanceof Error ? err.message : 'Unknown error'}`);
    } finally {
      setIsSaving(false);
    }
  };
  
  const handleCancel = () => {
    setEditingLabels([...labels]);
    setIsEditing(false);
    setSaveError(null);
    setSaveSuccess(null);
  };
  
  const handleSkip = () => {
    // Return to setup step 4 (Connect Spreadsheet) after skipping label review
    navigate('/setup?step=4');
  };
  
  const handleContinue = () => {
    // Return to setup step 4 (Connect Spreadsheet) after reviewing/editing labels
    navigate('/setup?step=4');
  };
  
  if (isLoading) {
    return (
      <div className="max-w-6xl mx-auto p-6">
        <div className="flex justify-center items-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
          <span className="ml-3 text-lg">Loading scouting labels...</span>
        </div>
      </div>
    );
  }
  
  return (
    <div className="max-w-6xl mx-auto p-6">
      <h1 className="text-3xl font-bold mb-6">Review Scouting Labels</h1>
      
      <div className="bg-blue-50 p-4 rounded-lg mb-6 border-l-4 border-blue-400">
        <h2 className="text-lg font-semibold text-blue-800 mb-2">What Are Scouting Labels?</h2>
        <p className="text-blue-700 mb-2">
          Scouting labels are specific metrics that teams track about robot performance during matches.
          These help categorize your scouting data fields for better analysis.
        </p>
        <p className="text-blue-600 text-sm">
          <strong>Examples:</strong> auto_coral_L1_scored, teleop_defense_rating, endgame_climb_successful
        </p>
      </div>
      
      {error && (
        <div className="p-3 mb-4 bg-red-100 text-red-700 rounded">
          {error}
        </div>
      )}
      
      {saveSuccess && (
        <div className="p-3 mb-4 bg-green-100 text-green-700 rounded">
          {saveSuccess}
        </div>
      )}
      
      {saveError && (
        <div className="p-3 mb-4 bg-red-100 text-red-700 rounded">
          {saveError}
        </div>
      )}
      
      <div className="bg-white rounded-lg shadow-md p-6 mb-6">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-bold">
            Scouting Metrics ({editingLabels.length} labels)
          </h2>
          <div className="flex gap-2">
            {!isEditing && (
              <>
                <button
                  onClick={() => setIsEditing(true)}
                  className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
                >
                  Edit Labels
                </button>
                <button
                  onClick={handleSkip}
                  className="px-4 py-2 bg-gray-600 text-white rounded hover:bg-gray-700"
                >
                  Skip & Return to Setup
                </button>
              </>
            )}
            
            {isEditing && (
              <>
                <button
                  onClick={handleAddLabel}
                  className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700"
                >
                  Add Label
                </button>
                <button
                  onClick={handleSave}
                  disabled={isSaving}
                  className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:bg-gray-400"
                >
                  {isSaving ? 'Saving...' : 'Save'}
                </button>
                <button
                  onClick={handleCancel}
                  className="px-4 py-2 bg-gray-600 text-white rounded hover:bg-gray-700"
                >
                  Cancel
                </button>
              </>
            )}
          </div>
        </div>
        
        {editingLabels.length === 0 ? (
          <div className="text-center py-8">
            <p className="text-gray-600 mb-4">No scouting labels found.</p>
            <button
              onClick={handleAddLabel}
              className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
            >
              Add First Label
            </button>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full border">
              <thead className="bg-gray-100">
                <tr>
                  <th className="border px-4 py-2 text-left">Label Name</th>
                  <th className="border px-4 py-2 text-left">Category</th>
                  <th className="border px-4 py-2 text-left">Data Type</th>
                  <th className="border px-4 py-2 text-left">Range</th>
                  <th className="border px-4 py-2 text-left">Description</th>
                  <th className="border px-4 py-2 text-left">Usage Context</th>
                  {isEditing && <th className="border px-4 py-2 text-left">Actions</th>}
                </tr>
              </thead>
              <tbody>
                {editingLabels.map((label, index) => (
                  <tr key={index} className="hover:bg-gray-50">
                    <td className="border px-4 py-2">
                      {isEditing ? (
                        <input
                          type="text"
                          value={label.label}
                          onChange={(e) => handleEditLabel(index, 'label', e.target.value)}
                          className="w-full p-1 border rounded"
                          placeholder="e.g., auto_coral_L1_scored"
                        />
                      ) : (
                        <span className="font-mono text-sm">{label.label}</span>
                      )}
                    </td>
                    <td className="border px-4 py-2">
                      {isEditing ? (
                        <select
                          value={label.category}
                          onChange={(e) => handleEditLabel(index, 'category', e.target.value)}
                          className="w-full p-1 border rounded"
                        >
                          {CATEGORIES.map(cat => (
                            <option key={cat} value={cat}>{cat}</option>
                          ))}
                        </select>
                      ) : (
                        <span className="px-2 py-1 bg-blue-100 text-blue-800 rounded-full text-xs">
                          {label.category}
                        </span>
                      )}
                    </td>
                    <td className="border px-4 py-2">
                      {isEditing ? (
                        <select
                          value={label.data_type}
                          onChange={(e) => handleEditLabel(index, 'data_type', e.target.value)}
                          className="w-full p-1 border rounded"
                        >
                          {DATA_TYPES.map(type => (
                            <option key={type} value={type}>{type}</option>
                          ))}
                        </select>
                      ) : (
                        <span className="px-2 py-1 bg-green-100 text-green-800 rounded-full text-xs">
                          {label.data_type}
                        </span>
                      )}
                    </td>
                    <td className="border px-4 py-2">
                      {isEditing ? (
                        <input
                          type="text"
                          value={label.typical_range}
                          onChange={(e) => handleEditLabel(index, 'typical_range', e.target.value)}
                          className="w-full p-1 border rounded"
                          placeholder="e.g., 0-10, 1-5, true/false"
                        />
                      ) : (
                        <span className="text-sm">{label.typical_range}</span>
                      )}
                    </td>
                    <td className="border px-4 py-2">
                      {isEditing ? (
                        <textarea
                          value={label.description}
                          onChange={(e) => handleEditLabel(index, 'description', e.target.value)}
                          className="w-full p-1 border rounded"
                          rows={2}
                          placeholder="What this metric measures..."
                        />
                      ) : (
                        <span className="text-sm">{label.description}</span>
                      )}
                    </td>
                    <td className="border px-4 py-2">
                      {isEditing ? (
                        <textarea
                          value={label.usage_context}
                          onChange={(e) => handleEditLabel(index, 'usage_context', e.target.value)}
                          className="w-full p-1 border rounded"
                          rows={2}
                          placeholder="When this would be tracked..."
                        />
                      ) : (
                        <span className="text-sm">{label.usage_context}</span>
                      )}
                    </td>
                    {isEditing && (
                      <td className="border px-4 py-2">
                        <button
                          onClick={() => handleRemoveLabel(index)}
                          className="px-2 py-1 bg-red-600 text-white rounded hover:bg-red-700 text-xs"
                        >
                          Remove
                        </button>
                      </td>
                    )}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
      
      {!isEditing && editingLabels.length > 0 && (
        <div className="flex justify-center">
          <button
            onClick={handleContinue}
            className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-lg font-semibold"
          >
            Return to Setup
          </button>
        </div>
      )}
    </div>
  );
}

export default GameLabelManager;