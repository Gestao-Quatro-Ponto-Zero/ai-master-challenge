export const getScoreBadgeColor = (score) => {
  if (score >= 75) return 'badge-excellent';
  if (score >= 60) return 'badge-good';
  if (score >= 45) return 'badge-fair';
  return 'badge-poor';
};

export const getScoreBadgeLabel = (score) => {
  if (score >= 75) return 'Excellent';
  if (score >= 60) return 'Good';
  if (score >= 45) return 'Fair';
  return 'Poor';
};

export const getSuccessProbabilityLabel = (probability) => {
  const percent = Math.round(probability * 100);
  if (percent >= 80) return `${percent}% - Very High`;
  if (percent >= 60) return `${percent}% - High`;
  if (percent >= 40) return `${percent}% - Moderate`;
  return `${percent}% - Low`;
};

export const formatCurrency = (value) => {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(value);
};

export const formatNumber = (value) => {
  if (typeof value !== 'number') return '-';
  return value.toLocaleString();
};

export const daysOnPipeline = (engageDate) => {
  if (!engageDate) return 0;
  const now = new Date();
  const engage = new Date(engageDate);
  return Math.floor((now - engage) / (1000 * 60 * 60 * 24));
};

export const formatDate = (dateString) => {
  if (!dateString) return '-';
  return new Date(dateString).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  });
};
