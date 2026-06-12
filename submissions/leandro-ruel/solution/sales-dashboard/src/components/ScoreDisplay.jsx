import React from 'react';
import { ChevronDown } from 'lucide-react';
import {
  getScoreBadgeColor,
  getScoreBadgeLabel,
  getSuccessProbabilityLabel,
} from '../utils/formatting';

export const ScoreBadge = ({ score, onClick }) => {
  const color = getScoreBadgeColor(score);
  const label = getScoreBadgeLabel(score);

  return (
    <button
      onClick={onClick}
      className={`badge-score ${color} group`}
      title="Click to view score breakdown"
    >
      <span className="font-bold">{Math.round(score)}</span>
      <span className="text-xs ml-1 opacity-70">{label}</span>
      <ChevronDown className="w-3 h-3 ml-1 opacity-0 group-hover:opacity-100 transition-opacity" />
    </button>
  );
};

export const ScoreBreakdown = ({
  stage_score,
  account_score,
  seller_score,
  product_score,
  time_score,
  total_score,
  success_probability,
}) => {
  const scores = [
    { label: 'Deal Stage', value: stage_score, max: 25, color: 'bg-purple-500' },
    { label: 'Account Size', value: account_score, max: 20, color: 'bg-blue-500' },
    { label: 'Seller Performance', value: seller_score, max: 20, color: 'bg-green-500' },
    { label: 'Product Performance', value: product_score, max: 20, color: 'bg-yellow-500' },
    { label: 'Time on Pipeline', value: time_score, max: 15, color: 'bg-pink-500' },
  ];

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-4 space-y-3">
      <h3 className="font-semibold text-gray-900">Score Breakdown</h3>

      <div className="space-y-2">
        {scores.map((score) => (
          <div key={score.label} className="score-item">
            <div className="flex items-center flex-1">
              <span className="text-gray-600 min-w-32 text-xs font-medium">
                {score.label}
              </span>
              <div className="score-bar">
                <div
                  className={`score-bar-fill ${score.color}`}
                  style={{ width: `${(score.value / score.max) * 100}%` }}
                />
              </div>
            </div>
            <span className="font-semibold text-gray-900 min-w-10 text-right">
              {score.value.toFixed(1)}/{score.max}
            </span>
          </div>
        ))}
      </div>

      <div className="border-t pt-3 mt-3 bg-blue-50 rounded p-2">
        <div className="flex justify-between items-center">
          <span className="font-semibold text-gray-900">Total Score</span>
          <span className="text-2xl font-bold text-blue-600">
            {total_score.toFixed(1)}/100
          </span>
        </div>
        <div className="text-xs text-gray-600 mt-2">
          Success Probability: {getSuccessProbabilityLabel(success_probability)}
        </div>
      </div>

      <div className="text-xs text-gray-500 space-y-1 bg-gray-50 p-2 rounded">
        <p className="font-medium text-gray-700">What each score means:</p>
        <ul className="space-y-0.5">
          <li><strong>Deal Stage:</strong> Progress through pipeline (Prospecting → Engaging → Won)</li>
          <li><strong>Account Size:</strong> Company employees and revenue size</li>
          <li><strong>Seller Performance:</strong> Sales agent's historical win rate</li>
          <li><strong>Product Performance:</strong> Product's historical success rate</li>
          <li><strong>Time on Pipeline:</strong> How long deal has been active (optimal: 100-120 days)</li>
        </ul>
      </div>
    </div>
  );
};

export const SuccessProbability = ({ probability }) => {
  const percent = Math.round(probability * 100);
  let bgColor = 'bg-red-100';
  let textColor = 'text-red-800';

  if (percent >= 80) {
    bgColor = 'bg-green-100';
    textColor = 'text-green-800';
  } else if (percent >= 60) {
    bgColor = 'bg-blue-100';
    textColor = 'text-blue-800';
  } else if (percent >= 40) {
    bgColor = 'bg-yellow-100';
    textColor = 'text-yellow-800';
  }

  return (
    <div className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${bgColor} ${textColor}`}>
      <span>{percent}%</span>
    </div>
  );
};
