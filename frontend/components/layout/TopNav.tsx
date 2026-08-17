"use client";

import { useState, useRef, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth } from "@/contexts/AuthContext";
import { TickerSearch } from "./TickerSearch";
import { Button } from "@/components/ui/Button";

export function TopNav() {
  const { user, isLoading, logout } = useAuth();
  const router = useRouter();
  const [menuOpen, setMenuOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function onClickOutside(e: MouseEvent) {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) setMenuOpen(false);
    }
    document.addEventListener("mousedown", onClickOutside);
    return () => document.removeEventListener("mousedown", onClickOutside);
  }, []);

  function handleLogout() {
    setMenuOpen(false);
    logout();
    router.push("/");
  }

  return (
    <header className="sticky top-0 z-40 border-b border-border bg-surface/90 backdrop-blur">
      <div className="mx-auto flex max-w-[1400px] items-center gap-6 px-4 py-3 sm:px-6">
        <Link href="/" className="flex shrink-0 items-center gap-2">
          <span className="flex h-7 w-7 items-center justify-center rounded-md bg-primary font-display text-sm font-semibold text-ink-inverse">
            R
          </span>
          <span className="hidden font-display text-[15px] font-semibold tracking-tight text-ink sm:inline">
            Research &amp; Analytics
          </span>
        </Link>

        <div className="flex-1">
          <TickerSearch />
        </div>

        <nav className="hidden shrink-0 items-center gap-5 text-sm text-ink-muted md:flex">
          <Link href="/research/AAPL" className="transition-colors duration-[var(--duration-fast)] hover:text-ink">
            Research
          </Link>
          <Link href="/compare" className="transition-colors duration-[var(--duration-fast)] hover:text-ink">
            Compare
          </Link>
          <Link href="/screener" className="transition-colors duration-[var(--duration-fast)] hover:text-ink">
            Screener
          </Link>
          <Link href="/watchlist" className="transition-colors duration-[var(--duration-fast)] hover:text-ink">
            Watchlist
          </Link>
          <Link href="/portfolio" className="transition-colors duration-[var(--duration-fast)] hover:text-ink">
            Portfolio
          </Link>
        </nav>

        <div className="shrink-0">
          {isLoading ? (
            <div className="h-8 w-20 animate-pulse rounded-md bg-surface-sunken" />
          ) : user ? (
            <div ref={menuRef} className="relative">
              <button
                type="button"
                onClick={() => setMenuOpen((o) => !o)}
                aria-expanded={menuOpen}
                className="flex items-center gap-2 rounded-md border border-border px-2.5 py-1.5 text-sm text-ink transition-colors duration-[var(--duration-fast)] hover:bg-surface-sunken"
              >
                <span className="flex h-5 w-5 items-center justify-center rounded-full bg-primary-soft text-[11px] font-semibold text-primary">
                  {user.display_name.charAt(0).toUpperCase()}
                </span>
                <span className="hidden sm:inline">{user.display_name}</span>
              </button>
              {menuOpen && (
                <div className="animate-dropdown-in origin-top-right absolute right-0 z-30 mt-1.5 w-44 overflow-hidden rounded-md border border-border bg-surface shadow-lg">
                  <Link
                    href="/portfolio"
                    onClick={() => setMenuOpen(false)}
                    className="block px-3 py-2 text-sm text-ink-muted transition-colors duration-[var(--duration-fast)] hover:bg-surface-sunken hover:text-ink"
                  >
                    Portfolio
                  </Link>
                  <Link
                    href="/watchlist"
                    onClick={() => setMenuOpen(false)}
                    className="block px-3 py-2 text-sm text-ink-muted transition-colors duration-[var(--duration-fast)] hover:bg-surface-sunken hover:text-ink"
                  >
                    Watchlist
                  </Link>
                  <button
                    type="button"
                    onClick={handleLogout}
                    className="block w-full px-3 py-2 text-left text-sm text-negative transition-colors duration-[var(--duration-fast)] hover:bg-negative-soft"
                  >
                    Log out
                  </button>
                </div>
              )}
            </div>
          ) : (
            <div className="flex items-center gap-2">
              <Link href="/login">
                <Button variant="ghost" size="sm">
                  Log in
                </Button>
              </Link>
              <Link href="/signup">
                <Button variant="primary" size="sm">
                  Sign up
                </Button>
              </Link>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
