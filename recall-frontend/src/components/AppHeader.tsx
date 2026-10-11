import { BookOpen, MessageSquareText, Plus } from 'lucide-react';
import type { View } from '@/types';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';

const recallMark = new URL('../assets/recall-mark.png', import.meta.url).href;

const NAV: Array<{ view: View; label: string; icon: typeof BookOpen }> = [
  { view: 'ask', label: 'Ask', icon: MessageSquareText },
  { view: 'library', label: 'Library', icon: BookOpen },
];

export default function AppHeader({
  view,
  onNavigate,
  onAddNotes,
}: {
  view: View;
  onNavigate: (view: View) => void;
  onAddNotes: () => void;
}) {
  return (
    <header className="sticky top-0 z-40 border-b bg-background/85 backdrop-blur">
      <div className="container flex h-14 items-center gap-4">
        <button
          type="button"
          onClick={() => onNavigate('ask')}
          className="flex items-center gap-2 rounded-md focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
        >
          <img src={recallMark} alt="" className="h-7 w-7 object-contain" />
          <span className="text-lg font-bold tracking-tight">Recall</span>
        </button>

        <nav className="flex items-center gap-1">
          {NAV.map(({ view: target, label, icon: Icon }) => (
            <Button
              key={target}
              variant="ghost"
              size="sm"
              onClick={() => onNavigate(target)}
              aria-current={view === target ? 'page' : undefined}
              className={cn(view === target ? 'bg-accent text-foreground' : 'text-muted-foreground')}
            >
              <Icon />
              {label}
            </Button>
          ))}
        </nav>

        <Button size="sm" variant="outline" className="ml-auto" onClick={onAddNotes}>
          <Plus />
          <span className="hidden sm:inline">Add notes</span>
        </Button>
      </div>
    </header>
  );
}
