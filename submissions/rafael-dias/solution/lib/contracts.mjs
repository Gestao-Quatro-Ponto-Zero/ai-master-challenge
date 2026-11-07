/**
 * Shared data contracts. These describe the existing JSON format, not a migration.
 * Rules/validation live in workflow.mjs; storage must never invent CRM information.
 *
 * @typedef {'profile'|'contact'|'qualify'|'proposal'|'followup'|'won'|'lost'|'note'|'pause'} ActivityType
 * @typedef {'new'|'contacted'|'qualified'|'proposal'|'won'|'lost'} OperationalStage
 * @typedef {{name:string,email?:string,phone?:string}} Contact
 * @typedef {{need:string,authority:string,timing:string}} Qualification
 * @typedef {{label:string,dueAt:string}} Commitment
 * @typedef {Object} Activity
 * @property {string} id
 * @property {string} opportunityId
 * @property {string} agent Original CRM owner
 * @property {string} at ISO timestamp
 * @property {ActivityType} type
 * @property {3} [schemaVersion]
 * @property {string} [occurredAt]
 * @property {string} [recordedAt]
 * @property {string} [evidenceId]
 * @property {string} [evidenceSource]
 * @property {string} [healthPolicyVersion]
 * @property {"unknown"|"confirmed"|"none"} [buyerResponse]
 * @property {"unknown"|"yes"|"no"} [nextStepAccepted]
 * @property {"unknown"|"compatible"|"blocked"} [financialStatus]
 * @property {string|number} [quotedAmount]
 * @property {"USD"} [quoteCurrency]
 * @property {string} [pauseUntil]
 * @property {string} [notes]
 * @property {string} [dueAt]
 * @property {string} [nextAction]
 * @property {string} [account]
 * @property {string} [contactName]
 * @property {string} [email]
 * @property {string} [phone]
 * @property {string} [need]
 * @property {string} [authority]
 * @property {string} [timing]
 * @property {string|number} [amount]
 * @typedef {{opportunityId:string,goal:string,label:string,account?:string,assignedAt?:string}} DailyTask
 * @typedef {{day:string,createdAt:string,version?:number,batchSize?:number,tasks:DailyTask[]}} DailyPlan
 * @typedef {{version:2,agent:string,events:Activity[],plans:Record<string,DailyPlan>}} WorkspaceSnapshot
 */
export {};
