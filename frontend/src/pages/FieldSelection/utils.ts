// frontend/src/pages/FieldSelection/utils.ts

// Enhanced utility function to auto-categorize fields based on patterns
export const autoCategorizeField = (header: string): string => {
  // Convert to lowercase for case-insensitive matching
  const headerLower = header.toLowerCase();
  
  // Special handling for robot team numbers in SuperScouting
  if (/robot\s*\d+\s*number/i.test(header)) {
    return 'team_number'; // Identify "Robot X Number" as team number fields
  }
  
  // Check for team number or match number patterns (general)
  if ((/team|^t\d+$|^frc\d+$/i.test(headerLower)) && /number/i.test(headerLower)) {
    return 'team_number';
  }
  
  // Handle match/qual number fields
  if (/qual\s*number/i.test(headerLower)) {
    return 'match_number';
  }
  
  if (/match|qualification|^q\d+$/i.test(headerLower)) {
    return 'match_number';
  }
  
  // Check for autonomous/auto patterns
  if (/auto|autonomous|^a_|^a\.|auton/i.test(headerLower)) {
    return 'auto';
  }
  
  // Check for teleop patterns
  if (/tele|teleop|teleoperated|driver|^t_|^t\./i.test(headerLower)) {
    return 'teleop';
  }
  
  // Check for endgame patterns
  if (/end|endgame|final|climb|parking|docking|hanging/i.test(headerLower)) {
    return 'endgame';
  }
  
  // Check for strategy/subjective patterns
  if (/strat|comment|note|subjective|rating|skill|defense|speed|observ/i.test(headerLower)) {
    return 'strategy';
  }
  
  // Check for team info patterns
  if (/alliance|color|station|position|start/i.test(headerLower)) {
    return 'team_info';
  }
  
  // Default to 'other' if no patterns match
  return 'other';
};

// Utility to format field names for display
export const formatFieldName = (fieldName: string): string => {
  return fieldName
    .replace(/_/g, ' ')
    .replace(/\b\w/g, l => l.toUpperCase());
};

// Utility to validate critical field patterns
export const validateCriticalField = (header: string, fieldType: 'team_number' | 'match_number'): boolean => {
  const headerLower = header.toLowerCase();
  
  switch (fieldType) {
    case 'team_number':
      return /team|number|^\d+$|frc/i.test(headerLower);
    case 'match_number':
      return /match|qual|^q\d+$/i.test(headerLower);
    default:
      return false;
  }
};

// Utility to group fields by category
export const groupFieldsByCategory = (fields: string[], selectedFields: { [key: string]: string }) => {
  const grouped: { [key: string]: string[] } = {};
  
  fields.forEach(field => {
    const category = selectedFields[field] || 'other';
    if (!grouped[category]) {
      grouped[category] = [];
    }
    grouped[category].push(field);
  });
  
  return grouped;
};

// Utility to get field category color
export const getCategoryColor = (category: string): string => {
  switch (category) {
    case 'team_info': return 'bg-blue-100 text-blue-800';
    case 'auto': return 'bg-green-100 text-green-800';
    case 'teleop': return 'bg-purple-100 text-purple-800';
    case 'endgame': return 'bg-orange-100 text-orange-800';
    case 'strategy': return 'bg-yellow-100 text-yellow-800';
    case 'other': return 'bg-gray-100 text-gray-800';
    default: return 'bg-gray-100 text-gray-800';
  }
};

// Utility to get data type icon
export const getDataTypeIcon = (dataType: string): string => {
  switch (dataType.toLowerCase()) {
    case 'integer':
    case 'int':
    case 'number': return '🔢';
    case 'float':
    case 'decimal': return '🔢';
    case 'string':
    case 'text': return '📝';
    case 'boolean':
    case 'bool': return '✅';
    default: return '❓';
  }
};