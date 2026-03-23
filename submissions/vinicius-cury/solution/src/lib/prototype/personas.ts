// Persona definitions for QA simulation testing

export interface Persona {
  id: string;
  name: string;
  email: string;
  age: number;
  role: string;
  techLevel: 'beginner' | 'intermediate' | 'advanced' | 'expert';
  communicationStyle: string;
  traits: string[];
  preferredChannel: string;
}

export const PERSONAS: Persona[] = [
  {
    id: 'joao-tech',
    name: 'João Tech',
    email: 'joao.tech@devmail.com',
    age: 28,
    role: 'Desenvolvedor',
    techLevel: 'expert',
    communicationStyle: 'Uses technical jargon, impatient, wants CLI solutions, skips pleasantries',
    traits: ['impatient', 'technical', 'direct'],
    preferredChannel: 'Chat',
  },
  {
    id: 'maria-dona',
    name: 'Maria Aparecida',
    email: 'maria.aparecida@gmail.com',
    age: 67,
    role: 'Aposentada',
    techLevel: 'beginner',
    communicationStyle: 'Very polite, confused by technology, long explanations with irrelevant details, uses formal language',
    traits: ['polite', 'confused', 'verbose', 'patient'],
    preferredChannel: 'Phone',
  },
  {
    id: 'carlos-gerente',
    name: 'Carlos Gerente',
    email: 'carlos.silva@empresa.com.br',
    age: 45,
    role: 'Gerente de Operações',
    techLevel: 'intermediate',
    communicationStyle: 'Terse, results-oriented, no patience for troubleshooting steps, threatens to escalate',
    traits: ['impatient', 'authoritative', 'demanding'],
    preferredChannel: 'Email',
  },
  {
    id: 'ana-estagiaria',
    name: 'Ana Clara',
    email: 'ana.clara@empresa.com.br',
    age: 21,
    role: 'Estagiária',
    techLevel: 'beginner',
    communicationStyle: 'Very detailed descriptions, afraid of breaking things, apologetic, asks permission before doing anything',
    traits: ['cautious', 'detailed', 'apologetic', 'nervous'],
    preferredChannel: 'Chat',
  },
  {
    id: 'roberto-irritado',
    name: 'Roberto Furioso',
    email: 'roberto.santos@hotmail.com',
    age: 38,
    role: 'Analista Financeiro',
    techLevel: 'intermediate',
    communicationStyle: 'Angry, references previous unresolved tickets, demands supervisor, uses caps for emphasis',
    traits: ['angry', 'returning', 'demanding', 'vocal'],
    preferredChannel: 'Chat',
  },
  {
    id: 'fernanda-objetiva',
    name: 'Fernanda Lima',
    email: 'fernanda.lima@corp.com',
    age: 33,
    role: 'Analista de Dados',
    techLevel: 'advanced',
    communicationStyle: 'Minimal words, gives only essential info, expects system to figure out the rest',
    traits: ['concise', 'efficient', 'expects-competence'],
    preferredChannel: 'Chat',
  },
  {
    id: 'paulo-professor',
    name: 'Paulo Henrique',
    email: 'ph.oliveira@universidade.edu.br',
    age: 55,
    role: 'Professor Universitário',
    techLevel: 'intermediate',
    communicationStyle: 'Verbose, uses academic language, explains background context extensively, technically wrong terms sometimes',
    traits: ['verbose', 'intellectual', 'patient', 'detailed'],
    preferredChannel: 'Email',
  },
  {
    id: 'luciana-urgente',
    name: 'Luciana Martins',
    email: 'luciana.m@startup.io',
    age: 30,
    role: 'Product Manager',
    techLevel: 'intermediate',
    communicationStyle: 'Panicked about deadline, needs resolution NOW, mentions consequences of delay, will escalate to CEO',
    traits: ['urgent', 'stressed', 'deadline-driven', 'escalation-prone'],
    preferredChannel: 'Phone',
  },
  {
    id: 'diego-timido',
    name: 'Diego Souza',
    email: 'diego.s@empresa.com.br',
    age: 24,
    role: 'Assistente Administrativo',
    techLevel: 'beginner',
    communicationStyle: 'Hesitant, vague problem descriptions, unsure if its their fault, needs prompting to give details',
    traits: ['hesitant', 'vague', 'self-blaming', 'shy'],
    preferredChannel: 'Chat',
  },
  {
    id: 'beatriz-multi',
    name: 'Beatriz Nakamura',
    email: 'b.nakamura@multinational.com',
    age: 40,
    role: 'Diretora de TI',
    techLevel: 'advanced',
    communicationStyle: 'Mixes English and Portuguese naturally, concise, high expectations, references enterprise solutions',
    traits: ['bilingual', 'executive', 'high-expectations', 'concise'],
    preferredChannel: 'Email',
  },
  {
    id: 'thiago-repetidor',
    name: 'Thiago Costa',
    email: 'thiago.costa@gmail.com',
    age: 35,
    role: 'Designer',
    techLevel: 'intermediate',
    communicationStyle: 'Frustrated because same issue happened before, references ticket numbers, wants different solution than last time',
    traits: ['frustrated', 'returning', 'skeptical', 'references-history'],
    preferredChannel: 'Chat',
  },
  {
    id: 'camila-vip',
    name: 'Camila Rodrigues',
    email: 'camila@ceo-office.com.br',
    age: 50,
    role: 'CEO',
    techLevel: 'advanced',
    communicationStyle: 'Very few words, expects premium treatment, will name-drop, no patience for scripts',
    traits: ['authoritative', 'vip', 'terse', 'expects-special-treatment'],
    preferredChannel: 'Phone',
  },
];

