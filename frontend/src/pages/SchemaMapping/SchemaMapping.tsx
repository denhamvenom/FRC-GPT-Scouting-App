import React from 'react';
import { useSchemaMapping } from './hooks/useSchemaMapping';
import { useFieldMapping } from './hooks/useFieldMapping';
import { FieldMapper } from './components/FieldMapper';
import { SchemaPreview } from './components/SchemaPreview';
import { MappingActions } from './components/MappingActions';

const SchemaMapping: React.FC = () => {
  const { state, actions } = useSchemaMapping();
  const fieldMappingHook = useFieldMapping(state.headers);

  if (state.loading) {
    return <div className="text-center p-8">Loading schema...</div>;
  }

  return (
    <div className="max-w-6xl mx-auto p-8">
      <h1 className="text-2xl font-bold mb-6">Scouting Schema Mapping</h1>
      
      {state.error && (
        <div className="p-3 mb-4 bg-red-100 text-red-700 rounded">
          {state.error}
        </div>
      )}
      
      {state.validationMessage && (
        <div className="p-3 mb-4 bg-yellow-100 text-yellow-700 rounded">
          {state.validationMessage}
        </div>
      )}
      
      <MappingActions
        criticalMappings={state.criticalMappings}
        mapping={state.mapping}
        headers={state.headers}
        teamNumberCandidates={fieldMappingHook.getTeamNumberCandidates}
        matchNumberCandidates={fieldMappingHook.getMatchNumberCandidates}
        onCriticalFieldChange={actions.handleCriticalFieldChange}
        onClearCriticalMapping={actions.clearCriticalMapping}
        onSave={actions.handleSave}
        getMappingValue={fieldMappingHook.getMappingValue}
      />
      
      <div className="flex space-x-4">
        <FieldMapper
          headers={state.headers}
          mapping={state.mapping}
          criticalMappings={state.criticalMappings}
          suggestedVariables={state.suggestedVariables}
          teamNumberCandidates={fieldMappingHook.getTeamNumberCandidates}
          matchNumberCandidates={fieldMappingHook.getMatchNumberCandidates}
          onCriticalFieldChange={actions.handleCriticalFieldChange}
          onMappingChange={actions.handleChange}
          onClearCriticalMapping={actions.clearCriticalMapping}
          getMappingValue={fieldMappingHook.getMappingValue}
          isCriticalField={fieldMappingHook.isCriticalField}
        />
        
        <SchemaPreview
          suggestedVariables={state.suggestedVariables}
        />
      </div>
    </div>
  );
};

export default SchemaMapping;