import React from 'react';
import { useNavigate } from 'react-router-dom';
import EventArchiveManager from '../../components/EventArchiveManager';
import SheetConfigManager from '../../components/SheetConfigManager';
import { useSetup } from './hooks/useSetup';
import { useEventData } from './hooks/useEventData';
import { useProgress } from './hooks/useProgress';
import { StepIndicator } from './components/StepIndicator';
import { EventSelector } from './components/EventSelector';
import { SetupActions } from './components/SetupActions';
import type { TocItemType } from './types';

const Setup: React.FC = () => {
  const navigate = useNavigate();
  const { state, actions, canProceedToNextStep } = useSetup();
  const progressHook = useProgress();
  
  const eventDataHook = useEventData(
    state.currentManualInfo,
    progressHook.selectedTocItems,
    progressHook.updateSelectedTocItems
  );

  const handleContinue = () => {
    navigate("/field-selection");
  };

  // Event Switch Dialog
  const renderEventSwitchDialog = () => {
    if (!state.showEventSwitchDialog || !state.pendingEventAction) return null;

    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white p-6 rounded-lg shadow-xl max-w-md w-full">
          <div className="flex items-center text-yellow-600 mb-4">
            <svg className="w-6 h-6 mr-2" fill="none" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" viewBox="0 0 24 24" stroke="currentColor">
              <path d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"></path>
            </svg>
            <h3 className="text-xl font-bold">Change Active Event?</h3>
          </div>
          
          <p className="mb-4">
            An event is already loaded in the system: <strong>{state.currentEvent.event_name || state.currentEvent.event_key}</strong>
          </p>
          
          <p className="mb-4">
            To switch to <strong>{state.pendingEventAction.eventName || state.pendingEventAction.eventKey}</strong>, you must either:
          </p>
          
          <ul className="list-disc pl-5 mb-6 text-gray-700">
            <li className="mb-2">Archive the current event (recommended to preserve data)</li>
            <li className="mb-2">Continue without archiving (data may be lost)</li>
            <li>Cancel and keep working with the current event</li>
          </ul>
          
          <div className="flex flex-col space-y-3">
            <button
              onClick={actions.handleArchiveAndSwitch}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              Archive Current Event
            </button>
            
            <button
              onClick={actions.handleContinueWithoutArchiving}
              className="px-4 py-2 bg-yellow-600 text-white rounded-lg hover:bg-yellow-700"
            >
              Continue Without Archiving
            </button>
            
            <button
              onClick={actions.handleCancelEventSwitch}
              className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-100"
            >
              Cancel
            </button>
          </div>
        </div>
      </div>
    );
  };

  // Step 1: Manual Training
  const renderManualTrainingStep = () => (
    <div className="space-y-6">
      {/* Upload New Manual Section */}
      <div className="bg-white p-6 rounded-lg shadow">
        <h2 className="text-xl font-bold mb-4">Upload Game Manual</h2>
        
        <div className="space-y-4">
          <div>
            <label className="block mb-2 font-semibold">FRC Season Year</label>
            <select
              value={state.year}
              onChange={(e) => actions.handleYearChange(parseInt(e.target.value))}
              className="w-full p-2 border rounded"
              disabled={state.isUploadingManual}
            >
              <option value={2025}>2025</option>
              <option value={2024}>2024</option>
              <option value={2023}>2023</option>
            </select>
          </div>

          <div>
            <label className="block mb-2 font-semibold">Game Manual PDF</label>
            <input
              type="file"
              accept=".pdf"
              onChange={(e) => actions.handleManualFileChange(e.target.files?.[0] || null)}
              disabled={state.isUploadingManual}
              className="w-full p-2 border rounded file:mr-4 file:py-2 file:px-4
                        file:rounded-full file:border-0
                        file:text-sm file:font-semibold
                        file:bg-blue-50 file:text-blue-700
                        hover:file:bg-blue-100"
            />
            {state.selectedManualFile && (
              <p className="mt-1 text-sm text-gray-600">
                Selected file: <strong>{state.selectedManualFile.name}</strong> ({(state.selectedManualFile.size / 1024).toFixed(1)} KB)
              </p>
            )}
          </div>

          {state.manualUploadError && (
            <div className="p-3 bg-red-100 text-red-700 rounded">
              {state.manualUploadError}
            </div>
          )}

          <button
            onClick={actions.handleManualUpload}
            disabled={!state.selectedManualFile || state.isUploadingManual}
            className="w-full py-3 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:bg-blue-300"
          >
            {state.isUploadingManual ? "Uploading..." : "Upload Manual"}
          </button>
        </div>
      </div>

      {/* Existing Manuals Section */}
      <div className="bg-white p-6 rounded-lg shadow">
        <h2 className="text-xl font-bold mb-4">Existing Manuals</h2>
        
        <button
          onClick={actions.fetchManagedManuals}
          disabled={state.isLoadingManagedManuals}
          className="mb-4 px-4 py-2 bg-gray-500 text-white rounded hover:bg-gray-600 disabled:bg-gray-300"
        >
          {state.isLoadingManagedManuals ? "Refreshing..." : "Refresh List"}
        </button>

        {state.managedManualsError && <div className="p-3 mb-4 bg-red-100 text-red-700 rounded">{state.managedManualsError}</div>}
        {state.deleteManualError && <div className="p-3 mb-4 bg-red-100 text-red-700 rounded">Delete Error: {state.deleteManualError}</div>}
        {state.selectedManualError && <div className="p-3 mb-4 bg-red-100 text-red-700 rounded">Load Error: {state.selectedManualError}</div>}

        {state.isLoadingManagedManuals && !state.managedManuals.length ? (
          <p>Loading manuals...</p>
        ) : !state.managedManuals.length && !state.managedManualsError ? (
          <p>No manuals uploaded yet.</p>
        ) : state.managedManuals.length > 0 ? (
          <div className="overflow-x-auto max-h-96">
            <table className="min-w-full border text-sm">
              <thead className="bg-gray-100 sticky top-0">
                <tr>
                  <th className="border px-3 py-2 text-left">Filename</th>
                  <th className="border px-3 py-2 text-left">Year</th>
                  <th className="border px-3 py-2 text-left">Uploaded</th>
                  <th className="border px-3 py-2 text-left">Actions</th>
                </tr>
              </thead>
              <tbody>
                {state.managedManuals.map(manual => (
                  <tr key={manual.id} className="hover:bg-gray-50">
                    <td className="border px-3 py-2">{manual.original_filename}</td>
                    <td className="border px-3 py-2">{manual.year}</td>
                    <td className="border px-3 py-2">{eventDataHook.formatTimestamp(manual.upload_timestamp)}</td>
                    <td className="border px-3 py-2">
                      <button
                        onClick={() => actions.handleSelectManagedManual(manual)}
                        disabled={state.isLoadingSelectedManualId === manual.id}
                        className="mr-2 px-3 py-1 bg-blue-500 text-white text-xs rounded hover:bg-blue-600 disabled:bg-blue-300"
                      >
                        {state.isLoadingSelectedManualId === manual.id ? "Loading..." : "Load ToC"}
                      </button>
                      <button
                        onClick={() => actions.handleDeleteManual(manual.id)}
                        disabled={state.activeDeletingManualId === manual.id}
                        className="px-3 py-1 bg-red-500 text-white text-xs rounded hover:bg-red-600 disabled:bg-red-300"
                      >
                        {state.activeDeletingManualId === manual.id ? "Deleting..." : "Delete"}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : null}
      </div>

      {/* ToC Selection Section */}
      {state.currentManualInfo?.toc_data && state.currentManualInfo.toc_data.length > 0 && (
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-lg font-medium mb-2">Table of Contents - {state.currentManualInfo.original_filename}</h3>
          <p className="text-sm text-gray-600 mb-4">
            💡 <strong>Tip:</strong> Selecting a major section will automatically select all its subsections. 
            Selecting all subsections will automatically select the parent section.
          </p>
          <div className="max-h-96 overflow-y-auto border rounded p-4 bg-gray-50 space-y-1">
            {state.currentManualInfo.toc_data.map((item: TocItemType, index: number) => {
              const key = `${item.title}-${item.page}`;
              const isMainSection = item.level === 1;
              const hasChildren = index < state.currentManualInfo!.toc_data!.length - 1 && 
                                  state.currentManualInfo!.toc_data![index + 1].level > item.level;
              
              return (
                <div 
                  key={key} 
                  className={`flex items-center py-1 px-2 rounded hover:bg-blue-50 ${
                    isMainSection ? 'bg-blue-25' : ''
                  }`} 
                  style={{ marginLeft: `${(item.level -1) * 20}px`}}
                >
                  <input
                    type="checkbox"
                    id={`toc-${key}`}
                    checked={progressHook.selectedTocItems.has(key)}
                    onChange={() => eventDataHook.handleTocItemToggle(item)}
                    className="mr-2 h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                  />
                  <label 
                    htmlFor={`toc-${key}`} 
                    className={`text-sm cursor-pointer hover:text-blue-700 ${
                      isMainSection ? 'font-medium text-gray-900' : 'text-gray-700'
                    }`}
                  >
                    {hasChildren && isMainSection && '📁 '}
                    {item.title} 
                    <span className="text-gray-500 text-xs ml-1">(p. {item.page})</span>
                  </label>
                </div>
              );
            })}
          </div>
          {progressHook.selectedTocItems.size > 0 && (
            <button
              onClick={() => eventDataHook.handleProcessSelectedSections(
                state.year,
                progressHook.setProcessingResult,
                progressHook.setProcessingError,
                progressHook.setProcessingStart,
                progressHook.setProcessingEnd
              )}
              disabled={progressHook.isProcessingSections}
              className="mt-4 w-full py-2 px-4 bg-indigo-600 text-white rounded hover:bg-indigo-700 disabled:bg-indigo-300"
            >
              {progressHook.isProcessingSections ? "Processing Sections..." : `Process ${progressHook.selectedTocItems.size} Selected Section(s)`}
            </button>
          )}
          {progressHook.processSectionsError && (
            <div className="mt-2 p-3 bg-red-100 text-red-700 rounded">
              {progressHook.processSectionsError}
            </div>
          )}
          {progressHook.processedSectionsResult && (
            <div className="mt-2 p-3 bg-green-50 text-green-700 rounded">
              <h4 className="font-semibold">Sections Processed Successfully!</h4>
              <p className="text-sm">Saved to: {progressHook.processedSectionsResult.saved_text_path}</p>
              <p className="text-sm">Extracted Length: {progressHook.processedSectionsResult.extracted_text_length} chars</p>
              <p className="text-xs mt-1">Sample: <pre className="whitespace-pre-wrap bg-gray-100 p-1 rounded text-xs">{progressHook.processedSectionsResult.sample_text}</pre></p>
            </div>
          )}
        </div>
      )}
    </div>
  );

  // Step 2: Event Selection
  const renderEventSelectionStep = () => (
    <div className="space-y-6">
      {renderEventSwitchDialog()}

      {/* Current Event Display */}
      <div className="bg-white p-6 rounded-lg shadow">
        <h2 className="text-xl font-bold mb-4">Current Event</h2>
        
        {state.isLoadingCurrentEvent ? (
          <div className="p-2 text-blue-600">Loading current event...</div>
        ) : (
          <div className="mb-6">
            <div className="flex items-center">
              <span className="font-semibold mr-2">Active Event:</span>
              {state.currentEvent.event_key ? (
                <span className="px-3 py-1 rounded-full bg-blue-100 text-blue-800 font-medium">
                  {state.currentEvent.event_name || state.currentEvent.event_key} ({state.currentEvent.year})
                </span>
              ) : (
                <span className="px-3 py-1 rounded-full bg-yellow-100 text-yellow-800">
                  None Selected
                </span>
              )}
            </div>
          </div>
        )}
      </div>

      <EventSelector
        year={state.year}
        selectedEvent={state.selectedEvent}
        selectedEventName={state.selectedEventName}
        events={state.events}
        groupedEvents={state.groupedEvents}
        loadingEvents={state.loadingEvents}
        eventsError={state.eventsError}
        isSettingUpEvent={state.isSettingUpEvent}
        onYearChange={actions.handleYearChange}
        onEventChange={actions.handleEventChange}
        onEventSetup={actions.checkForEventSwitch}
      />

      {/* Success Message */}
      {state.setupResult && !state.isSettingUpEvent && (
        <div className="bg-green-50 border border-green-200 p-4 rounded-lg">
          <div className="flex items-center">
            <svg className="w-5 h-5 text-green-600 mr-2" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd"/>
            </svg>
            <span className="text-green-800 font-medium">Event successfully configured!</span>
          </div>
        </div>
      )}

      {/* Sample Teams Display */}
      {state.setupResult && (
        <div className="bg-white p-6 rounded-lg shadow">
          <h2 className="text-xl font-bold mb-4">Event Setup Details</h2>
          
          {state.setupResult.sample_teams && state.setupResult.sample_teams.length > 0 ? (
            <>
              <h3 className="text-lg font-semibold mb-2">Sample Teams from {state.selectedEventName || state.currentEvent.event_name}</h3>
              <p className="text-sm text-gray-600 mb-4">
                These teams are participating in the selected event. This confirms we're connected to the correct event data.
              </p>
              <div className="overflow-x-auto">
                <table className="min-w-full border">
                  <thead className="bg-gray-100">
                    <tr>
                      <th className="border px-4 py-2">Team #</th>
                      <th className="border px-4 py-2">Name</th>
                      <th className="border px-4 py-2">EPA</th>
                    </tr>
                  </thead>
                  <tbody>
                    {state.setupResult.sample_teams.map((team: any) => (
                      <tr key={team.team_number}>
                        <td className="border px-4 py-2">{team.team_number}</td>
                        <td className="border px-4 py-2">{team.team_name}</td>
                        <td className="border px-4 py-2">{team.epa_total?.toFixed(1) || "N/A"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </>
          ) : (
            <p className="text-gray-600">No sample teams data available. Check console for setup response.</p>
          )}
        </div>
      )}

      {/* Event Archive Manager */}
      <div id="archiveSection" className="bg-white p-6 rounded-lg shadow">
        <h2 className="text-xl font-bold mb-4">Event Management</h2>
        
        <EventArchiveManager
          currentEventKey={state.currentEvent.event_key || state.selectedEvent}
          currentYear={state.currentEvent.year || state.year}
          onArchiveSuccess={() => {
            console.log("Archive success callback triggered");
            // Handle archive success - implementation simplified for refactoring
          }}
          onRestoreSuccess={() => {
            console.log("Restore success callback triggered");
            window.location.reload();
          }}
        />
      </div>
    </div>
  );

  // Step 3: Database Alignment
  const renderDatabaseAlignmentStep = () => (
    <div className="space-y-6">
      <div className="bg-white p-6 rounded-lg shadow">
        <SheetConfigManager
          currentEventKey={state.currentEvent.event_key || state.selectedEvent}
          currentYear={state.currentEvent.year || state.year}
          onConfigurationChange={actions.handleSheetConfigurationChange}
          onConfigurationConfirmed={actions.handleSheetConfigurationChange}
        />
      </div>
    </div>
  );

  // Step 4: Setup Complete Summary
  const renderSetupCompleteStep = () => (
    <div className="space-y-6">
      <div className="bg-white p-6 rounded-lg shadow">
        <div className="flex items-center mb-6">
          <svg className="w-8 h-8 text-green-600 mr-3" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd"/>
          </svg>
          <h2 className="text-2xl font-bold text-green-800">Setup Complete!</h2>
        </div>

        <p className="text-gray-600 mb-6">
          Your FRC Scouting Assistant has been successfully configured. Here's a summary of your setup:
        </p>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Manual Configuration */}
          <div className="bg-gray-50 p-4 rounded-lg">
            <h3 className="font-semibold text-lg mb-3 flex items-center">
              <svg className="w-5 h-5 mr-2 text-blue-600" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4zm2 6a1 1 0 011-1h6a1 1 0 110 2H7a1 1 0 01-1-1zm1 3a1 1 0 100 2h6a1 1 0 100-2H7z" clipRule="evenodd"/>
              </svg>
              Game Manual
            </h3>
            {state.currentManualInfo ? (
              <div>
                <p className="text-sm text-gray-700">
                  <strong>File:</strong> {state.currentManualInfo.original_filename}
                </p>
                <p className="text-sm text-gray-700">
                  <strong>Year:</strong> {state.year}
                </p>
                <p className="text-sm text-gray-700">
                  <strong>Status:</strong> {state.currentManualInfo.using_cached_manual ? 'Loaded from database' : 'Newly uploaded'}
                </p>
                {progressHook.processedSectionsResult && (
                  <p className="text-sm text-green-700">
                    <strong>Processed Sections:</strong> {progressHook.selectedTocItems.size} sections extracted
                  </p>
                )}
              </div>
            ) : (
              <p className="text-sm text-yellow-700">Using existing manual for {state.year} or basic analysis</p>
            )}
          </div>

          {/* Event Configuration */}
          <div className="bg-gray-50 p-4 rounded-lg">
            <h3 className="font-semibold text-lg mb-3 flex items-center">
              <svg className="w-5 h-5 mr-2 text-green-600" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M6 2a1 1 0 00-1 1v1H4a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V6a2 2 0 00-2-2h-1V3a1 1 0 10-2 0v1H7V3a1 1 0 00-1-1zm0 5a1 1 0 000 2h8a1 1 0 100-2H6z" clipRule="evenodd"/>
              </svg>
              Event Selection
            </h3>
            <div>
              <p className="text-sm text-gray-700">
                <strong>Event:</strong> {state.currentEvent.event_name || state.currentEvent.event_key}
              </p>
              <p className="text-sm text-gray-700">
                <strong>Year:</strong> {state.currentEvent.year || state.year}
              </p>
              <p className="text-sm text-gray-700">
                <strong>Event Key:</strong> {state.currentEvent.event_key}
              </p>
              {state.setupResult?.sample_teams && (
                <p className="text-sm text-green-700">
                  <strong>Teams Found:</strong> {state.setupResult.sample_teams.length} sample teams loaded
                </p>
              )}
            </div>
          </div>

          {/* Sheets Configuration */}
          <div className="bg-gray-50 p-4 rounded-lg md:col-span-2">
            <h3 className="font-semibold text-lg mb-3 flex items-center">
              <svg className="w-5 h-5 mr-2 text-purple-600" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M3 4a1 1 0 011-1h12a1 1 0 011 1v2a1 1 0 01-1 1H4a1 1 0 01-1-1V4zm0 4a1 1 0 011-1h12a1 1 0 011 1v6a1 1 0 01-1 1H4a1 1 0 01-1-1V8z" clipRule="evenodd"/>
              </svg>
              Google Sheets Configuration
            </h3>
            {state.completedSteps.has(3) ? (
              <p className="text-sm text-green-700">
                ✓ Google Sheets configuration has been completed. Sheet mappings are ready for field selection.
              </p>
            ) : (
              <p className="text-sm text-yellow-700">
                Configuration in progress - please complete the sheets setup above.
              </p>
            )}
          </div>
        </div>

        {/* Action Buttons */}
        <div className="mt-8 space-y-4">
          <div className="flex flex-col sm:flex-row gap-4">
            <button
              onClick={handleContinue}
              className="flex-1 py-3 px-6 bg-green-600 text-white rounded-lg hover:bg-green-700 font-semibold"
            >
              Continue to Field Selection →
            </button>
            
            <button
              onClick={() => actions.handleStepClick(1)}
              className="flex-1 py-3 px-6 bg-gray-500 text-white rounded-lg hover:bg-gray-600"
            >
              Review Setup Steps
            </button>
          </div>
          
          <p className="text-center text-sm text-gray-500">
            You can return to setup at any time to modify these configurations.
          </p>
        </div>
      </div>
    </div>
  );

  // Render step content
  const renderStepContent = () => {
    switch (state.currentStep) {
      case 1:
        return renderManualTrainingStep();
      case 2:
        return renderEventSelectionStep();
      case 3:
        return renderDatabaseAlignmentStep();
      case 4:
        return renderSetupCompleteStep();
      default:
        return null;
    }
  };

  return (
    <div className="max-w-7xl mx-auto p-6">
      <h1 className="text-3xl font-bold mb-8">FRC Scouting Assistant Setup</h1>

      <StepIndicator
        currentStep={state.currentStep}
        completedSteps={state.completedSteps}
        onStepClick={actions.handleStepClick}
      />

      {renderStepContent()}

      <SetupActions
        currentStep={state.currentStep}
        canProceedToNextStep={canProceedToNextStep()}
        onPreviousStep={actions.handlePreviousStep}
        onNextStep={actions.handleNextStep}
      />
    </div>
  );
};

export default Setup;