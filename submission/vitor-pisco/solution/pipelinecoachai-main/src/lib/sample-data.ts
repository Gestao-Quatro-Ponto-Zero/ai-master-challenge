import type { PipelineDeal, SalesTeam, Product } from '@/types/csv';

export const SAMPLE_PIPELINE: PipelineDeal[] = [
  { opportunity_id: '1', sales_agent: 'Anna Thompson', product: 'GTXPro', account: 'Acme Corp', deal_stage: 'Engaging', engage_date: '2017-11-01', close_date: '', close_value: '' },
  { opportunity_id: '2', sales_agent: 'Anna Thompson', product: 'MG Special', account: 'Beta Inc', deal_stage: 'Prospecting', engage_date: '2017-10-15', close_date: '', close_value: '' },
  { opportunity_id: '3', sales_agent: 'Anna Thompson', product: 'GTXPro', account: '', deal_stage: 'Engaging', engage_date: '2017-12-10', close_date: '', close_value: '' },
  { opportunity_id: '4', sales_agent: 'Anna Thompson', product: 'GTXBasic', account: 'Gamma Ltd', deal_stage: 'Engaging', engage_date: '2017-09-20', close_date: '', close_value: '' },
  { opportunity_id: '5', sales_agent: 'Anna Thompson', product: 'MG Special', account: 'Delta Co', deal_stage: 'Prospecting', engage_date: '2017-11-25', close_date: '', close_value: '' },
  { opportunity_id: '6', sales_agent: 'Anna Thompson', product: 'GTXPro', account: 'Epsilon', deal_stage: 'Won', engage_date: '2017-06-01', close_date: '2017-08-15', close_value: '5400' },
  { opportunity_id: '7', sales_agent: 'Anna Thompson', product: 'GTXBasic', account: 'Zeta Corp', deal_stage: 'Lost', engage_date: '2017-07-10', close_date: '2017-09-20', close_value: '0' },
  { opportunity_id: '8', sales_agent: 'Carl Fox', product: 'GTXPro', account: 'Kappa Inc', deal_stage: 'Engaging', engage_date: '2017-11-05', close_date: '', close_value: '' },
  { opportunity_id: '9', sales_agent: 'Carl Fox', product: 'MG Special', account: 'Lambda', deal_stage: 'Prospecting', engage_date: '2017-10-01', close_date: '', close_value: '' },
  { opportunity_id: '10', sales_agent: 'Carl Fox', product: 'GTXPro', account: 'Mu Corp', deal_stage: 'Won', engage_date: '2017-05-01', close_date: '2017-07-01', close_value: '5400' },
];

export const SAMPLE_TEAMS: SalesTeam[] = [
  { sales_agent: 'Anna Thompson', manager: 'Dustin Brinkmann', regional_office: 'Central' },
  { sales_agent: 'Carl Fox', manager: 'Dustin Brinkmann', regional_office: 'Central' },
];

export const SAMPLE_PRODUCTS: Product[] = [
  { product: 'GTXPro', series: 'GTX', sales_price: '5400' },
  { product: 'GTXBasic', series: 'GTX', sales_price: '550' },
  { product: 'MG Special', series: 'MG', sales_price: '55' },
];
