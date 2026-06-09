export const CONFIDENCE_THRESHOLD = 85;

export const HUMAN_REQUIRED_TYPES = [
  "Refund request",
  "Cancellation request",
] as const;

export const TOPIC_TO_QUEUE: Record<string, string> = {
  Hardware: "hardware",
  "HR Support": "hr-support",
  Access: "access",
  Miscellaneous: "miscellaneous",
  Storage: "storage",
  Purchase: "purchase",
  "Internal Project": "internal-project",
  "Administrative rights": "admin-rights",
};

export const DS2_CATEGORIES = [
  "Access",
  "Administrative rights",
  "HR Support",
  "Hardware",
  "Internal Project",
  "Miscellaneous",
  "Purchase",
  "Storage",
] as const;
