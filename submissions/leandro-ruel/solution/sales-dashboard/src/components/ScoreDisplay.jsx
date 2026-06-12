import React from 'react';
import { ChevronDown } from 'lucide-react';
import { motion } from 'framer-motion';
import { useLanguage } from '../i18n/LanguageContext';
import { getScoreBadgeColor, getScoreBadgeLabel, getSuccessProbabilityLabel } from '../utils/formatting';

export const ScoreBadge = ({ score, onClick, size = 'sm' }) => {
  const { t } = useLanguage();
  const color = getScoreBadgeColor(score);
  const label = getScoreBadgeLabel(score);
  const isCompact = size === 'sm';

  return (
    <motion.button
      whileHover={{ scale: 1.05 }}
      whileTap={{ scale: 0.95 }}
      onClick={onClick}
      className={`badge-score ${color} ${isCompact ? 'text-xs px-2 py-1' : 'text-sm px-3 py-1.5'}`}
      title={t('scoreBreakdown.title')}
    >
      <span className={`font-bold ${isCompact ? '' : 'text-base'}`}>{Math.round(score)}</span>
      <span className="opacity-75 font-medium">{label}</span>
      <ChevronDown className="w-3 h-3 opacity-40 group-hover:opacity-100 transition-opacity" aria-hidden="true" />
    </motion.button>
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
  const { t } = useLanguage();

  const scores = [
    { key: 'stage', label: t('scoreBreakdown.stage'), value: stage_score, max: 25, color: 'bg-violet-500' },
    { key: 'accountSize', label: t('scoreBreakdown.accountSize'), value: account_score, max: 20, color: 'bg-blue-500' },
    { key: 'sellerPerformance', label: t('scoreBreakdown.sellerPerformance'), value: seller_score, max: 20, color: 'bg-emerald-500' },
    { key: 'productPerformance', label: t('scoreBreakdown.productPerformance'), value: product_score, max: 20, color: 'bg-amber-500' },
    { key: 'timeOnPipeline', label: t('scoreBreakdown.timeOnPipeline'), value: time_score, max: 15, color: 'bg-rose-500' },
  ];

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25 }}
      className="bg-white rounded-xl border border-gray-200 shadow-sm p-5 space-y-3"
    >
      <h3 className="font-bold text-gray-900 text-base">{t('scoreBreakdown.title')}</h3>

      <div className="space-y-2">
        {scores.map((score, i) => (
          <motion.div
            key={score.key}
            initial={{ opacity: 0, x: -8 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: i * 0.05, duration: 0.2 }}
            className="score-item"
          >
            <div className="flex items-center flex-1 min-w-0">
              <span className="text-gray-600 min-w-32 text-xs font-semibold">{score.label}</span>
              <div className="score-bar">
                <motion.div
                  className={`score-bar-fill ${score.color}`}
                  initial={{ scaleX: 0 }}
                  animate={{ scaleX: score.value / score.max }}
                  transition={{ delay: 0.2 + i * 0.05, duration: 0.5, ease: 'easeOut' }}
                  style={{ transformOrigin: 'left' }}
                />
              </div>
            </div>
            <span className="font-bold text-gray-900 min-w-10 text-right text-sm tabular-nums">
              {score.value.toFixed(1)}
              <span className="text-gray-400 font-normal">/{score.max}</span>
            </span>
          </motion.div>
        ))}
      </div>

      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.4 }}
        className="border-t pt-4 mt-4 bg-gradient-to-r from-indigo-50 to-blue-50 rounded-xl p-4"
      >
        <div className="flex justify-between items-center">
          <span className="font-bold text-gray-900">{t('scoreBreakdown.totalScore')}</span>
          <span className="text-3xl font-extrabold text-indigo-600 tabular-nums">
            {total_score.toFixed(1)}
            <span className="text-lg text-indigo-400 font-normal">/100</span>
          </span>
        </div>
        <div className="flex items-center gap-2 mt-2 text-sm text-gray-600">
          <span className="font-medium">{t('scoreBreakdown.successProbability')}:</span>
          <span className="font-bold text-indigo-600">{getSuccessProbabilityLabel(success_probability)}</span>
        </div>
      </motion.div>

      <details className="group text-xs text-gray-500">
        <summary className="cursor-pointer font-medium text-gray-600 hover:text-gray-800 transition-colors select-none">
          {t('scoreBreakdown.hint')}
        </summary>
        <div className="mt-3 space-y-1.5 bg-gray-50 rounded-lg p-3">
          <p><strong className="text-gray-700">{t('scoreBreakdown.stage')}:</strong> {t('scoreBreakdown.stageHint')}</p>
          <p><strong className="text-gray-700">{t('scoreBreakdown.accountSize')}:</strong> {t('scoreBreakdown.accountSizeHint')}</p>
          <p><strong className="text-gray-700">{t('scoreBreakdown.sellerPerformance')}:</strong> {t('scoreBreakdown.sellerHint')}</p>
          <p><strong className="text-gray-700">{t('scoreBreakdown.productPerformance')}:</strong> {t('scoreBreakdown.productHint')}</p>
          <p><strong className="text-gray-700">{t('scoreBreakdown.timeOnPipeline')}:</strong> {t('scoreBreakdown.timeHint')}</p>
        </div>
      </details>
    </motion.div>
  );
};

export const SuccessProbability = ({ probability }) => {
  const percent = Math.round(probability * 100);

  let bgColor = 'bg-rose-50 text-rose-700 ring-1 ring-rose-200';
  if (percent >= 80) bgColor = 'bg-emerald-50 text-emerald-700 ring-1 ring-emerald-200';
  else if (percent >= 60) bgColor = 'bg-blue-50 text-blue-700 ring-1 ring-blue-200';
  else if (percent >= 40) bgColor = 'bg-amber-50 text-amber-700 ring-1 ring-amber-200';

  return (
    <div className={`inline-flex items-center px-2.5 py-1 rounded-lg text-xs font-bold tabular-nums ${bgColor}`}>
      {percent}%
    </div>
  );
};
