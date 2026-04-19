'use client';

import dynamic from "next/dynamic";

export const DynamicWellsMap = dynamic(
  () => import("@/components/Map/WellsMap").then((m) => m.WellsMap),
  { ssr: false, loading: () => <div className="w-full h-full bg-gray-100 animate-pulse" /> }
);
