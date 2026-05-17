"use client";

import type { ReactNode } from "react";
import { useEffect, useState } from "react";

const STUDENT_DEVICE_FRAME_WIDTH = 1093;
const STUDENT_DEVICE_FRAME_HEIGHT = 820;

export function StudentDeviceFrame({
  children,
  contentClassName = "",
}: {
  children: ReactNode;
  contentClassName?: string;
}) {
  const [scale, setScale] = useState(1);
  const [isReady, setIsReady] = useState(false);

  useEffect(() => {
    const resizeFrame = () => {
      const availableWidth = Math.max(320, window.innerWidth - 32);
      const availableHeight = Math.max(320, window.innerHeight - 32);
      setScale(Math.min(1, availableWidth / STUDENT_DEVICE_FRAME_WIDTH, availableHeight / STUDENT_DEVICE_FRAME_HEIGHT));
      setIsReady(true);
    };

    resizeFrame();
    window.addEventListener("resize", resizeFrame);
    return () => window.removeEventListener("resize", resizeFrame);
  }, []);

  const activeScale = isReady ? scale : 1;

  return (
    <div
      className="m-auto"
      style={{
        width: STUDENT_DEVICE_FRAME_WIDTH * activeScale,
        height: STUDENT_DEVICE_FRAME_HEIGHT * activeScale,
      }}
    >
      <div
        className="relative origin-top-left rounded-[44px] bg-[#202939] p-4 shadow-[0_30px_90px_rgba(15,23,42,0.28)]"
        style={{
          width: STUDENT_DEVICE_FRAME_WIDTH,
          height: STUDENT_DEVICE_FRAME_HEIGHT,
          transform: `scale(${activeScale})`,
        }}
      >
        <div className="absolute bottom-5 left-1/2 h-1.5 w-24 -translate-x-1/2 rounded-full bg-white/22" />
        <div className={`h-full overflow-hidden rounded-[30px] bg-[#fbfaf4] ${contentClassName}`}>
          {children}
        </div>
      </div>
    </div>
  );
}
