'use client';

import { useState, useCallback } from "react";
import { uploadCSV } from "@/lib/api";
import type { ValidationResult } from "@/types";

export function CSVUpload() {
  const [isDragging, setIsDragging] = useState(false);
  const [result, setResult] = useState<ValidationResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isUploading, setIsUploading] = useState(false);

  const handleFile = useCallback(async (file: File) => {
    if (!file.name.endsWith(".csv")) {
      setError("Only .csv files are accepted");
      return;
    }

    setIsUploading(true);
    setError(null);
    setResult(null);

    try {
      const res = await uploadCSV(file);
      setResult(res);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setIsUploading(false);
    }
  }, []);

  const onDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragging(false);
      const file = e.dataTransfer.files[0];
      if (file) handleFile(file);
    },
    [handleFile]
  );

  const onFileInput = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (file) handleFile(file);
    },
    [handleFile]
  );

  return (
    <div className="p-3">
      {/* Drop zone */}
      <div
        onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={onDrop}
        className={`border-2 border-dashed rounded-lg p-4 text-center text-sm transition-colors ${
          isDragging ? "border-blue-500 bg-blue-50" : "border-gray-300 hover:border-gray-400"
        }`}
      >
        <p className="text-gray-500 mb-2">
          {isUploading ? "Uploading..." : "Drop CSV file here or"}
        </p>
        <label className="cursor-pointer text-blue-600 hover:text-blue-700 font-medium">
          browse
          <input
            type="file"
            accept=".csv"
            onChange={onFileInput}
            className="hidden"
            disabled={isUploading}
          />
        </label>
      </div>

      {/* Error */}
      {error && (
        <p className="mt-2 text-xs text-red-600">{error}</p>
      )}

      {/* Result */}
      {result && !isUploading && (
        <div className="mt-3 p-3 bg-gray-50 rounded-lg text-xs">
          <div className="flex items-center gap-2 mb-2">
            <span className={`font-bold text-sm ${result.valid ? "text-green-600" : "text-red-600"}`}>
              {result.valid ? "Valid" : "Invalid"}
            </span>
            <span className="text-gray-500">
              {result.valid_rows}/{result.total_rows} rows
            </span>
          </div>

          {result.errors.length > 0 && (
            <div className="mb-2">
              <h5 className="font-medium text-red-600 mb-1">Errors:</h5>
              <ul className="list-disc list-inside text-red-600 space-y-0.5">
                {result.errors.map((e, i) => <li key={i}>{e}</li>)}
              </ul>
            </div>
          )}

          {result.warnings.length > 0 && (
            <div>
              <h5 className="font-medium text-yellow-600 mb-1">Warnings:</h5>
              <ul className="list-disc list-inside text-yellow-600 space-y-0.5">
                {result.warnings.map((w, i) => <li key={i}>{w}</li>)}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
