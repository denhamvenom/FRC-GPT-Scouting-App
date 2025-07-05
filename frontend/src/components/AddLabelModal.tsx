import React, { useState, useEffect } from 'react';
import { GameLabel } from '../hooks/useGameLabels';
import { apiUrl, fetchWithNgrokHeaders } from '../config';

interface AddLabelModalProps {
  isOpen: boolean;
  onClose: () => void;
  onLabelAdded: (newLabel: GameLabel) => void;
  onLabelUpdated?: (updatedLabel: GameLabel) => void;
  fieldHeader?: string; // The field header to provide context for AI generation
  editingLabel?: GameLabel; // If provided, modal is in edit mode
}

export function AddLabelModal({ isOpen, onClose, onLabelAdded, onLabelUpdated, fieldHeader, editingLabel }: AddLabelModalProps) {
  const [formData, setFormData] = useState({
    label: '',
    category: 'autonomous',
    description: '',
    data_type: 'count',
    typical_range: '',
    usage_context: ''
  });
  
  const [isGenerating, setIsGenerating] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const isEditing = !!editingLabel;

  // Populate form when editing a label
  useEffect(() => {
    if (editingLabel) {
      setFormData({
        label: editingLabel.label,
        category: editingLabel.category,
        description: editingLabel.description,
        data_type: editingLabel.data_type,
        typical_range: editingLabel.typical_range,
        usage_context: editingLabel.usage_context
      });
    } else {
      // Reset form for new label
      setFormData({
        label: '',
        category: 'autonomous',
        description: '',
        data_type: 'count',
        typical_range: '',
        usage_context: ''
      });
    }
    setError(null);
  }, [editingLabel, isOpen]);

  const categories = [
    'autonomous',
    'teleop',
    'endgame',
    'defense',
    'reliability',
    'strategic'
  ];

  const dataTypes = [
    'count',
    'rating',
    'boolean',
    'time'
  ];

  const handleGenerateDescription = async () => {
    if (!formData.label && !fieldHeader) {
      setError('Please provide a label name or field header for AI generation');
      return;
    }

    setIsGenerating(true);
    setError(null);

    try {
      const response = await fetchWithNgrokHeaders(
        apiUrl('/api/v1/game-labels/generate-description'),
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            label_name: formData.label || fieldHeader,
            category: formData.category,
            data_type: formData.data_type,
            context: fieldHeader ? `Field header: ${fieldHeader}` : undefined
          })
        }
      );

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      
      if (data.success) {
        setFormData(prev => ({
          ...prev,
          description: data.description || prev.description,
          typical_range: data.typical_range || prev.typical_range,
          usage_context: data.usage_context || prev.usage_context,
          label: data.suggested_label || prev.label || fieldHeader || ''
        }));
      } else {
        setError(data.message || 'Failed to generate description');
      }
    } catch (err) {
      console.error('Error generating description:', err);
      setError(`Failed to generate description: ${err instanceof Error ? err.message : 'Unknown error'}`);
    } finally {
      setIsGenerating(false);
    }
  };

  const handleSave = async () => {
    // Basic validation
    if (!formData.label.trim()) {
      setError('Label name is required');
      return;
    }
    
    if (!formData.description.trim()) {
      setError('Description is required');
      return;
    }

    setIsSaving(true);
    setError(null);

    try {
      // Create the new label object
      const newLabel: GameLabel = {
        label: formData.label.trim(),
        category: formData.category,
        description: formData.description.trim(),
        data_type: formData.data_type,
        typical_range: formData.typical_range.trim() || 'varies',
        usage_context: formData.usage_context.trim() || 'custom field'
      };

      if (isEditing) {
        // Update existing label
        const response = await fetchWithNgrokHeaders(
          apiUrl('/api/v1/game-labels/update'),
          {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({
              original_label: editingLabel!.label,
              updated_label: newLabel,
              year: new Date().getFullYear()
            })
          }
        );

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        const data = await response.json();
        
        if (data.success) {
          if (onLabelUpdated) {
            onLabelUpdated(newLabel);
          }
          onClose();
        } else {
          setError(data.message || 'Failed to update label');
        }
      } else {
        // Create new label
        const response = await fetchWithNgrokHeaders(
          apiUrl('/api/v1/game-labels/add'),
          {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({
              label: newLabel,
              year: new Date().getFullYear()
            })
          }
        );

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        const data = await response.json();
        
        if (data.success) {
          onLabelAdded(newLabel);
          onClose();
        } else {
          setError(data.message || 'Failed to save label');
        }
      }
    } catch (err) {
      console.error('Error saving label:', err);
      setError(`Failed to save label: ${err instanceof Error ? err.message : 'Unknown error'}`);
    } finally {
      setIsSaving(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 w-full max-w-2xl max-h-[90vh] overflow-y-auto">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-bold">
            {isEditing ? 'Edit Scouting Label' : 'Add New Scouting Label'}
          </h2>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700 text-2xl"
          >
            ×
          </button>
        </div>

        {fieldHeader && !isEditing && (
          <div className="mb-4 p-3 bg-blue-50 border border-blue-200 rounded">
            <p className="text-blue-800 text-sm">
              <strong>Creating label for field:</strong> {fieldHeader}
            </p>
          </div>
        )}
        
        {isEditing && (
          <div className="mb-4 p-3 bg-amber-50 border border-amber-200 rounded">
            <p className="text-amber-800 text-sm">
              <strong>Editing label:</strong> {editingLabel!.label}
            </p>
          </div>
        )}

        {error && (
          <div className="mb-4 p-3 bg-red-100 text-red-700 rounded">
            {error}
          </div>
        )}

        <div className="space-y-4">
          {/* Label Name */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Label Name *
            </label>
            <input
              type="text"
              value={formData.label}
              onChange={(e) => setFormData(prev => ({ ...prev, label: e.target.value }))}
              placeholder="e.g., teleop_custom_scoring"
              className="w-full p-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500"
            />
            <p className="text-xs text-gray-500 mt-1">
              Use underscores instead of spaces (e.g., "my_custom_field")
            </p>
          </div>

          {/* Category and Data Type Row */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Category *
              </label>
              <select
                value={formData.category}
                onChange={(e) => setFormData(prev => ({ ...prev, category: e.target.value }))}
                className="w-full p-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500"
              >
                {categories.map(cat => (
                  <option key={cat} value={cat}>
                    {cat.charAt(0).toUpperCase() + cat.slice(1)}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Data Type *
              </label>
              <select
                value={formData.data_type}
                onChange={(e) => setFormData(prev => ({ ...prev, data_type: e.target.value }))}
                className="w-full p-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500"
              >
                {dataTypes.map(type => (
                  <option key={type} value={type}>
                    {type.charAt(0).toUpperCase() + type.slice(1)}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* AI Generate Button */}
          <div className="flex justify-center">
            <button
              onClick={handleGenerateDescription}
              disabled={isGenerating || (!formData.label && !fieldHeader)}
              className="px-4 py-2 bg-purple-600 text-white rounded hover:bg-purple-700 disabled:opacity-50 flex items-center"
            >
              {isGenerating ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-t-2 border-b-2 border-white mr-2"></div>
                  Generating with AI...
                </>
              ) : (
                <>
                  🤖 Generate Description with AI
                </>
              )}
            </button>
          </div>

          {/* Description */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Description *
            </label>
            <textarea
              value={formData.description}
              onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
              placeholder="Describe what this field measures..."
              rows={3}
              className="w-full p-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500"
            />
          </div>

          {/* Typical Range */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Typical Range
            </label>
            <input
              type="text"
              value={formData.typical_range}
              onChange={(e) => setFormData(prev => ({ ...prev, typical_range: e.target.value }))}
              placeholder="e.g., 0-10, 1-5, true/false"
              className="w-full p-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500"
            />
          </div>

          {/* Usage Context */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Usage Context
            </label>
            <input
              type="text"
              value={formData.usage_context}
              onChange={(e) => setFormData(prev => ({ ...prev, usage_context: e.target.value }))}
              placeholder="e.g., Tracked during teleop period"
              className="w-full p-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex justify-end space-x-3 mt-6">
          <button
            onClick={onClose}
            className="px-4 py-2 text-gray-600 border border-gray-300 rounded hover:bg-gray-50"
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            disabled={isSaving || !formData.label.trim() || !formData.description.trim()}
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50 flex items-center"
          >
            {isSaving ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-t-2 border-b-2 border-white mr-2"></div>
                {isEditing ? 'Updating...' : 'Saving...'}
              </>
            ) : (
              isEditing ? 'Update Label' : 'Save Label'
            )}
          </button>
        </div>
      </div>
    </div>
  );
}