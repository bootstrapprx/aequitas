/**
 * Dexter Insights Panel
 *
 * Passive, dismissible panel for Dexter observations.
 *
 * Authority: Canon IV - Intelligence (Zone C) is advisory, never authoritative.
 *
 * CRITICAL CONSTRAINTS:
 * - Dismissible (no blocking)
 * - Optional (can be hidden)
 * - Non-urgent (calm, neutral design)
 * - No imperative language
 */

import React, { useState, useEffect } from 'react';
import { X, Lightbulb, AlertTriangle, Calendar, TrendingUp, Info } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { Badge } from '../ui/badge';
import { Button } from '../ui/button';
import { ScrollArea } from '../ui/scroll-area';
import { Separator } from '../ui/separator';
import { cn } from '../../lib/utils';

// ============================================================================
// TYPES
// ============================================================================

interface DexterInsight {
  type: string;
  message: string;
  data: Record<string, any>;
  dismissible: boolean;
  actions: string[];
}

interface DexterInsightsPanelProps {
  companyId: string;
  periodId?: string;
  className?: string;
  onActionClick?: (insightType: string, actionLabel: string, data: Record<string, any>) => void;
}

// ============================================================================
// INSIGHT CARD COMPONENT
// ============================================================================

const DexterInsightCard: React.FC<{
  insight: DexterInsight;
  onDismiss: () => void;
  onActionClick?: (actionLabel: string, data: Record<string, any>) => void;
}> = ({ insight, onDismiss, onActionClick }) => {
  const getInsightIcon = (type: string) => {
    switch (type) {
      case 'recurring_pattern':
        return <TrendingUp className="h-4 w-4 text-blue-500" />;
      case 'anomaly':
        return <AlertTriangle className="h-4 w-4 text-amber-500" />;
      case 'missing_entry':
        return <Calendar className="h-4 w-4 text-purple-500" />;
      case 'account_usage':
        return <Info className="h-4 w-4 text-green-500" />;
      default:
        return <Lightbulb className="h-4 w-4 text-gray-500" />;
    }
  };

  const getInsightTypeLabel = (type: string) => {
    switch (type) {
      case 'recurring_pattern':
        return 'Pattern';
      case 'anomaly':
        return 'Anomaly';
      case 'missing_entry':
        return 'Observation';
      case 'account_usage':
        return 'Usage';
      default:
        return 'Insight';
    }
  };

  return (
    <Card className="relative border-l-4 border-l-blue-500/20">
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between gap-2">
          <div className="flex items-center gap-2">
            {getInsightIcon(insight.type)}
            <Badge variant="secondary" className="text-xs">
              {getInsightTypeLabel(insight.type)}
            </Badge>
          </div>
          {insight.dismissible && (
            <Button
              variant="ghost"
              size="sm"
              className="h-6 w-6 p-0 hover:bg-destructive/10"
              onClick={onDismiss}
            >
              <X className="h-3 w-3" />
            </Button>
          )}
        </div>
      </CardHeader>
      <CardContent className="space-y-3">
        <p className="text-sm text-muted-foreground leading-relaxed">
          {insight.message}
        </p>

        {insight.actions && insight.actions.length > 0 && (
          <div className="flex flex-wrap gap-2">
            {insight.actions.filter(action => action !== 'Dismiss').map((action, idx) => (
              <Button
                key={idx}
                variant="outline"
                size="sm"
                className="text-xs"
                onClick={() => onActionClick?.(action, insight.data)}
              >
                {action}
              </Button>
            ))}
            <Button
              variant="ghost"
              size="sm"
              className="text-xs text-muted-foreground"
              onClick={onDismiss}
            >
              Dismiss
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

// ============================================================================
// MAIN PANEL COMPONENT
// ============================================================================

export const DexterInsightsPanel: React.FC<DexterInsightsPanelProps> = ({
  companyId,
  periodId,
  className,
  onActionClick,
}) => {
  const [insights, setInsights] = useState<DexterInsight[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [panelVisible, setPanelVisible] = useState(true);

  useEffect(() => {
    fetchInsights();
  }, [companyId, periodId]);

  const fetchInsights = async () => {
    setLoading(true);
    setError(null);

    try {
      const params = new URLSearchParams();
      if (periodId) params.append('period_id', periodId);
      params.append('max_insights', '10');

      const response = await fetch(
        `/api/v1/dexter/observer/companies/${companyId}/insights?${params}`,
        {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`,
          },
        }
      );

      if (!response.ok) {
        throw new Error('Failed to fetch insights');
      }

      const data = await response.json();
      setInsights(data.insights || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
      console.error('Failed to fetch Dexter insights:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleDismissInsight = (index: number) => {
    setInsights(prev => prev.filter((_, i) => i !== index));
  };

  const handleActionClick = (insightType: string, actionLabel: string, data: Record<string, any>) => {
    onActionClick?.(insightType, actionLabel, data);
  };

  if (!panelVisible) {
    return null;
  }

  return (
    <Card className={cn('w-full', className)}>
      <CardHeader>
        <div className="flex items-start justify-between">
          <div className="space-y-1">
            <CardTitle className="text-base flex items-center gap-2">
              <Lightbulb className="h-4 w-4" />
              Dexter (Observation)
            </CardTitle>
            <CardDescription className="text-xs">
              Read-only insights. Dexter cannot take actions.
            </CardDescription>
          </div>
          <Button
            variant="ghost"
            size="sm"
            className="h-6 w-6 p-0"
            onClick={() => setPanelVisible(false)}
          >
            <X className="h-4 w-4" />
          </Button>
        </div>
      </CardHeader>

      <Separator />

      <CardContent className="p-0">
        {loading && (
          <div className="p-6 text-center text-sm text-muted-foreground">
            Analyzing data...
          </div>
        )}

        {error && (
          <div className="p-6 text-center">
            <p className="text-sm text-destructive mb-2">Failed to load insights</p>
            <Button variant="outline" size="sm" onClick={fetchInsights}>
              Retry
            </Button>
          </div>
        )}

        {!loading && !error && insights.length === 0 && (
          <div className="p-6 text-center text-sm text-muted-foreground">
            No insights available at this time.
          </div>
        )}

        {!loading && !error && insights.length > 0 && (
          <ScrollArea className="h-[400px]">
            <div className="p-4 space-y-3">
              {insights.map((insight, index) => (
                <DexterInsightCard
                  key={index}
                  insight={insight}
                  onDismiss={() => handleDismissInsight(index)}
                  onActionClick={(action, data) => handleActionClick(insight.type, action, data)}
                />
              ))}
            </div>
          </ScrollArea>
        )}
      </CardContent>

      <Separator />

      <div className="p-3 bg-muted/30">
        <p className="text-xs text-muted-foreground text-center">
          All insights are optional and dismissible.
        </p>
      </div>
    </Card>
  );
};

export default DexterInsightsPanel;
