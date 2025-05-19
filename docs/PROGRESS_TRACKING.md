# Progress Tracking Implementation

This document details the progress tracking system implemented for long-running operations in the FRC GPT Scouting App.

## Architecture Overview

The progress tracking system consists of three main components:

1. **Backend Progress Tracker Service** - Manages operation state
2. **Progress API Endpoint** - Provides status updates
3. **Frontend Progress Component** - Displays real-time updates

## Backend Implementation

### Progress Tracker Service

Location: `backend/app/services/progress_tracker.py`

Key features:
- In-memory storage of operation progress
- Thread-safe updates
- Automatic stale operation detection
- Estimated time remaining calculations

```python
class ProgressTracker:
    @classmethod
    def create_tracker(cls, operation_id: str) -> 'ProgressTracker':
        """Create a new progress tracker for an operation"""
        
    def update(self, progress: float, message: str, current_step: str = "", status: str = "active"):
        """Update the progress of an operation"""
        
    def complete(self, message: str = "Operation completed successfully"):
        """Mark an operation as completed"""
        
    def fail(self, message: str = "Operation failed"):
        """Mark an operation as failed"""
```

### Progress API

Location: `backend/app/api/progress.py`

Endpoints:
- `GET /api/progress/{operation_id}` - Get specific operation progress
- `GET /api/progress/` - List all active operations

### Integration with Picklist Generation

The picklist generator service uses threading to provide non-blocking progress updates:

```python
# Create progress tracker
progress_tracker = ProgressTracker.create_tracker(cache_key)

# Threading for API call
def make_api_call():
    response = client.chat.completions.create(...)
    api_complete.set()

api_thread = threading.Thread(target=make_api_call)
api_thread.start()

# Update progress while waiting
while not api_complete.is_set():
    elapsed = time.time() - start_wait_time
    progress = min(50, 20 + (elapsed / 50) * 30)
    progress_tracker.update(progress, f"Analyzing teams... ({elapsed:.0f}s)")
    await asyncio.sleep(1.0)
```

## Frontend Implementation

### Progress Tracker Component

Location: `frontend/src/components/ProgressTracker.tsx`

Features:
- Polling for updates (configurable interval)
- Visual progress bar
- Status indicators
- Time remaining estimates
- Completed steps tracking

```typescript
interface ProgressTrackerProps {
  operationId: string;
  onComplete?: (success: boolean) => void;
  pollingInterval?: number; // Default: 2000ms
}
```

### Usage in Picklist Generation

Location: `frontend/src/pages/PicklistNew.tsx`

```typescript
// Generate cache key before API call
const cacheKey = `${yourTeamNumber}_${activeTab}_${Date.now()}`;
setProgressOperationId(cacheKey);

// Make API call with cache key
const response = await fetch('/api/picklist/generate', {
  method: 'POST',
  body: JSON.stringify({
    ...params,
    cache_key: cacheKey
  })
});

// Progress component displays updates
{progressOperationId && (
  <ProgressTracker 
    operationId={progressOperationId}
    pollingInterval={500}
    onComplete={(success) => {
      setSuccessMessage(success ? 'Complete!' : 'Failed');
    }}
  />
)}
```

## Progress Stages

For picklist generation, progress moves through these stages:

1. **Initialization (5%)** - Creating tracker, preparing data
2. **Preparation (10%)** - Condensing team data
3. **API Call (20%)** - Sending to GPT
4. **Processing (20-50%)** - Waiting for GPT (dynamic)
5. **Response (60%)** - GPT complete
6. **Parsing (70%)** - Processing response
7. **Deduplication (80%)** - Finalizing data
8. **Complete (100%)** - Operation finished

## Best Practices

### Backend
- Create tracker immediately when operation starts
- Update progress at meaningful intervals (not too frequent)
- Include descriptive messages for each stage
- Always mark complete/failed at end
- Clean up old operations periodically

### Frontend
- Generate cache key before API call
- Set reasonable polling intervals
- Handle 404 gracefully (operation not started yet)
- Clear operation ID after completion
- Provide user feedback on completion

## Error Handling

The system handles several error scenarios:

1. **Operation Not Found** - Returns 404, frontend handles gracefully
2. **Stalled Operations** - Auto-detected after 60s of no updates
3. **Failed Operations** - Marked with failure status and message
4. **Network Errors** - Frontend retries polling

## Performance Considerations

- Polling interval: 500ms for responsive updates
- Progress updates: Every 1s during long operations
- Memory cleanup: Stale operations removed after 1 hour
- Thread safety: Updates are thread-safe

## Future Enhancements

1. **WebSocket Support** - Replace polling with real-time updates
2. **Persistent Storage** - Store progress in database
3. **Cancellation** - Allow users to cancel operations
4. **Partial Results** - Show intermediate results
5. **Progress History** - Track historical performance

## Debugging

Progress tracking can be debugged via:

1. Backend logs in `picklist_generator.log`
2. Progress API endpoint responses
3. Browser developer tools (Network tab)
4. React Developer Tools

## Code Examples

### Creating a Progress-Tracked Operation

```python
async def long_operation(operation_id: str):
    tracker = ProgressTracker.create_tracker(operation_id)
    
    try:
        tracker.update(10, "Starting operation...")
        
        # Do work...
        result = await some_async_work()
        tracker.update(50, "Halfway complete...")
        
        # More work...
        final_result = await more_async_work()
        tracker.update(90, "Finalizing...")
        
        tracker.complete("Operation successful")
        return final_result
        
    except Exception as e:
        tracker.fail(f"Operation failed: {str(e)}")
        raise
```

### Monitoring Progress in Frontend

```typescript
const MonitoredOperation: React.FC = () => {
  const [operationId, setOperationId] = useState<string | null>(null);
  
  const startOperation = async () => {
    const id = `op_${Date.now()}`;
    setOperationId(id);
    
    const response = await fetch('/api/start-operation', {
      method: 'POST',
      body: JSON.stringify({ operation_id: id })
    });
  };
  
  return (
    <div>
      <button onClick={startOperation}>Start Operation</button>
      {operationId && (
        <ProgressTracker 
          operationId={operationId}
          onComplete={() => setOperationId(null)}
        />
      )}
    </div>
  );
};
```