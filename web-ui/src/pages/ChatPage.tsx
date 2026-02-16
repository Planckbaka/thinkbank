/**
 * ThinkBank - Chat Page
 * RAG-based chat interface for querying assets with AI
 */

import { useState, useRef, useEffect } from 'react';
import { Send, Loader2, Bot, User, FileText, Image as ImageIcon, AlertCircle } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Separator } from '@/components/ui/separator';
import { chatWithAssets, type ChatMessage, type ChatResponse, type SearchResultItem } from '@/lib/api';

interface DisplayMessage {
    role: 'user' | 'assistant';
    content: string;
    sources?: SearchResultItem[];
}

export function ChatPage() {
    const [messages, setMessages] = useState<DisplayMessage[]>([]);
    const [input, setInput] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const messagesEndRef = useRef<HTMLDivElement>(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    const handleSend = async () => {
        const query = input.trim();
        if (!query || loading) return;

        setInput('');
        setError(null);

        const userMessage: DisplayMessage = { role: 'user', content: query };
        setMessages((prev) => [...prev, userMessage]);

        setLoading(true);
        try {
            // Build history for context
            const history: ChatMessage[] = messages.map((m) => ({
                role: m.role,
                content: m.content,
            }));

            const response: ChatResponse = await chatWithAssets(query, history);

            const assistantMessage: DisplayMessage = {
                role: 'assistant',
                content: response.answer,
                sources: response.sources,
            };
            setMessages((prev) => [...prev, assistantMessage]);
        } catch (err) {
            setError((err as Error).message);
        } finally {
            setLoading(false);
        }
    };

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSend();
        }
    };

    const getSourceIcon = (mimeType: string) => {
        if (mimeType.startsWith('image/')) return ImageIcon;
        return FileText;
    };

    return (
        <div className="flex flex-col h-[calc(100vh-5rem)]">
            {/* Header */}
            <div className="mb-4">
                <h1 className="text-2xl font-semibold tracking-tight">AI Chat</h1>
                <p className="text-muted-foreground">
                    Ask questions about your assets using RAG-powered AI
                </p>
            </div>

            {/* Messages Area */}
            <div className="flex-1 overflow-y-auto space-y-4 pb-4">
                {messages.length === 0 && (
                    <div className="flex flex-col items-center justify-center h-full text-center">
                        <div className="mb-4 rounded-full bg-muted p-6">
                            <Bot className="h-10 w-10 text-muted-foreground" />
                        </div>
                        <h3 className="mb-2 text-lg font-medium">Start a Conversation</h3>
                        <p className="text-muted-foreground max-w-md">
                            Ask questions about your images and documents. The AI will search your assets and provide answers with sources.
                        </p>
                        <div className="mt-6 flex flex-wrap gap-2 justify-center">
                            {['What images do I have?', 'Summarize my documents', 'Find landscape photos'].map((suggestion) => (
                                <Button
                                    key={suggestion}
                                    variant="outline"
                                    size="sm"
                                    onClick={() => {
                                        setInput(suggestion);
                                    }}
                                >
                                    {suggestion}
                                </Button>
                            ))}
                        </div>
                    </div>
                )}

                {messages.map((msg, idx) => (
                    <div
                        key={idx}
                        className={`flex items-start gap-3 ${msg.role === 'user' ? 'justify-end' : ''}`}
                    >
                        {msg.role === 'assistant' && (
                            <div className="flex-shrink-0 h-8 w-8 rounded-full bg-primary/10 flex items-center justify-center">
                                <Bot className="h-4 w-4 text-primary" />
                            </div>
                        )}

                        <div className={`max-w-[75%] ${msg.role === 'user' ? 'order-first' : ''}`}>
                            <Card className={msg.role === 'user' ? 'bg-primary text-primary-foreground' : ''}>
                                <CardContent className="p-3">
                                    <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
                                </CardContent>
                            </Card>

                            {/* Sources */}
                            {msg.sources && msg.sources.length > 0 && (
                                <div className="mt-2 space-y-1">
                                    <p className="text-xs text-muted-foreground font-medium">Sources:</p>
                                    <div className="flex flex-wrap gap-1">
                                        {msg.sources.map((source) => {
                                            const Icon = getSourceIcon(source.mime_type);
                                            return (
                                                <div
                                                    key={source.id}
                                                    className="flex items-center gap-1 bg-muted rounded px-2 py-1"
                                                >
                                                    <Icon className="h-3 w-3 text-muted-foreground" />
                                                    <span className="text-xs text-muted-foreground truncate max-w-[120px]">
                                                        {source.file_name}
                                                    </span>
                                                </div>
                                            );
                                        })}
                                    </div>
                                </div>
                            )}
                        </div>

                        {msg.role === 'user' && (
                            <div className="flex-shrink-0 h-8 w-8 rounded-full bg-primary flex items-center justify-center">
                                <User className="h-4 w-4 text-primary-foreground" />
                            </div>
                        )}
                    </div>
                ))}

                {loading && (
                    <div className="flex items-start gap-3">
                        <div className="flex-shrink-0 h-8 w-8 rounded-full bg-primary/10 flex items-center justify-center">
                            <Bot className="h-4 w-4 text-primary" />
                        </div>
                        <Card>
                            <CardContent className="p-3">
                                <div className="flex items-center gap-2">
                                    <Loader2 className="h-4 w-4 animate-spin" />
                                    <span className="text-sm text-muted-foreground">Thinking...</span>
                                </div>
                            </CardContent>
                        </Card>
                    </div>
                )}

                {error && (
                    <div className="flex items-center gap-2 text-destructive text-sm p-3 bg-destructive/10 rounded-lg">
                        <AlertCircle className="h-4 w-4" />
                        <span>{error}</span>
                    </div>
                )}

                <div ref={messagesEndRef} />
            </div>

            <Separator />

            {/* Input Area */}
            <div className="pt-4 pb-2">
                <div className="flex items-end gap-2">
                    <textarea
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        onKeyDown={handleKeyDown}
                        placeholder="Ask about your assets..."
                        className="flex-1 resize-none rounded-lg border bg-background px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-ring min-h-[44px] max-h-[120px]"
                        rows={1}
                        disabled={loading}
                    />
                    <Button
                        onClick={handleSend}
                        disabled={!input.trim() || loading}
                        size="icon"
                        className="h-11 w-11 flex-shrink-0"
                    >
                        {loading ? (
                            <Loader2 className="h-4 w-4 animate-spin" />
                        ) : (
                            <Send className="h-4 w-4" />
                        )}
                    </Button>
                </div>
            </div>
        </div>
    );
}
