import React, { useState, useMemo, useCallback } from 'react';
import { HeatmapProps, HeatmapCell } from '../types/graphicalAnalysis';
import { getHeatmapCellColor, formatHeatmapValue } from '../utils/heatmapDataProcessing';

interface TooltipData {
  cell: HeatmapCell;
  position: { x: number; y: number };
}

const ConsistencyHeatmap: React.FC<HeatmapProps> = ({
  data,
  selectedMetric,
  showMode,
  normalizationMode,
  onCellHover,
  onCellClick,
  height = 400
}) => {
  const [tooltip, setTooltip] = useState<TooltipData | null>(null);
  
  // Create a lookup map for cells by team and sequence position
  const cellMap = useMemo(() => {
    const map: { [key: string]: HeatmapCell[] } = {};
    
    // Group cells by team
    data.cells.forEach(cell => {
      const teamKey = cell.teamNumber.toString();
      if (!map[teamKey]) {
        map[teamKey] = [];
      }
      map[teamKey].push(cell);
    });
    
    // Sort each team's matches chronologically
    Object.keys(map).forEach(teamKey => {
      map[teamKey].sort((a, b) => a.matchNumber - b.matchNumber);
    });
    
    return map;
  }, [data.cells]);
  
  // Calculate grid dimensions
  const teamCount = data.teams.length;
  const matchCount = data.matches.length;
  
  // Cell dimensions - adjust width based on match count to fit better
  const maxWidth = 1200; // Maximum container width
  const cellWidth = Math.max(35, Math.min(60, (maxWidth - 120) / matchCount));
  const cellHeight = Math.max(30, Math.min(50, (height - 100) / teamCount));
  
  // Grid dimensions
  const gridWidth = matchCount * cellWidth + 120; // 120px for team labels
  const gridHeight = teamCount * cellHeight + 100; // 100px for headers and legend
  
  console.log('Heatmap dimensions:', {
    teamCount,
    matchCount,
    cellHeight,
    cellWidth,
    gridHeight,
    containerHeight: height
  });
  
  const handleCellMouseEnter = useCallback((cell: HeatmapCell, event: React.MouseEvent) => {
    const rect = event.currentTarget.getBoundingClientRect();
    const tooltipData: TooltipData = {
      cell,
      position: {
        x: rect.left + rect.width / 2,
        y: rect.top - 10
      }
    };
    setTooltip(tooltipData);
    onCellHover?.(cell);
  }, [onCellHover]);
  
  const handleCellMouseLeave = useCallback(() => {
    setTooltip(null);
    onCellHover?.(null);
  }, [onCellHover]);
  
  const handleCellClick = useCallback((cell: HeatmapCell) => {
    onCellClick?.(cell);
  }, [onCellClick]);
  
  // Show performance warning for large datasets
  const isLargeDataset = teamCount > 50 || matchCount > 50;
  const totalCells = teamCount * matchCount;
  
  return (
    <div className="relative">
      {/* Performance Warning */}
      {isLargeDataset && (
        <div className="mb-4 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
          <div className="flex items-center">
            <svg className="w-5 h-5 text-yellow-600 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
            </svg>
            <div>
              <p className="text-sm font-medium text-yellow-800">
                Large Dataset ({teamCount} teams × {matchCount} matches = {totalCells} cells)
              </p>
              <p className="text-xs text-yellow-600">
                Performance may be impacted. Consider filtering to fewer teams or using a smaller dataset.
              </p>
            </div>
          </div>
        </div>
      )}
      
      {/* Heatmap Grid */}
      <div 
        className="overflow-auto border border-gray-300 rounded-lg bg-white"
        style={{ maxHeight: height + 100, maxWidth: '100%' }}
      >
        <div 
          className="relative bg-white"
          style={{ 
            width: gridWidth, 
            height: gridHeight,
            minWidth: 600 // Ensure minimum width for readability
          }}
        >
          {/* Column Headers (Match Numbers) */}
          <div className="absolute top-0" style={{ left: 120 }}>
            <div className="flex">
              {data.matches.map((match, index) => (
                <div
                  key={match.matchNumber}
                  className="flex items-center justify-center text-xs font-medium text-gray-700 border-b border-gray-200 bg-gray-50"
                  style={{
                    width: cellWidth,
                    height: 40,
                    minWidth: 35
                  }}
                  title={`Match ${match.matchNumber}`}
                >
                  <span className="truncate px-1">{match.matchNumber}</span>
                </div>
              ))}
            </div>
          </div>
          
          {/* Row Headers (Team Names) */}
          <div className="absolute left-0" style={{ top: 40 }}>
            <div className="flex flex-col">
              {data.teams.map((team, index) => (
                <div
                  key={team.teamNumber}
                  className="flex items-center justify-end text-xs font-medium text-gray-700 border-r border-gray-200 bg-gray-50 px-2"
                  style={{
                    width: 120,
                    height: cellHeight,
                    minHeight: 25
                  }}
                >
                  <span className="truncate">
                    {team.teamNumber} - {team.nickname}
                  </span>
                </div>
              ))}
            </div>
          </div>
          
          {/* Heatmap Cells */}
          <div className="absolute" style={{ top: 40, left: 120 }}>
            {data.teams.map((team, teamIndex) => {
              const teamCells = cellMap[team.teamNumber.toString()] || [];
              
              return teamCells.map((cell, cellIndex) => {
                const backgroundColor = getHeatmapCellColor(
                  cell.value, 
                  data.valueRange.min, 
                  data.valueRange.max, 
                  cell.isValid, 
                  data.colorScale
                );
                
                return (
                  <div
                    key={`${team.teamNumber}-${cell.matchNumber}`}
                    className="border border-gray-200 flex items-center justify-center text-xs font-medium cursor-pointer hover:ring-2 hover:ring-blue-500 hover:z-10 transition-all duration-150"
                    style={{
                      width: cellWidth,
                      height: cellHeight,
                      backgroundColor,
                      color: cell.value > (data.valueRange.min + data.valueRange.max) / 2 ? '#ffffff' : '#374151',
                      minWidth: 35,
                      minHeight: 25,
                      position: 'absolute',
                      top: teamIndex * cellHeight,
                      left: cellIndex * cellWidth
                    }}
                    onMouseEnter={(e) => handleCellMouseEnter(cell, e)}
                    onMouseLeave={handleCellMouseLeave}
                    onClick={() => handleCellClick(cell)}
                    title={`Team ${team.teamNumber} - Match ${cell.matchNumber}: ${formatHeatmapValue(cell.value, cell.isValid)}`}
                  >
                    {formatHeatmapValue(cell.value, cell.isValid)}
                  </div>
                );
              });
            })}
          </div>
          
          {/* Legend */}
          <div className="absolute bottom-0 left-0 right-0 bg-gray-50 border-t border-gray-200 p-3">
            <div className="flex items-center justify-between">
              <div className="text-xs text-gray-600">
                <span className="font-medium">
                  {selectedMetric.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())} 
                  ({showMode === 'auto' ? 'Autonomous' : showMode === 'teleop' ? 'Teleop' : 'Total'})
                </span>
                <span className="text-gray-500 ml-2">
                  • Sequential view: Each team shows their own matches in chronological order
                </span>
              </div>
              
              <div className="flex items-center space-x-4">
                <div className="flex items-center space-x-2">
                  <div className="w-4 h-4 bg-gradient-to-r from-red-500 to-green-500 rounded"></div>
                  <span className="text-xs text-gray-600">
                    {data.valueRange.min.toFixed(1)} - {data.valueRange.max.toFixed(1)}
                  </span>
                </div>
                <div className="flex items-center space-x-2">
                  <div className="w-4 h-4 bg-gray-300 rounded"></div>
                  <span className="text-xs text-gray-600">No Data</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      {/* Tooltip */}
      {tooltip && (
        <div
          className="absolute z-50 bg-gray-900 text-white text-xs rounded-lg px-3 py-2 shadow-lg pointer-events-none"
          style={{
            left: tooltip.position.x,
            top: tooltip.position.y,
            transform: 'translate(-50%, -100%)'
          }}
        >
          <div className="font-medium">
            Team {tooltip.cell.teamNumber} - Match {tooltip.cell.matchNumber}
          </div>
          <div className="text-gray-300">
            {tooltip.cell.isValid ? (
              <>
                <div>Value: {formatHeatmapValue(tooltip.cell.value, tooltip.cell.isValid)}</div>
                <div>Actual Match: {tooltip.cell.matchNumber}</div>
                {tooltip.cell.matchType && (
                  <div>Type: {tooltip.cell.matchType}</div>
                )}
                {tooltip.cell.allianceColor && (
                  <div>Alliance: {tooltip.cell.allianceColor}</div>
                )}
              </>
            ) : (
              <div>No data available</div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default ConsistencyHeatmap;