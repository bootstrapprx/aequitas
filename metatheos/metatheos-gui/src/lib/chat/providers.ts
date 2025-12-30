export type ChatProviderId = 'chatgpt' | 'claude-web' | 'mistral' | 'deepseek' | 'ollama-assistant'

export interface ChatProvider {
  id: ChatProviderId
  label: string
  url: string
  description: string
  webOnly: boolean
  allowCustomUrl: boolean
}

export const defaultProviders: ChatProvider[] = [
  {
    id: 'chatgpt',
    label: 'ChatGPT (web)',
    url: 'https://chatgpt.com/',
    description: 'Web chat, no governance context unless pasted.',
    webOnly: true,
    allowCustomUrl: true,
  },
  {
    id: 'claude-web',
    label: 'Claude (web)',
    url: 'https://claude.ai/',
    description: 'Web chat, no governance context unless pasted.',
    webOnly: true,
    allowCustomUrl: true,
  },
  {
    id: 'mistral',
    label: 'Mistral Le Chat (web)',
    url: 'https://chat.mistral.ai/chat',
    description: 'Web chat, no governance context unless pasted.',
    webOnly: true,
    allowCustomUrl: true,
  },
  {
    id: 'deepseek',
    label: 'DeepSeek (web)',
    url: 'https://chat.deepseek.com/',
    description: 'Web chat, no governance context unless pasted.',
    webOnly: true,
    allowCustomUrl: true,
  },
  {
    id: 'ollama-assistant',
    label: 'Local Ollama (vault-aware)',
    url: '',
    description: 'Switches to Governance Assistant tab (vault-aware).',
    webOnly: false,
    allowCustomUrl: false,
  },
]
