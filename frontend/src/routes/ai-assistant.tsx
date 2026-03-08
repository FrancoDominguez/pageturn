import { useState } from 'react';
import { useApiKeys, useGenerateApiKey, useRevokeApiKey } from '../hooks/useApiKeys';
import LoadingSkeleton from '../components/LoadingSkeleton';
import Modal from '../components/Modal';
import { useToast } from '../components/Toast';

// ── MCP Config ─────────────────────────────────────────────────────────────

const MCP_CONFIG = `{
  "mcpServers": {
    "pageturn-library": {
      "url": "https://api.pageturn.library/mcp",
      "headers": {
        "Authorization": "Bearer YOUR_API_KEY"
      }
    }
  }
}`;

// ── Example Prompts ────────────────────────────────────────────────────────

const EXAMPLE_PROMPTS = [
  {
    title: 'Find a book',
    description: 'Ask the AI to search the catalogue for you.',
    prompt: '"Find me a mystery novel set in Tokyo with at least 4 stars"',
  },
  {
    title: 'Check out a book',
    description: 'Have the AI check out a book on your behalf.',
    prompt: '"Check out The Great Gatsby for me"',
  },
  {
    title: 'Get recommendations',
    description: 'Get personalized suggestions based on your history.',
    prompt: '"Based on my reading history, what should I read next?"',
  },
];

// ── Copy button helper ─────────────────────────────────────────────────────

function CopyButton({ text, label }: { text: string; label?: string }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // fallback
    }
  };

  return (
    <button
      type="button"
      onClick={handleCopy}
      className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium bg-white/10 hover:bg-white/20 text-white rounded-button transition-colors cursor-pointer"
    >
      {copied ? (
        <>
          <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
          </svg>
          Copied!
        </>
      ) : (
        <>
          <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
          </svg>
          {label ?? 'Copy'}
        </>
      )}
    </button>
  );
}

// ── Generate Key Modal ─────────────────────────────────────────────────────

function GenerateKeyModal({
  isOpen,
  onClose,
}: {
  isOpen: boolean;
  onClose: () => void;
}) {
  const [name, setName] = useState('');
  const [generatedKey, setGeneratedKey] = useState<string | null>(null);
  const generateKey = useGenerateApiKey();
  const { toast } = useToast();

  const handleGenerate = () => {
    if (!name.trim()) return;
    generateKey.mutate(name.trim(), {
      onSuccess: (data: any) => {
        setGeneratedKey(data.key || data.api_key || 'Key generated successfully');
        toast('API key generated!', 'success');
      },
      onError: () => toast('Failed to generate key.', 'error'),
    });
  };

  const handleClose = () => {
    setName('');
    setGeneratedKey(null);
    onClose();
  };

  return (
    <Modal isOpen={isOpen} onClose={handleClose} title="Generate New API Key">
      {generatedKey ? (
        <div className="space-y-4">
          <div className="p-4 bg-amber-50 border border-amber-200 rounded-card text-sm text-amber-800">
            <strong>Save this key now!</strong> You won't be able to see it again after closing this dialog.
          </div>
          <div className="flex items-center gap-2 p-3 bg-[#0d1117] rounded-card">
            <code className="flex-1 text-sm text-emerald-400 font-mono break-all">{generatedKey}</code>
            <CopyButton text={generatedKey} label="Copy Key" />
          </div>
          <div className="flex justify-end">
            <button
              type="button"
              onClick={handleClose}
              className="px-4 py-2 bg-primary hover:bg-primary-hover text-white text-sm font-medium rounded-button transition-colors cursor-pointer"
            >
              Done
            </button>
          </div>
        </div>
      ) : (
        <div className="space-y-4">
          <div>
            <label htmlFor="key-name" className="block text-sm font-medium text-text-primary mb-1.5">
              Key Name
            </label>
            <input
              id="key-name"
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g., My Claude Desktop"
              className="w-full h-10 px-3 text-sm text-text-primary bg-background border border-border rounded-card focus:ring-2 focus:ring-primary/40 focus:outline-none placeholder:text-text-muted"
            />
          </div>
          <div className="flex justify-end gap-3">
            <button
              type="button"
              onClick={handleClose}
              className="px-4 py-2 text-sm font-medium text-text-secondary border border-border rounded-button hover:bg-gray-50 transition-colors cursor-pointer"
            >
              Cancel
            </button>
            <button
              type="button"
              onClick={handleGenerate}
              disabled={!name.trim() || generateKey.isPending}
              className="px-4 py-2 bg-primary hover:bg-primary-hover text-white text-sm font-medium rounded-button transition-colors disabled:opacity-50 cursor-pointer disabled:cursor-not-allowed"
            >
              {generateKey.isPending ? 'Generating...' : 'Generate Key'}
            </button>
          </div>
        </div>
      )}
    </Modal>
  );
}

