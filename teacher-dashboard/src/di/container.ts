/**
 * Dependency Injection Container
 *
 * This is the ONLY file that changes when switching between phases:
 *   Pilot   → ProcessedDataAdapter + ClaudeAgentAdapter
 *   Deploy  → MongoDataAdapter + ClaudeAgentAdapter  ← current
 */

import { MongoDataAdapter } from '../adapters/MongoDataAdapter'
import { MockMasteryAdapter } from '../adapters/MockMasteryAdapter'
import { ClaudeAgentAdapter } from '../adapters/ClaudeAgentAdapter'

import type { DataService } from '../ports/DataService'
import type { AgentService } from '../ports/AgentService'
import type { MasteryService } from '../ports/MasteryService'

export const container: {
  dataService: DataService
  agentService: AgentService
  masteryService: MasteryService
} = {
  dataService: new MongoDataAdapter(),
  agentService: new ClaudeAgentAdapter(),
  masteryService: new MockMasteryAdapter(),
}
