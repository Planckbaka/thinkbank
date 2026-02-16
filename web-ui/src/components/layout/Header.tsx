/**
 * ThinkBank - Header Component
 */

import { Upload, Images, Search } from 'lucide-react';
import { Link, useLocation } from 'react-router-dom';
import { Button } from '@/components/ui/button';

export function Header() {
  const location = useLocation();

  const isActive = (path: string) => location.pathname === path;

  return (
    <header className="border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container mx-auto flex h-14 items-center justify-between px-4">
        <div className="flex items-center gap-6">
          <Link to="/" className="flex items-center gap-2">
            <div className="h-8 w-8 rounded-lg bg-primary flex items-center justify-center">
              <span className="text-primary-foreground font-bold text-sm">TB</span>
            </div>
            <span className="font-semibold text-lg hidden sm:block">ThinkBank</span>
          </Link>

          <nav className="flex items-center gap-1">
            <Link to="/">
              <Button
                variant={isActive('/') ? 'secondary' : 'ghost'}
                size="sm"
                className="gap-2"
              >
                <Images className="h-4 w-4" />
                <span className="hidden sm:inline">Gallery</span>
              </Button>
            </Link>
            <Link to="/upload">
              <Button
                variant={isActive('/upload') ? 'secondary' : 'ghost'}
                size="sm"
                className="gap-2"
              >
                <Upload className="h-4 w-4" />
                <span className="hidden sm:inline">Upload</span>
              </Button>
            </Link>
            <Link to="/search">
              <Button
                variant={isActive('/search') ? 'secondary' : 'ghost'}
                size="sm"
                className="gap-2"
              >
                <Search className="h-4 w-4" />
                <span className="hidden sm:inline">Search</span>
              </Button>
            </Link>
          </nav>
        </div>
      </div>
    </header>
  );
}