// ── Main Page ──────────────────────────────────────────────────────────────

export default function AIAssistantPage() {
  const { data, isLoading } = useApiKeys();
  const revokeKey = useRevokeApiKey();
  const { toast } = useToast();
  const [showGenerateModal, setShowGenerateModal] = useState(false);

  const apiKeys = data?.api_keys ?? [];

  const handleRevoke = (keyId: string) => {
    revokeKey.mutate(keyId, {
      onSuccess: () => toast('API key revoked.', 'success'),
      onError: () => toast('Failed to revoke key.', 'error'),
    });
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 py-8">
      <h1 className="font-heading font-bold text-2xl text-text-primary mb-2">AI Assistant</h1>
      <p className="text-text-muted text-sm mb-8">
        Connect your AI assistant (like Claude) to PageTurn using the MCP protocol.
      </p>

      {/* Setup Guide */}
      <section className="mb-10">
        <h2 className="font-heading font-semibold text-xl text-text-primary mb-4">Setup Guide</h2>
        <div className="bg-surface rounded-card shadow-card p-6">
          <ol className="space-y-6">
            <li className="flex gap-4">
              <div className="w-8 h-8 rounded-full bg-gradient-to-br from-primary to-secondary flex items-center justify-center text-white text-sm font-bold flex-shrink-0">
                1
              </div>
              <div className="flex-1">
                <h3 className="font-heading font-semibold text-sm text-text-primary mb-1">
                  Generate an API Key
                </h3>
                <p className="text-sm text-text-secondary">
                  Create an API key below to authenticate your AI assistant with PageTurn.
                </p>
              </div>
            </li>

            <li className="flex gap-4">
              <div className="w-8 h-8 rounded-full bg-gradient-to-br from-primary to-secondary flex items-center justify-center text-white text-sm font-bold flex-shrink-0">
                2
              </div>
              <div className="flex-1">
                <h3 className="font-heading font-semibold text-sm text-text-primary mb-1">
                  Add the MCP Configuration
                </h3>
                <p className="text-sm text-text-secondary mb-3">
                  Add the following configuration to your AI assistant's MCP settings file. Replace{' '}
                  <code className="text-xs bg-gray-100 px-1.5 py-0.5 rounded">YOUR_API_KEY</code> with your actual key.
                </p>

                {/* Code block */}
                <div className="bg-[#0d1117] rounded-card overflow-hidden">
                  <div className="flex items-center justify-between px-4 py-2 border-b border-white/10">
                    <span className="text-xs text-white/50 font-mono">mcp_config.json</span>
                    <CopyButton text={MCP_CONFIG} label="Copy Config" />
                  </div>
                  <pre className="p-4 text-sm text-emerald-400 font-mono overflow-x-auto">
                    {MCP_CONFIG}
                  </pre>
                </div>
              </div>
            </li>

            <li className="flex gap-4">
              <div className="w-8 h-8 rounded-full bg-gradient-to-br from-primary to-secondary flex items-center justify-center text-white text-sm font-bold flex-shrink-0">
                3
              </div>
              <div className="flex-1">
                <h3 className="font-heading font-semibold text-sm text-text-primary mb-1">
                  Start Using It
                </h3>
                <p className="text-sm text-text-secondary">
                  Once configured, you can ask your AI assistant to search books, check out items, view your loans, and more -- all through natural conversation.
                </p>
              </div>
            </li>
          </ol>
        </div>
      </section>

      {/* API Keys */}
      <section className="mb-10">
        <div className="flex items-center justify-between mb-4">
          <h2 className="font-heading font-semibold text-xl text-text-primary">API Keys</h2>
          <button
            type="button"
            onClick={() => setShowGenerateModal(true)}
            className="inline-flex items-center gap-1.5 px-4 py-2 bg-primary hover:bg-primary-hover text-white text-sm font-medium rounded-button transition-colors cursor-pointer"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            Generate New Key
          </button>
        </div>

        {isLoading ? (
          <LoadingSkeleton type="table" />
        ) : apiKeys.length === 0 ? (
          <div className="bg-surface rounded-card shadow-card p-8 text-center">
            <p className="text-text-muted text-sm">No API keys yet. Generate one to get started.</p>
          </div>
        ) : (
          <div className="bg-surface rounded-card shadow-card overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="bg-[#0d1117] text-white text-left text-sm">
                    <th className="px-4 py-3 font-medium">Name</th>
                    <th className="px-4 py-3 font-medium">Key</th>
                    <th className="px-4 py-3 font-medium hidden sm:table-cell">Scope</th>
                    <th className="px-4 py-3 font-medium hidden md:table-cell">Last Used</th>
                    <th className="px-4 py-3 font-medium hidden md:table-cell">Created</th>
                    <th className="px-4 py-3 font-medium text-right">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {apiKeys.map((key) => (
                    <tr key={key.id} className="hover:bg-gray-50/50 transition-colors">
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-2">
                          <span className="text-sm font-medium text-text-primary">{key.name}</span>
                          {!key.is_active && (
                            <span className="inline-flex items-center px-2 py-0.5 rounded-pill bg-red-50 text-red-600 text-[10px] font-medium">
                              Revoked
                            </span>
                          )}
                        </div>
                      </td>
                      <td className="px-4 py-3">
                        <code className="text-xs text-text-muted font-mono bg-gray-100 px-2 py-1 rounded">
                          {key.key_prefix}...
                        </code>
                      </td>
                      <td className="px-4 py-3 text-sm text-text-secondary hidden sm:table-cell capitalize">
                        {key.scope}
                      </td>
                      <td className="px-4 py-3 text-sm text-text-muted hidden md:table-cell">
                        {key.last_used_at
                          ? new Date(key.last_used_at).toLocaleDateString()
                          : 'Never'}
                      </td>
                      <td className="px-4 py-3 text-sm text-text-muted hidden md:table-cell">
                        {new Date(key.created_at).toLocaleDateString()}
                      </td>
                      <td className="px-4 py-3 text-right">
                        {key.is_active && (
                          <button
                            type="button"
                            onClick={() => handleRevoke(key.id)}
                            disabled={revokeKey.isPending}
                            className="text-sm font-medium text-red-600 hover:text-red-700 transition-colors cursor-pointer disabled:opacity-50"
                          >
                            Revoke
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </section>

      {/* Example prompts */}
      <section>
        <h2 className="font-heading font-semibold text-xl text-text-primary mb-4">Example Prompts</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {EXAMPLE_PROMPTS.map((example) => (
            <div
              key={example.title}
              className="bg-surface rounded-card shadow-card p-5 hover:shadow-hover transition-shadow"
            >
              <h3 className="font-heading font-semibold text-sm text-text-primary mb-1">
                {example.title}
              </h3>
              <p className="text-xs text-text-muted mb-3">{example.description}</p>
              <p className="text-sm text-secondary italic">{example.prompt}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Generate Key Modal */}
      <GenerateKeyModal
        isOpen={showGenerateModal}
        onClose={() => setShowGenerateModal(false)}
      />
    </div>
  );
}
