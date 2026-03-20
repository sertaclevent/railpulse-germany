import type { ReactNode } from "react";

interface NavbarProps {
  children?: ReactNode;
}

export const Navbar = ({ children }: NavbarProps) => (
  <header className="rounded-2xl border border-slate-200 bg-gradient-to-r from-slate-950 via-slate-900 to-cyan-900/90 px-6 py-5 text-white shadow-lg shadow-slate-300/40">
    <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
      <div>
        <p className="text-xs uppercase tracking-[0.24em] text-cyan-200">RailPulse Germany</p>
        <h1 className="mt-1 font-heading text-2xl font-semibold leading-tight md:text-3xl">
          Train Delay Analytics Dashboard
        </h1>
      </div>
      <div className="w-full max-w-xl">{children}</div>
    </div>
  </header>
);
