import { Mail, User } from 'lucide-react';
import { Link } from 'react-router-dom';
import { GitHubLogo } from '@/components/icons/GitHubLogo';
import { MemberPublic, LecturerPublic } from '@/types';

type GenericMember = MemberPublic | LecturerPublic;

interface MemberInfoProps {
  members: GenericMember[];
  variant?: 'grid' | 'list' | 'inline' | 'simple';
  showLinks?: boolean;
  className?: string;
}

export const MemberInfo = ({ 
  members, 
  variant = 'list', 
  showLinks = true,
  className = '' 
}: MemberInfoProps) => {
  if (members.length === 0) return null;

  if (variant === 'inline') {
    return (
      <div className={`flex flex-wrap gap-x-2 gap-y-1 text-xs font-bold text-slate-500 ${className}`}>
        {members.map((m, idx) => (
          <span key={'id' in m ? m.id : idx}>
            {m.name}{idx < members.length - 1 ? ',' : ''}
          </span>
        ))}
      </div>
    );
  }

  if (variant === 'simple') {
    return (
      <div className={`text-xs font-bold text-slate-500 flex flex-wrap gap-x-2 gap-y-2 ${className}`}>
        {members.map((m, idx) => (
          <div key={'id' in m ? m.id : idx} className="flex items-center gap-2 px-3 py-1.5 rounded-xl border bg-slate-50 border-slate-100 text-[10px] font-black uppercase tracking-widest text-slate-600">
            {m.name}
          </div>
        ))}
      </div>
    );
  }

  const renderMember = (m: GenericMember, idx: number) => {
    const id = 'id' in m ? m.id : idx;
    
    return (
      <div key={id} className={`flex items-start gap-3 ${variant === 'grid' ? '' : 'mb-4 last:mb-0'}`}>
        <div className="w-10 h-10 rounded-xl bg-slate-50 flex items-center justify-center text-slate-400 font-black shrink-0">
          <User size={18} />
        </div>
        <div className="min-w-0">
          <div className="text-sm font-black text-slate-800 truncate">
            {m.name}
          </div>
          {showLinks && (
            <div className="flex flex-col gap-1 mt-1">
              {m.email && (
                <a href={`mailto:${m.email}`} className="text-[10px] font-bold text-slate-400 hover:text-tul-blue flex items-center gap-1 transition-colors">
                  <Mail size={10} /> {m.email}
                </a>
              )}
              {m.github_alias && (
                <a href={`https://github.com/${m.github_alias}`} target="_blank" rel="noreferrer" className="text-[10px] font-bold text-slate-400 hover:text-tul-blue flex items-center gap-1 transition-colors">
                  <GitHubLogo size={10} /> {m.github_alias}
                </a>
              )}
            </div>
          )}
        </div>
      </div>
    );
  };

  if (variant === 'grid') {
    return (
      <div className={`grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 ${className}`}>
        {members.map(renderMember)}
      </div>
    );
  }

  return (
    <div className={`space-y-4 ${className}`}>
      {members.map(renderMember)}
    </div>
  );
};
