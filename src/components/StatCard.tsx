import React from 'react';
import { LucideIcon } from 'lucide-react';

interface StatCardProps {
  title: string;
  value: string | number;
  subtext: string;
  trend?: {
    value: string;
    isPositive: boolean; // positive means SRE metrics got better (e.g. MTTR decreased)
  };
  icon: LucideIcon;
  variant?: 'blue' | 'rose' | 'amber' | 'emerald';
}

export const StatCard: React.FC<StatCardProps> = ({
  title,
  value,
  subtext,
  trend,
  icon: Icon,
  variant = 'blue'
}) => {
  const getColors = () => {
    switch (variant) {
      case 'rose':
        return {
          bg: 'bg-rose-500/10 border-rose-500/20',
          icon: 'text-rose-400 bg-rose-500/15 border-rose-500/30',
        };
      case 'amber':
        return {
          bg: 'bg-amber-500/10 border-amber-500/20',
          icon: 'text-amber-400 bg-amber-500/15 border-amber-500/30',
        };
      case 'emerald':
        return {
          bg: 'bg-emerald-500/10 border-emerald-500/20',
          icon: 'text-emerald-400 bg-emerald-500/15 border-emerald-500/30',
        };
      default:
        return {
          bg: 'bg-blue-500/10 border-blue-500/20',
          icon: 'text-blue-400 bg-blue-500/15 border-blue-500/30',
        };
    }
  };

  const colors = getColors();

  return (
    <div className={`p-5 rounded-xl border bg-slate-900/60 flex items-center justify-between transition-all hover:scale-[1.015] hover:border-slate-800`}>
      <div className="space-y-1">
        <span className="text-xs font-medium text-slate-400 font-sans">{title}</span>
        <div className="flex items-baseline gap-2">
          <span className="text-2xl font-bold text-slate-100 font-sans tracking-tight">{value}</span>
          {trend && (
            <span className={`text-[10.5px] font-mono font-bold px-1.5 py-0.5 rounded-sm ${
              trend.isPositive ? 'text-emerald-400 bg-emerald-500/10' : 'text-rose-400 bg-rose-500/10'
            }`}>
              {trend.value}
            </span>
          )}
        </div>
        <p className="text-[10.5px] text-slate-500 font-mono font-medium leading-none">{subtext}</p>
      </div>

      <div className={`p-3 rounded-lg border shrink-0 ${colors.icon}`}>
        <Icon className="w-5 h-5" />
      </div>
    </div>
  );
};
