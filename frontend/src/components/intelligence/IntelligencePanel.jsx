/**
 * Intelligence Panel - Main tabbed interface for M1-M9 analysis
 */
import { useState } from 'react';
import OverviewTab from './OverviewTab';
import TracksTab from './TracksTab';
import BehaviourTab from './BehaviourTab';
import AnomaliesTab from './AnomaliesTab';
import EventsTab from './EventsTab';
import InteractionsTab from './InteractionsTab';
import ScenesTab from './ScenesTab';
import AIExplanationTab from './AIExplanationTab';

const IntelligencePanel = ({ results, onSeek, jobId }) => {
  const [activeTab, setActiveTab] = useState('overview');

  const tabs = [
    { id: 'overview', label: 'Overview', component: OverviewTab },
    { id: 'tracks', label: 'Tracks', component: TracksTab, count: results.m2_unique_tracks },
    { id: 'behaviour', label: 'Behaviour', component: BehaviourTab },
    { id: 'anomalies', label: 'Anomalies', component: AnomaliesTab, count: results.m4_total_anomalies },
    { id: 'events', label: 'Events', component: EventsTab, count: results.m5_correlated_events },
    { id: 'interactions', label: 'Interactions', component: InteractionsTab, count: results.m6_total_relationships },
    { id: 'scenes', label: 'Scenes', component: ScenesTab, count: results.m8_total_scenes },
    { id: 'ai', label: 'AI Explanation', component: AIExplanationTab }
  ];

  const ActiveComponent = tabs.find(t => t.id === activeTab)?.component || OverviewTab;

  return (
    <div style={{
      backgroundColor: '#161b22',
      borderRadius: '8px',
      border: '1px solid #30363d',
      overflow: 'hidden',
      boxShadow: '0 2px 8px rgba(0,0,0,0.4)'
    }}>
      {/* Tab Navigation */}
      <div style={{
        display: 'flex',
        borderBottom: '1px solid #30363d',
        backgroundColor: '#0d1117',
        overflowX: 'auto',
        scrollbarWidth: 'none', // For Firefox
        msOverflowStyle: 'none',  // For IE/Edge
      }}>
        {tabs.map(tab => {
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              style={{
                flex: '0 0 auto',
                padding: '14px 18px',
                border: 'none',
                backgroundColor: isActive ? '#161b22' : 'transparent',
                borderTop: isActive ? '2px solid #58a6ff' : '2px solid transparent',
                cursor: 'pointer',
                fontSize: '13px',
                fontWeight: isActive ? '600' : '500',
                color: isActive ? '#e6edf3' : '#8b949e',
                transition: 'all 0.2s ease',
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                whiteSpace: 'nowrap'
              }}
              onMouseEnter={(e) => {
                if (!isActive) {
                  e.currentTarget.style.color = '#c9d1d9';
                  e.currentTarget.style.backgroundColor = '#161b22';
                }
              }}
              onMouseLeave={(e) => {
                if (!isActive) {
                  e.currentTarget.style.color = '#8b949e';
                  e.currentTarget.style.backgroundColor = 'transparent';
                }
              }}
            >
              {tab.label}
              {tab.count !== undefined && tab.count > 0 && (
                <span style={{
                  backgroundColor: isActive ? 'rgba(88, 166, 255, 0.15)' : '#21262d',
                  border: isActive ? '1px solid rgba(88, 166, 255, 0.4)' : '1px solid #30363d',
                  color: isActive ? '#58a6ff' : '#8b949e',
                  padding: '2px 8px',
                  borderRadius: '12px',
                  fontSize: '11px',
                  fontWeight: '600'
                }}>
                  {tab.count}
                </span>
              )}
            </button>
          );
        })}
      </div>

      {/* Tab Content */}
      <div style={{
        minHeight: '400px',
        maxHeight: '600px',
        overflowY: 'auto'
      }}>
        <ActiveComponent results={results} onSeek={onSeek} jobId={jobId} />
      </div>
    </div>
  );
};

export default IntelligencePanel;
