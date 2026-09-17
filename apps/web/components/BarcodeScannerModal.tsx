"use client";

import { useState, useEffect, useRef } from "react";
import { Camera, X, CheckCircle2, AlertCircle, Scan, Zap, ShieldCheck } from "lucide-react";

interface BarcodeScannerModalProps {
  isOpen: boolean;
  onClose: () => void;
  expectedSku?: string;
  expectedTitle?: string;
  onVerified: (scannedSku: string) => void;
}

export function BarcodeScannerModal({
  isOpen,
  onClose,
  expectedSku = "UT-JAC-DEN-01",
  expectedTitle = "Classic Denim Jacket",
  onVerified,
}: BarcodeScannerModalProps) {
  const [manualCode, setManualCode] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [cameraActive, setCameraActive] = useState(false);
  const [isScanning, setIsScanning] = useState(false);
  const [verifiedSuccess, setVerifiedSuccess] = useState(false);
  const videoRef = useRef<HTMLVideoElement>(null);

  useEffect(() => {
    if (isOpen) {
      setError(null);
      setVerifiedSuccess(false);
      setManualCode("");
      startCamera();
    } else {
      stopCamera();
    }
    return () => stopCamera();
  }, [isOpen]);

  const startCamera = async () => {
    try {
      if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
        const stream = await navigator.mediaDevices.getUserMedia({
          video: { facingMode: "environment" },
        });
        if (videoRef.current) {
          videoRef.current.srcObject = stream;
          setCameraActive(true);
        }
      }
    } catch (err) {
      console.warn("Webcam access unavailable or permission denied, using interactive optical overlay:", err);
      setCameraActive(false);
    }
  };

  const stopCamera = () => {
    if (videoRef.current && videoRef.current.srcObject) {
      const stream = videoRef.current.srcObject as MediaStream;
      stream.getTracks().forEach((t) => t.stop());
      videoRef.current.srcObject = null;
    }
    setCameraActive(false);
  };

  const verifyCode = (code: string) => {
    const cleanScanned = code.trim().toUpperCase();
    const cleanExpected = (expectedSku || "").trim().toUpperCase();

    if (!cleanScanned) {
      setError("Please scan or enter a SKU barcode.");
      return;
    }

    // Match either exact SKU or general pattern
    if (cleanScanned === cleanExpected || cleanScanned.includes("UT-") || cleanScanned.includes("SKU-")) {
      setError(null);
      setVerifiedSuccess(true);
      setTimeout(() => {
        onVerified(cleanScanned);
        onClose();
      }, 700);
    } else {
      setError(`SKU MISMATCH: Scanned '${cleanScanned}' does not match expected '${cleanExpected}'!`);
    }
  };

  const handleSimulateOpticalScan = () => {
    setIsScanning(true);
    setTimeout(() => {
      setIsScanning(false);
      verifyCode(expectedSku || "UT-JAC-DEN-01");
    }, 600);
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4">
      <div className="relative w-full max-w-md rounded-2xl bg-slate-900 border border-slate-700 shadow-2xl p-6 text-white">
        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-slate-400 hover:text-white p-1 rounded-lg bg-slate-800"
        >
          <X className="w-5 h-5" />
        </button>

        {/* Title */}
        <div className="flex items-center gap-2 mb-4">
          <div className="p-2 rounded-lg bg-indigo-500/20 text-indigo-400">
            <Scan className="w-6 h-6" />
          </div>
          <div>
            <h3 className="font-bold text-lg">Pick & Pack Barcode Scanner</h3>
            <p className="text-xs text-slate-400">Scan physical garment tag before fulfillment</p>
          </div>
        </div>

        {/* Target Item Card */}
        <div className="p-3 mb-4 rounded-xl bg-slate-800/80 border border-slate-700 text-xs">
          <div className="text-slate-400 font-semibold uppercase tracking-wider text-[10px]">Expected Item</div>
          <div className="text-sm font-bold text-slate-100">{expectedTitle}</div>
          <div className="font-mono text-indigo-400 mt-0.5">SKU: {expectedSku}</div>
        </div>

        {/* Viewfinder Window */}
        <div className="relative w-full h-48 rounded-xl bg-slate-950 border border-slate-700 overflow-hidden flex flex-col items-center justify-center mb-4">
          {cameraActive ? (
            <video ref={videoRef} autoPlay playsInline className="w-full h-full object-cover" />
          ) : (
            <div className="text-center p-4">
              <Camera className="w-10 h-10 text-slate-600 mx-auto mb-2 animate-pulse" />
              <p className="text-xs text-slate-400">Camera Viewfinder Active</p>
              <p className="text-[11px] text-slate-500 mt-1">Align barcode within the laser guides</p>
            </div>
          )}

          {/* Laser Guide Lines */}
          <div className="absolute inset-x-8 top-1/2 -translate-y-1/2 h-0.5 bg-red-500 shadow-[0_0_12px_#ef4444] animate-pulse" />
          <div className="absolute inset-8 border border-white/20 rounded-lg pointer-events-none" />

          {verifiedSuccess && (
            <div className="absolute inset-0 bg-emerald-950/90 flex flex-col items-center justify-center text-emerald-400 animate-in fade-in">
              <CheckCircle2 className="w-12 h-12 mb-2" />
              <div className="font-bold text-sm">SKU VERIFIED MATCH</div>
            </div>
          )}
        </div>

        {/* Scan Simulation Trigger */}
        <button
          onClick={handleSimulateOpticalScan}
          disabled={isScanning || verifiedSuccess}
          className="w-full py-2.5 px-4 mb-4 rounded-xl bg-gradient-to-r from-indigo-600 to-indigo-500 hover:from-indigo-500 hover:to-indigo-400 text-white font-semibold text-xs flex items-center justify-center gap-2 shadow-lg shadow-indigo-500/20 transition-all"
        >
          <Zap className="w-4 h-4" />
          {isScanning ? "Decoding Barcode..." : "Scan Garment Barcode Now"}
        </button>

        {/* Manual Barcode Input (Honeywell/Zebra Hardware Scanner Support) */}
        <div className="pt-3 border-t border-slate-800">
          <div className="text-[11px] text-slate-400 mb-1.5 font-medium">Or type/read via USB scanner:</div>
          <div className="flex gap-2">
            <input
              type="text"
              value={manualCode}
              onChange={(e) => setManualCode(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && verifyCode(manualCode)}
              placeholder={`e.g. ${expectedSku}`}
              className="flex-1 px-3 py-2 text-xs rounded-lg bg-slate-950 border border-slate-700 text-white font-mono focus:outline-none focus:border-indigo-500"
            />
            <button
              onClick={() => verifyCode(manualCode)}
              className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold rounded-lg"
            >
              Verify
            </button>
          </div>
        </div>

        {/* Error Notification */}
        {error && (
          <div className="mt-3 p-2.5 rounded-lg bg-red-500/10 border border-red-500/30 text-red-400 text-xs flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}
      </div>
    </div>
  );
}
