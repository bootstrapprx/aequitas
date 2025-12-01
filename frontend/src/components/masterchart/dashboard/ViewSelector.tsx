// frontend/src/components/masterchart/dashboard/ViewSelector.tsx
import React from 'react';
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Network, List, LayoutGrid } from 'lucide-react';
import { ViewMode } from '@/types/masterchart';

interface ViewSelectorProps {
    activeView: ViewMode;
    onViewChange: (view: ViewMode) => void;
}

const ViewSelector: React.FC<ViewSelectorProps> = ({ activeView, onViewChange }) => {
    return (
        <Tabs value={activeView} onValueChange={(value) => onViewChange(value as ViewMode)}>
            <TabsList className="grid w-full max-w-md grid-cols-3">
                <TabsTrigger value="tree" className="flex items-center gap-2">
                    <Network className="h-4 w-4" />
                    <span className="hidden sm:inline">Tree View</span>
                </TabsTrigger>
                <TabsTrigger value="list" className="flex items-center gap-2">
                    <List className="h-4 w-4" />
                    <span className="hidden sm:inline">List View</span>
                </TabsTrigger>
                <TabsTrigger value="cards" className="flex items-center gap-2">
                    <LayoutGrid className="h-4 w-4" />
                    <span className="hidden sm:inline">Cards View</span>
                </TabsTrigger>
            </TabsList>
        </Tabs>
    );
};

export default ViewSelector;
