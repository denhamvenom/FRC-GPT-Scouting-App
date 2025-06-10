import { useCallback } from 'react';
import type { TocItemType, CurrentManualInfo } from '../types';

export const useEventData = (
  currentManualInfo: CurrentManualInfo | null,
  selectedTocItems: Map<string, TocItemType>,
  onUpdateSelectedTocItems: (items: Map<string, TocItemType>) => void
) => {
  const handleTocItemToggle = useCallback((item: TocItemType) => {
    const key = `${item.title}-${item.page}`;
    const isCurrentlySelected = selectedTocItems.has(key);
    
    const newMap = new Map(selectedTocItems);
    
    if (isCurrentlySelected) {
      // Deselecting: Remove this item and all its children
      newMap.delete(key);
      
      // Find and remove all child items (higher level numbers after this item)
      if (currentManualInfo?.toc_data) {
        const currentIndex = currentManualInfo.toc_data.findIndex(tocItem => 
          `${tocItem.title}-${tocItem.page}` === key
        );
        
        if (currentIndex !== -1) {
          // Look ahead for child items (items with higher level that come after this one)
          for (let i = currentIndex + 1; i < currentManualInfo.toc_data.length; i++) {
            const nextItem = currentManualInfo.toc_data[i];
            
            // If we encounter an item at the same or lower level, stop
            if (nextItem.level <= item.level) {
              break;
            }
            
            // This is a child item, remove it
            const childKey = `${nextItem.title}-${nextItem.page}`;
            newMap.delete(childKey);
          }
        }
      }
    } else {
      // Selecting: Add this item and all its children
      newMap.set(key, item);
      
      // Find and add all child items
      if (currentManualInfo?.toc_data) {
        const currentIndex = currentManualInfo.toc_data.findIndex(tocItem => 
          `${tocItem.title}-${tocItem.page}` === key
        );
        
        if (currentIndex !== -1) {
          // Look ahead for child items
          for (let i = currentIndex + 1; i < currentManualInfo.toc_data.length; i++) {
            const nextItem = currentManualInfo.toc_data[i];
            
            // If we encounter an item at the same or lower level, stop
            if (nextItem.level <= item.level) {
              break;
            }
            
            // This is a child item, add it
            const childKey = `${nextItem.title}-${nextItem.page}`;
            newMap.set(childKey, nextItem);
          }
        }
      }
      
      // Check if we should auto-select parent items
      // If all siblings are now selected, select the parent too
      if (currentManualInfo?.toc_data && item.level > 1) {
        autoSelectParents(newMap, item, currentManualInfo.toc_data);
      }
    }
    
    onUpdateSelectedTocItems(newMap);
  }, [currentManualInfo, selectedTocItems, onUpdateSelectedTocItems]);

  // Helper function to auto-select parent items when all children are selected
  const autoSelectParents = (
    selectionMap: Map<string, TocItemType>, 
    childItem: TocItemType,
    tocData: TocItemType[]
  ) => {
    if (childItem.level <= 1) return;
    
    const childIndex = tocData.findIndex(item => 
      `${item.title}-${item.page}` === `${childItem.title}-${childItem.page}`
    );
    
    if (childIndex === -1) return;
    
    // Find the parent (previous item with lower level)
    let parentIndex = -1;
    for (let i = childIndex - 1; i >= 0; i--) {
      if (tocData[i].level < childItem.level) {
        parentIndex = i;
        break;
      }
    }
    
    if (parentIndex === -1) return;
    
    const parentItem = tocData[parentIndex];
    const parentKey = `${parentItem.title}-${parentItem.page}`;
    
    // Find all children of this parent
    const parentChildren: TocItemType[] = [];
    for (let i = parentIndex + 1; i < tocData.length; i++) {
      const item = tocData[i];
      
      // If we hit an item at the same or lower level than parent, stop
      if (item.level <= parentItem.level) {
        break;
      }
      
      // If this is a direct child (one level deeper), add it
      if (item.level === parentItem.level + 1) {
        parentChildren.push(item);
      }
    }
    
    // Check if all direct children are selected
    const allChildrenSelected = parentChildren.every(child => {
      const childKey = `${child.title}-${child.page}`;
      return selectionMap.has(childKey);
    });
    
    // If all children are selected and parent isn't already selected, select parent
    if (allChildrenSelected && !selectionMap.has(parentKey)) {
      selectionMap.set(parentKey, parentItem);
      
      // Recursively check if we should select grandparent
      autoSelectParents(selectionMap, parentItem, tocData);
    }
  };

  const handleProcessSelectedSections = async (
    year: number,
    onSuccess: (result: any) => void,
    onError: (error: string) => void,
    onStart: () => void,
    onEnd: () => void
  ) => {
    if (!currentManualInfo?.saved_manual_filename || selectedTocItems.size === 0) {
      onError("Manual information or selected ToC items are missing.");
      return;
    }

    onStart();

    const payload = {
      manual_identifier: currentManualInfo.saved_manual_filename,
      year: year,
      selected_sections: Array.from(selectedTocItems.values()),
    };

    try {
      const response = await fetch("http://localhost:8000/api/manuals/process-sections", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      });

      const data = await response.json();

      if (response.ok) {
        onSuccess(data);
      } else {
        onError(data.detail || "Failed to process selected sections.");
      }
    } catch (err) {
      onError("Error connecting to server for section processing.");
      console.error("Error processing sections:", err);
    } finally {
      onEnd();
    }
  };

  const formatTimestamp = (timestamp?: string) => {
    if (!timestamp) return "N/A";
    try {
      return new Date(timestamp).toLocaleString();
    } catch (e) {
      return "Invalid Date";
    }
  };

  return {
    handleTocItemToggle,
    handleProcessSelectedSections,
    formatTimestamp
  };
};