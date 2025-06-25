/**
 * Utility functions for statistical data color coding
 */

export const getStatColor = (value: number, allValues: number[]): string => {
  if (allValues.length <= 1) return "bg-gray-100";
  
  const sortedValues = [...allValues].sort((a, b) => b - a); // Descending order
  const highestValue = sortedValues[0];
  const lowestValue = sortedValues[sortedValues.length - 1];
  
  if (allValues.length === 2) {
    return value === highestValue ? "bg-green-100 text-green-800" : "bg-red-100 text-red-800";
  } else {
    // Three teams: highest = green, lowest = red, middle = yellow
    if (value === highestValue) return "bg-green-100 text-green-800";
    if (value === lowestValue) return "bg-red-100 text-red-800";
    return "bg-yellow-100 text-yellow-800";
  }
};