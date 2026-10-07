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
      backgroundColor: '#fff',
      borderRadius: '8px',
      border: '1px solid #e0e0e0',
      overflow: 'hidden'
    }}>
      {/* Tab Navigation */}
      <div style={{
        display: 'flex',
        borderBottom: '2px solid #e0e0e0',
        backgroundColor: '#fafafa',
        overflowX: 'auto'
      }}>
        {tabs.map(tab => {
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              style={{
                flex: '0 0 auto',
                padding: '15px 20px',
                border: 'none',
                backgroundColor: isActive ? '#fff' : 'transparent',
                borderBottom: isActive ? '3px solid #673AB7' : '3px solid transparent',
                cursor: 'pointer',
                fontSize: '14px',
                fontWeight: isActive ? '600' : '500',
                color: isActive ? '#673AB7' : '#666',
                transition: 'all 0.2s',
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                whiteSpace: 'nowrap'
              }}
              onMouseEnter={(e) => {
                if (!isActive) {
                  e.currentTarget.style.backgroundColor = '#f5f5f5';
                  e.currentTarget.style.color = '#333';
                }
              }}
              onMouseLeave={(e) => {
                if (!isActive) {
                  e.currentTarget.style.backgroundColor = 'transparent';
                  e.currentTarget.style.color = '#666';
                }
              }}
            >
              {tab.label}
              {tab.count !== undefined && tab.count > 0 && (
                <span style={{
                  backgroundColor: isActive ? '#673AB7' : '#e0e0e0',
                  color: isActive ? '#fff' : '#666',
                  padding: '2px 8px',
                  borderRadius: '12px',
                  fontSize: '12px',
                  fontWeight: 'bold'
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
