/**
 * Writing Tone Options
 * Shared across Profile Settings, Analyze Post, Generate Post, and Schedule Prompt
 */

export const TONE_OPTIONS = [
  { value: 'professional', label: 'Professional', description: 'Polished and business-appropriate' },
  { value: 'casual', label: 'Casual', description: 'Friendly and conversational' },
  { value: 'formal', label: 'Formal', description: 'Sophisticated and highly professional' },
  { value: 'friendly', label: 'Friendly', description: 'Warm and approachable' },
  { value: 'confident', label: 'Confident', description: 'Assertive and authoritative' },
  { value: 'direct', label: 'Direct', description: 'Clear and to-the-point' },
];

export const DEFAULT_TONE = 'professional';

/**
 * Get tone label by value
 * @param {string} value - The tone value
 * @returns {string} - The tone label
 */
export const getToneLabel = (value) => {
  const tone = TONE_OPTIONS.find(t => t.value === value);
  return tone ? tone.label : 'Professional';
};

/**
 * Get tone with description
 * @param {string} value - The tone value  
 * @returns {string} - The tone label with description
 */
export const getToneWithDescription = (value) => {
  const tone = TONE_OPTIONS.find(t => t.value === value);
  return tone ? `${tone.label} - ${tone.description}` : 'Professional - Polished and business-appropriate';
};
