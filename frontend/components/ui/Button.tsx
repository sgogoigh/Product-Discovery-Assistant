import type { ButtonHTMLAttributes } from "react";

type Variant = "primary" | "secondary" | "ghost";

const styles: Record<Variant, string> = {
  primary: "bg-brand-gradient text-white shadow-sm hover:brightness-105 hover:shadow-md",
  secondary: "border border-gray-200 bg-white text-gray-800 hover:border-brand-200 hover:bg-brand-50",
  ghost: "text-gray-600 hover:bg-gray-100",
};

export default function Button({
  variant = "primary",
  className = "",
  type = "button",
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement> & { variant?: Variant }) {
  return (
    <button
      type={type}
      className={`rounded-full px-5 py-2 text-sm font-semibold transition focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-400 focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 disabled:shadow-none ${styles[variant]} ${className}`}
      {...props}
    />
  );
}
