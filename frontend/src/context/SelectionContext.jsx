/**
 * Selection Context
 * Global state for selected anomalies, events, tracks, scenes
 * Enables synchronized selection across video, timeline, tabs, and evidence panel
 */
import { createContext, useContext, useState } from 'react';

const SelectionContext = createContext(null);

export const SelectionProvider = ({ children }) => {
  const [selectedItem, setSelectedItem] = useState(null);
  const [selectedType, setSelectedType] = useState(null); // 'anomaly' | 'event' | 'track' | 'scene' | 'relationship'

  const selectAnomaly = (anomaly) => {
    setSelectedItem(anomaly);
    setSelectedType('anomaly');
  };

  const selectEvent = (event) => {
    setSelectedItem(event);
    setSelectedType('event');
  };

  const selectTrack = (track) => {
    setSelectedItem(track);
    setSelectedType('track');
  };

  const selectScene = (scene) => {
    setSelectedItem(scene);
    setSelectedType('scene');
  };

  const selectRelationship = (relationship) => {
    setSelectedItem(relationship);
    setSelectedType('relationship');
  };

  const clearSelection = () => {
    setSelectedItem(null);
    setSelectedType(null);
  };

  const value = {
    selectedItem,
    selectedType,
    selectAnomaly,
    selectEvent,
    selectTrack,
    selectScene,
    selectRelationship,
    clearSelection,
  };

  return (
    <SelectionContext.Provider value={value}>
      {children}
    </SelectionContext.Provider>
  );
};

export const useSelection = () => {
  const context = useContext(SelectionContext);
  if (!context) {
    throw new Error('useSelection must be used within SelectionProvider');
  }
  return context;
};

export default SelectionContext;
