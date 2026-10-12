/**
 * Track Color Management Utilities
 * Provides deterministic, stable, high-contrast colors for confirmed tracks
 * Distinguishes unconfirmed detections and ensures consistency across player and dashboard views.
 */

// Curated high-contrast palette optimized for visibility on varied CCTV backgrounds (dark/light)
export const TRACK_PALETTE = [
  '#00E5FF', // Cyan / Electric Blue
  '#FFD600', // Vivid Gold / Yellow
  '#00E676', // Bright Emerald Green
  '#FF4081', // Vivid Rose / Pink
  '#7C4DFF', // Deep Purple / Violet
  '#FF6E40', // Coral / Neon Orange
  '#1DE9B6', // Bright Teal / Aqua
  '#E040FB', // Neon Magenta
  '#69F0AE', // Mint Neon
  '#FFAB00', // Amber
  '#40C4FF', // Light Sapphire Blue
  '#FF5252', // Vivid Coral Red
  '#B388FF', // Soft Lavender
  '#EEFF41', // Neon Lime
  '#FF80AB', // Flamingo Pink
  '#00B0FF', // Sky Blue
];

/**
 * Deterministically hash an ID to an integer
 */
const hashId = (id) => {
  if (id === null || id === undefined) return 0;
  const str = String(id);
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    hash = (hash << 5) - hash + str.charCodeAt(i);
    hash |= 0; // Convert to 32bit int
  }
  return Math.abs(hash);
};

/**
 * Get stable, deterministic color for a given track
 * @param {string|number} trackId - Tracking identifier
 * @param {boolean} isConfirmed - Whether track is confirmed (negative IDs = unconfirmed)
 */
export const getTrackColor = (trackId, isConfirmed = true) => {
  const numericId = parseInt(String(trackId), 10);
  
  // Unconfirmed detection or negative tracker ID
  if (!isConfirmed || (numericId < 0 && !isNaN(numericId))) {
    return '#8b949e'; // Muted slate gray for temporary unconfirmed detections
  }

  const index = hashId(trackId) % TRACK_PALETTE.length;
  return TRACK_PALETTE[index];
};

/**
 * Determine high-contrast text color (black or white) for a background hex
 */
export const getContrastTextColor = (hexColor) => {
  if (!hexColor || !hexColor.startsWith('#')) return '#ffffff';
  let hex = hexColor.replace('#', '');
  if (hex.length === 3) {
    hex = hex.split('').map(c => c + c).join('');
  }
  const r = parseInt(hex.substring(0, 2), 16) || 0;
  const g = parseInt(hex.substring(2, 4), 16) || 0;
  const b = parseInt(hex.substring(4, 6), 16) || 0;

  // Relative luminance calculation
  const yiq = (r * 299 + g * 587 + b * 114) / 1000;
  return yiq >= 140 ? '#0d1117' : '#ffffff';
};

/**
 * Check if a track ID represents an unconfirmed detection
 */
export const isUnconfirmedTrack = (trackId, confirmedFlag) => {
  if (confirmedFlag === false) return true;
  const num = parseInt(String(trackId), 10);
  return !isNaN(num) && num < 0;
};
