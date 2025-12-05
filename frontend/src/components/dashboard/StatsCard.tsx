import React from 'react';
import { LucideIcon } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';
import { cn } from '@/lib/utils';

interface StatsCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon?: LucideIcon;
  trend?: {
    value: number;
    isPositive: boolean;
  };
  color?: 'teal' | 'navy' | 'yellow' | 'green' | 'red';
  className?: string;
}

const colorClasses = {
  teal: {
    icon: 'text-teal-600',
    bg: 'bg-teal-50',
    trend: 'text-teal-600',
  },
  navy: {
    icon: 'text-blue-900',
    bg: 'bg-blue-50',
    trend: 'text-blue-900',
  },
  yellow: {
    icon: 'text-yellow-600',
    bg: 'bg-yellow-50',
    trend: 'text-yellow-600',
  },
  green: {
    icon: 'text-green-600',
    bg: 'bg-green-50',
    trend: 'text-green-600',
  },
  red: {
    icon: 'text-red-600',
    bg: 'bg-red-50',
    trend: 'text-red-600',
  },
};

export const StatsCard: React.FC<StatsCardProps> = ({
  title,
  value,
  subtitle,
  icon: Icon,
  trend,
  color = 'teal',
  className,
}) => {
  const colors = colorClasses[color];

  return (
    <Card
      className={cn(
        'hover:shadow-lg transition-all duration-300 border-0 bg-white',
        className
      )}
    >
      <CardContent className="p-6">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <p className="text-sm font-medium text-gray-600 mb-2">{title}</p>
            <div className="flex items-baseline space-x-2">
              <h3 className="text-3xl font-bold text-gray-900">{value}</h3>
              {trend && (
                <span
                  className={cn(
                    'text-sm font-semibold',
                    trend.isPositive ? 'text-green-600' : 'text-red-600'
                  )}
                >
                  {trend.isPositive ? '+' : ''}
                  {trend.value}%
                </span>
              )}
            </div>
            {subtitle && <p className="text-sm text-gray-500 mt-1">{subtitle}</p>}
          </div>
          {Icon && (
            <div className={cn('p-3 rounded-xl', colors.bg)}>
              <Icon className={cn('h-6 w-6', colors.icon)} />
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
};
