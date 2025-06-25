/**
 * Utility functions for formatting display text
 */

export const formatMetricName = (metric: string): string => {
  return metric
    .replace(/_/g, ' ')
    .replace(/\b\w/g, l => l.toUpperCase())
    .replace(/\bAvg\b/g, 'Average')
    .replace(/\bEpa\b/g, 'EPA')
    .replace(/\bTeleop\b/g, 'Teleop')
    .replace(/\bAuto\b/g, 'Autonomous')
    .replace(/\bTeleoperated\b/g, 'Teleoperated')
    .replace(/\bAutonomous\b/g, 'Autonomous')
    .replace(/\bPts\b/g, 'Points')
    .replace(/\bDef\b/g, 'Defense');
};