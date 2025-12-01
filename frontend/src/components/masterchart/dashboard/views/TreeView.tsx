// frontend/src/components/masterchart/dashboard/views/TreeView.tsx
import React, { useState } from 'react';
import { MasterAccountNode } from '@/types/masterchart';
import { ChevronDown, ChevronRight, Folder, FileText, Plus, Edit, Trash2, Info } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { motion, AnimatePresence } from 'framer-motion';

interface TreeViewProps {
    tree: MasterAccountNode[];
    onSelectAccount: (account: MasterAccountNode) => void;
}

const TreeNode: React.FC<{
    node: MasterAccountNode;
    level: number;
    onSelectAccount: (account: MasterAccountNode) => void;
}> = ({ node, level, onSelectAccount }) => {
    const [isExpanded, setIsExpanded] = useState(level < 2);
    const hasChildren = node.children && node.children.length > 0;
    const isHeader = node.type === 'H';

    return (
        <div>
            <motion.div
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                className={`group flex items-center gap-2 py-2 px-3 rounded-lg hover:bg-accent/50 transition-colors ${level > 0 ? 'ml-' + (level * 4) : ''
                    }`}
                style={{ paddingLeft: `${level * 20 + 12}px` }}
            >
                {/* Expand/Collapse */}
                <button
                    onClick={() => setIsExpanded(!isExpanded)}
                    className="p-0.5 hover:bg-accent rounded transition-colors"
                    disabled={!hasChildren}
                >
                    {hasChildren ? (
                        isExpanded ? (
                            <ChevronDown className="h-4 w-4" />
                        ) : (
                            <ChevronRight className="h-4 w-4" />
                        )
                    ) : (
                        <div className="w-4" />
                    )}
                </button>

                {/* Icon */}
                {isHeader ? (
                    <Folder className="h-4 w-4 text-primary" />
                ) : (
                    <FileText className="h-4 w-4 text-muted-foreground" />
                )}

                {/* Code and Description */}
                <div className="flex-1 flex items-center gap-3">
                    <span className="font-mono text-sm font-medium">{node.code}</span>
                    <span className="text-sm">{node.description}</span>
                </div>

                {/* Actions */}
                <div className="opacity-0 group-hover:opacity-100 transition-opacity flex items-center gap-1">
                    {isHeader && (
                        <Button size="sm" variant="ghost" className="h-7 w-7 p-0">
                            <Plus className="h-3.5 w-3.5" />
                        </Button>
                    )}
                    <Button size="sm" variant="ghost" className="h-7 w-7 p-0">
                        <Edit className="h-3.5 w-3.5" />
                    </Button>
                    <Button size="sm" variant="ghost" className="h-7 w-7 p-0">
                        <Trash2 className="h-3.5 w-3.5" />
                    </Button>
                    <Button
                        size="sm"
                        variant="ghost"
                        className="h-7 w-7 p-0"
                        onClick={() => onSelectAccount(node)}
                    >
                        <Info className="h-3.5 w-3.5" />
                    </Button>
                </div>
            </motion.div>

            {/* Children */}
            <AnimatePresence>
                {isExpanded && hasChildren && (
                    <motion.div
                        initial={{ opacity: 0, height: 0 }}
                        animate={{ opacity: 1, height: 'auto' }}
                        exit={{ opacity: 0, height: 0 }}
                        transition={{ duration: 0.2 }}
                    >
                        {node.children.map((child) => (
                            <TreeNode
                                key={child.id}
                                node={child}
                                level={level + 1}
                                onSelectAccount={onSelectAccount}
                            />
                        ))}
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    );
};

const TreeView: React.FC<TreeViewProps> = ({ tree, onSelectAccount }) => {
    return (
        <div className="space-y-1 p-4 bg-card rounded-xl border">
            {tree.map((node) => (
                <TreeNode key={node.id} node={node} level={0} onSelectAccount={onSelectAccount} />
            ))}
        </div>
    );
};

export default TreeView;
