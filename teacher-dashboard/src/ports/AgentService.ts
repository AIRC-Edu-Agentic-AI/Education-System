import type { ChatMessage, AgentContext } from '../types/domain'

export interface AgentService {
  /**
   * Streams an assistant response token by token.
   * Yields string chunks; caller appends them to the current message.
   */
  stream(
    messages: ChatMessage[],
    context: AgentContext
  ): AsyncIterable<string>
}
