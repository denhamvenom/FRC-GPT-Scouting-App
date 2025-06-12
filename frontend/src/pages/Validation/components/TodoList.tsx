// frontend/src/pages/Validation/components/TodoList.tsx

import React from 'react';
import { TodoItem } from '../types';

interface TodoListProps {
  todoList: TodoItem[];
  onUpdateStatus: (item: TodoItem, status: 'completed' | 'cancelled') => void;
}

export const TodoList: React.FC<TodoListProps> = ({
  todoList = [],  // Add default empty array
  onUpdateStatus,
}) => {
  const pendingItems = todoList.filter(item => item.status === 'pending');
  const completedItems = todoList.filter(item => item.status === 'completed');
  const cancelledItems = todoList.filter(item => item.status === 'cancelled');

  const formatTimestamp = (timestamp: string) => {
    return new Date(timestamp).toLocaleString();
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'pending': return 'bg-yellow-100 text-yellow-800';
      case 'completed': return 'bg-green-100 text-green-800';
      case 'cancelled': return 'bg-gray-100 text-gray-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  if (todoList.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500">
        <div className="text-4xl mb-2">📝</div>
        <div className="text-lg font-medium">No to-do items</div>
        <div>Virtual scouting tasks will appear here when matches need attention.</div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Pending Items */}
      {pendingItems.length > 0 && (
        <div>
          <h3 className="text-lg font-semibold mb-3 text-yellow-700">
            Pending Tasks ({pendingItems.length})
          </h3>
          <div className="space-y-2">
            {pendingItems.map((item, index) => (
              <div
                key={`${item.team_number}-${item.match_number}-${index}`}
                className="border border-yellow-200 rounded-lg p-4 bg-yellow-50"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <div className="font-medium">
                      Team {item.team_number} - Match {item.match_number}
                    </div>
                    <span className={`px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(item.status)}`}>
                      {item.status.toUpperCase()}
                    </span>
                  </div>
                  <div className="flex space-x-2">
                    <button
                      onClick={() => onUpdateStatus(item, 'completed')}
                      className="px-3 py-1 text-sm bg-green-600 text-white rounded hover:bg-green-700"
                    >
                      Mark Complete
                    </button>
                    <button
                      onClick={() => onUpdateStatus(item, 'cancelled')}
                      className="px-3 py-1 text-sm bg-gray-600 text-white rounded hover:bg-gray-700"
                    >
                      Cancel
                    </button>
                  </div>
                </div>
                <div className="mt-2 text-sm text-gray-600">
                  Added: {formatTimestamp(item.added_timestamp)}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Completed Items */}
      {completedItems.length > 0 && (
        <div>
          <h3 className="text-lg font-semibold mb-3 text-green-700">
            Completed Tasks ({completedItems.length})
          </h3>
          <div className="space-y-2">
            {completedItems.map((item, index) => (
              <div
                key={`${item.team_number}-${item.match_number}-${index}`}
                className="border border-green-200 rounded-lg p-4 bg-green-50"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <div className="font-medium">
                      Team {item.team_number} - Match {item.match_number}
                    </div>
                    <span className={`px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(item.status)}`}>
                      ✓ {item.status.toUpperCase()}
                    </span>
                  </div>
                </div>
                <div className="mt-2 text-sm text-gray-600">
                  <div>Added: {formatTimestamp(item.added_timestamp)}</div>
                  {item.updated_timestamp && (
                    <div>Completed: {formatTimestamp(item.updated_timestamp)}</div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Cancelled Items */}
      {cancelledItems.length > 0 && (
        <div>
          <h3 className="text-lg font-semibold mb-3 text-gray-700">
            Cancelled Tasks ({cancelledItems.length})
          </h3>
          <div className="space-y-2">
            {cancelledItems.map((item, index) => (
              <div
                key={`${item.team_number}-${item.match_number}-${index}`}
                className="border border-gray-200 rounded-lg p-4 bg-gray-50"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <div className="font-medium text-gray-600">
                      Team {item.team_number} - Match {item.match_number}
                    </div>
                    <span className={`px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(item.status)}`}>
                      {item.status.toUpperCase()}
                    </span>
                  </div>
                </div>
                <div className="mt-2 text-sm text-gray-500">
                  <div>Added: {formatTimestamp(item.added_timestamp)}</div>
                  {item.updated_timestamp && (
                    <div>Cancelled: {formatTimestamp(item.updated_timestamp)}</div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};