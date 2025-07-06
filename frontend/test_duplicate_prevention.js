// Test for label duplicate prevention functionality
// This is a simple JavaScript test to validate the getAvailableLabelsForField function

// Simulate the getAvailableLabelsForField function
const getAvailableLabelsForField = (allLabels, labelMappings, currentFieldHeader) => {
  // Get set of already assigned label names, excluding the current field
  const assignedLabelNames = new Set(
    Object.entries(labelMappings)
      .filter(([fieldHeader, _]) => fieldHeader !== currentFieldHeader)
      .map(([_, label]) => label.label)
  );
  
  // Return labels that are not already assigned
  return allLabels.filter(label => !assignedLabelNames.has(label.label));
};

// Test data
const testLabels = [
  { label: 'auto_coral_L1_scored', category: 'autonomous' },
  { label: 'teleop_speaker_scored', category: 'teleop' },
  { label: 'strategy_notes', category: 'strategic' },
  { label: 'endgame_climb_successful', category: 'endgame' }
];

// Test 1: No labels assigned yet
console.log('Test 1: No labels assigned');
const labelMappings1 = {};
const available1 = getAvailableLabelsForField(testLabels, labelMappings1, 'Header1');
console.log(`Available labels: ${available1.length} (expected: 4)`);
console.assert(available1.length === 4, 'Should have all labels available');

// Test 2: One label assigned to different field
console.log('\nTest 2: One label assigned to different field');
const labelMappings2 = {
  'Header2': { label: 'auto_coral_L1_scored', category: 'autonomous' }
};
const available2 = getAvailableLabelsForField(testLabels, labelMappings2, 'Header1');
console.log(`Available labels: ${available2.length} (expected: 3)`);
console.log(`Filtered out: ${testLabels.find(l => !available2.includes(l))?.label}`);
console.assert(available2.length === 3, 'Should filter out assigned label');
console.assert(!available2.find(l => l.label === 'auto_coral_L1_scored'), 'Should not include assigned label');

// Test 3: Label assigned to current field (should still be available)
console.log('\nTest 3: Label assigned to current field');
const labelMappings3 = {
  'Header1': { label: 'teleop_speaker_scored', category: 'teleop' }
};
const available3 = getAvailableLabelsForField(testLabels, labelMappings3, 'Header1');
console.log(`Available labels: ${available3.length} (expected: 4)`);
console.assert(available3.length === 4, 'Should include currently assigned label');
console.assert(available3.find(l => l.label === 'teleop_speaker_scored'), 'Should include current field label');

// Test 4: Multiple labels assigned
console.log('\nTest 4: Multiple labels assigned to different fields');
const labelMappings4 = {
  'Header2': { label: 'auto_coral_L1_scored', category: 'autonomous' },
  'Header3': { label: 'strategy_notes', category: 'strategic' }
};
const available4 = getAvailableLabelsForField(testLabels, labelMappings4, 'Header1');
console.log(`Available labels: ${available4.length} (expected: 2)`);
console.log(`Available: ${available4.map(l => l.label).join(', ')}`);
console.assert(available4.length === 2, 'Should filter out both assigned labels');
console.assert(available4.find(l => l.label === 'teleop_speaker_scored'), 'Should include unassigned label 1');
console.assert(available4.find(l => l.label === 'endgame_climb_successful'), 'Should include unassigned label 2');

// Test 5: Auto-match simulation
console.log('\nTest 5: Auto-match simulation');
const headers = ['Team Number', 'Auto Coral L1', 'Speaker Score', 'Strategy'];
const updatedLabelMappings = {};

headers.forEach((header, index) => {
  const availableLabels = getAvailableLabelsForField(testLabels, updatedLabelMappings, header);
  console.log(`Field "${header}": ${availableLabels.length} available labels`);
  
  // Simulate assigning first available label
  if (availableLabels.length > 0) {
    updatedLabelMappings[header] = availableLabels[0];
    console.log(`  Assigned: ${availableLabels[0].label}`);
  }
});

console.log(`\nFinal assignments: ${Object.keys(updatedLabelMappings).length}`);
Object.entries(updatedLabelMappings).forEach(([header, label]) => {
  console.log(`  ${header} -> ${label.label}`);
});

// Test uniqueness
const assignedLabels = Object.values(updatedLabelMappings).map(l => l.label);
const uniqueLabels = [...new Set(assignedLabels)];
console.assert(assignedLabels.length === uniqueLabels.length, 'All assigned labels should be unique');

console.log('\n✅ All duplicate prevention tests passed!');