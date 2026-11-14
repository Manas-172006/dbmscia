import React from 'react';

interface BadgeProps {
  status: 'available' | 'returned' | 'removed' | 'new' | 'read' | 'closed' | string;
  className?: string;
}

export const Badge: React.FC<BadgeProps> = ({ status, className = '' }) => {
  const norm = status.toLowerCase();

  let styles = 'bg-slate-100 text-slate-700 border-slate-200';
  let label = status;

  if (norm === 'available') {
    styles = 'bg-emerald-50 text-emerald-700 border-emerald-200';
    label = 'Available / Unclaimed';
  } else if (norm === 'returned') {
    styles = 'bg-blue-50 text-blue-700 border-blue-200';
    label = 'Returned to Owner';
  } else if (norm === 'removed') {
    styles = 'bg-slate-100 text-slate-600 border-slate-300';
    label = 'Archived / Removed';
  } else if (norm === 'new') {
    styles = 'bg-amber-50 text-amber-700 border-amber-300 font-semibold';
    label = 'New Enquiry';
  } else if (norm === 'read') {
    styles = 'bg-indigo-50 text-indigo-700 border-indigo-200';
    label = 'Read / In Progress';
  } else if (norm === 'closed') {
    styles = 'bg-slate-100 text-slate-600 border-slate-200';
    label = 'Resolved / Closed';
  }

  return (
    <span
      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${styles} ${className}`}
    >
      {label}
    </span>
  );
};
