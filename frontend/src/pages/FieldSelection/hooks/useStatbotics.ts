// frontend/src/pages/FieldSelection/hooks/useStatbotics.ts

import { useState, useMemo } from 'react';
import { StatboticsField } from '../types';

export const useStatbotics = (
  statboticsFields: StatboticsField[],
  selectedStatboticsFields: string[],
  onSelectionChange: (fields: string[]) => void
) => {
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [selectedCategory, setSelectedCategory] = useState<string>('all');

  // Get unique categories
  const categories = useMemo(() => {
    const cats = new Set(statboticsFields.map(field => field.category));
    return ['all', ...Array.from(cats).sort()];
  }, [statboticsFields]);

  // Filter fields based on search and category
  const filteredFields = useMemo(() => {
    return statboticsFields.filter(field => {
      const matchesSearch = searchTerm === '' || 
        field.field_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        field.description.toLowerCase().includes(searchTerm.toLowerCase());
      
      const matchesCategory = selectedCategory === 'all' || field.category === selectedCategory;
      
      return matchesSearch && matchesCategory;
    });
  }, [statboticsFields, searchTerm, selectedCategory]);

  // Toggle field selection
  const toggleField = (fieldName: string) => {
    const isSelected = selectedStatboticsFields.includes(fieldName);
    
    if (isSelected) {
      onSelectionChange(selectedStatboticsFields.filter(f => f !== fieldName));
    } else {
      onSelectionChange([...selectedStatboticsFields, fieldName]);
    }
  };

  // Select all filtered fields
  const selectAllFiltered = () => {
    const filteredFieldNames = filteredFields.map(f => f.field_name);
    const newSelection = Array.from(new Set([...selectedStatboticsFields, ...filteredFieldNames]));
    onSelectionChange(newSelection);
  };

  // Deselect all filtered fields
  const deselectAllFiltered = () => {
    const filteredFieldNames = new Set(filteredFields.map(f => f.field_name));
    const newSelection = selectedStatboticsFields.filter(f => !filteredFieldNames.has(f));
    onSelectionChange(newSelection);
  };

  // Clear all selections
  const clearAllSelections = () => {
    onSelectionChange([]);
  };

  // Select recommended fields (based on common usage)
  const selectRecommended = () => {
    const recommendedFields = statboticsFields
      .filter(field => 
        field.field_name.includes('epa') || 
        field.field_name.includes('auto') ||
        field.field_name.includes('teleop') ||
        field.field_name.includes('endgame')
      )
      .map(f => f.field_name);
    
    const newSelection = Array.from(new Set([...selectedStatboticsFields, ...recommendedFields]));
    onSelectionChange(newSelection);
  };

  // Get field counts
  const fieldCounts = useMemo(() => {
    return {
      total: statboticsFields.length,
      filtered: filteredFields.length,
      selected: selectedStatboticsFields.length,
      selectedFiltered: filteredFields.filter(f => selectedStatboticsFields.includes(f.field_name)).length
    };
  }, [statboticsFields, filteredFields, selectedStatboticsFields]);

  // Check if all filtered fields are selected
  const allFilteredSelected = useMemo(() => {
    return filteredFields.length > 0 && 
           filteredFields.every(f => selectedStatboticsFields.includes(f.field_name));
  }, [filteredFields, selectedStatboticsFields]);

  return {
    // State
    searchTerm,
    selectedCategory,
    categories,
    filteredFields,
    fieldCounts,
    allFilteredSelected,

    // Actions
    setSearchTerm,
    setSelectedCategory,
    toggleField,
    selectAllFiltered,
    deselectAllFiltered,
    clearAllSelections,
    selectRecommended,
  };
};