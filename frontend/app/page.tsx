"use client";

import React from "react";
import { PersonalShortsStudio } from "../components/PersonalShortsStudio";

export default function Home() {
  return (
    <main className="min-h-screen bg-[var(--color-dominant)] text-[var(--color-secondary)] antialiased">
      <PersonalShortsStudio />
    </main>
  );
}