// Issue templates for QA simulation
export const ISSUE_TEMPLATES = [
  // Hardware problems
  { category: 'Hardware', description: 'laptop won\'t start, black screen', issueType: 'hardware' },
  { category: 'Hardware', description: 'laptop overheating and shutting down', issueType: 'hardware' },
  { category: 'Hardware', description: 'keyboard keys not working', issueType: 'hardware' },
  { category: 'Hardware', description: 'monitor screen flickering', issueType: 'hardware' },
  { category: 'Hardware', description: 'laptop battery draining very fast', issueType: 'hardware' },
  { category: 'Hardware', description: 'USB ports not recognizing devices', issueType: 'hardware' },
  // Software issues
  { category: 'Software', description: 'application crashes on startup', issueType: 'software' },
  { category: 'Software', description: 'software running very slow', issueType: 'software' },
  { category: 'Software', description: 'can\'t install new software, permission error', issueType: 'software' },
  { category: 'Software', description: 'system update failed midway', issueType: 'software' },
  { category: 'Application', description: 'app freezes when opening large files', issueType: 'software' },
  { category: 'Application', description: 'error message when trying to save document', issueType: 'software' },
  // Network problems
  { category: 'Network', description: 'can\'t connect to WiFi', issueType: 'network' },
  { category: 'Network', description: 'internet very slow, pages won\'t load', issueType: 'network' },
  { category: 'Network', description: 'network printer not showing up', issueType: 'network' },
  { category: 'Network', description: 'VPN connection dropping constantly', issueType: 'network' },
  // Account issues
  { category: 'Access', description: 'locked out of account after too many attempts', issueType: 'account' },
  { category: 'Access', description: 'need password reset, forgot current password', issueType: 'account' },
  { category: 'Access', description: 'can\'t access shared drive, permission denied', issueType: 'account' },
  { category: 'Access', description: 'two-factor authentication not working', issueType: 'account' },
  // Data problems
  { category: 'Data', description: 'important files disappeared from folder', issueType: 'data' },
  { category: 'Data', description: 'backup job failed last night', issueType: 'data' },
  { category: 'Storage', description: 'disk storage full, can\'t save anything', issueType: 'data' },
  { category: 'Data', description: 'weekly report data showing wrong numbers', issueType: 'data' },
  { category: 'Storage', description: 'need to recover deleted files from last week', issueType: 'data' },
  // Integration issues
  { category: 'Integration', description: 'API returning 500 errors intermittently', issueType: 'integration' },
  { category: 'Integration', description: 'Salesforce sync not updating contacts', issueType: 'integration' },
  { category: 'Integration', description: 'payment gateway rejecting valid cards', issueType: 'integration' },
  { category: 'Integration', description: 'SSO login failing for third-party app', issueType: 'integration' },
  { category: 'Integration', description: 'email integration not sending notifications', issueType: 'integration' },
];

// Channels for random selection
export const CHANNELS = ['Chat', 'Email', 'Phone', 'Social media'] as const;

// Follow-up templates
export const POSITIVE_FOLLOWUPS = [
  'Sim, funcionou! Obrigado.',
  'Resolveu, muito obrigado pela ajuda.',
  'Deu certo! Valeu.',
  'Consegui resolver seguindo os passos. Obrigado!',
  'Perfeito, era isso mesmo. Agradeço.',
];

export const NEGATIVE_FOLLOWUPS = [
  'Não resolveu, continua com o mesmo problema.',
  'Já tentei isso antes e não funcionou.',
  'Não ajudou, ainda estou com o mesmo erro.',
  'Continua igual, preciso de outra solução.',
  'Não deu certo. Quero falar com um atendente humano.',
];
