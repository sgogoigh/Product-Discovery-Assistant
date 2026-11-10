"use client";

import Image from "next/image";
import { useState } from "react";

type Props = {
  src: string;
  alt: string;
  sizes: string;
  className?: string;
  priority?: boolean;
  zoom?: boolean;
};

/** Product photo in a fixed-ratio box, with a soft placeholder when the URL is missing or broken. */
export default function ProductImage({ src, alt, sizes, className = "", priority, zoom }: Props) {
  const [failed, setFailed] = useState(false);

  return (
    <div className={`relative overflow-hidden bg-brand-50 ${className}`}>
      {src && !failed ? (
        <Image
          src={src}
          alt={alt}
          fill
          sizes={sizes}
          priority={priority}
          className={`object-cover ${zoom ? "transition duration-500 group-hover:scale-105" : ""}`}
          onError={() => setFailed(true)}
        />
      ) : (
        <div className="absolute inset-0 flex items-center justify-center text-xs text-brand-300" aria-hidden>
          No image
        </div>
      )}
    </div>
  );
}
