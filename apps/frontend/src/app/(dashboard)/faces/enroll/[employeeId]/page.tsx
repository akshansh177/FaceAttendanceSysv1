"use client";

import { useParams } from "next/navigation";
import { useState, useRef } from "react";
import { apiUpload } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export default function FaceEnrollPage() {
  const { employeeId } = useParams<{ employeeId: string }>();
  const [files, setFiles] = useState<File[]>([]);
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [stream, setStream] = useState<MediaStream | null>(null);

  async function startCamera() {
    const media = await navigator.mediaDevices.getUserMedia({ video: true });
    if (videoRef.current) {
      videoRef.current.srcObject = media;
      await videoRef.current.play();
    }
    setStream(media);
  }

  function capturePhoto() {
    if (!videoRef.current || !canvasRef.current) return;
    const canvas = canvasRef.current;
    canvas.width = videoRef.current.videoWidth;
    canvas.height = videoRef.current.videoHeight;
    canvas.getContext("2d")?.drawImage(videoRef.current, 0, 0);
    canvas.toBlob((blob) => {
      if (blob) {
        const file = new File([blob], `capture-${files.length + 1}.jpg`, { type: "image/jpeg" });
        setFiles((prev) => [...prev, file].slice(0, 10));
      }
    }, "image/jpeg");
  }

  async function submit() {
    if (files.length < 5) {
      setMessage("Please provide at least 5 images");
      return;
    }
    setLoading(true);
    const formData = new FormData();
    files.forEach((f) => formData.append("files", f));
    try {
      const res = await apiUpload<{ message: string; embeddings_stored: number }>(
        `/api/faces/enroll?employee_id=${employeeId}`,
        formData
      );
      setMessage(res.message);
    } catch (e) {
      setMessage(e instanceof Error ? e.message : "Enrollment failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold">Face Enrollment</h2>
      <Card>
        <CardHeader>
          <CardTitle>Capture 5–10 face images</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex flex-wrap gap-2">
            <Button onClick={startCamera}>Start Camera</Button>
            <Button onClick={capturePhoto} variant="outline">Capture</Button>
            <input
              type="file"
              accept="image/*"
              multiple
              onChange={(e) => setFiles(Array.from(e.target.files || []))}
              className="text-sm"
            />
          </div>
          <div className="grid gap-4 md:grid-cols-2">
            <video ref={videoRef} className="aspect-video w-full rounded-lg bg-black" muted playsInline />
            <canvas ref={canvasRef} className="hidden" />
            <div className="flex flex-wrap gap-2">
              {files.map((f, i) => (
                <span key={i} className="rounded bg-slate-100 px-2 py-1 text-xs">{f.name}</span>
              ))}
            </div>
          </div>
          <p className="text-sm text-slate-500">{files.length} / 5–10 images selected</p>
          <Button onClick={submit} disabled={loading}>{loading ? "Enrolling..." : "Submit Enrollment"}</Button>
          {message && <p className="text-sm text-brand-700">{message}</p>}
        </CardContent>
      </Card>
    </div>
  );
}
