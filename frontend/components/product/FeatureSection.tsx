import type { Feature } from "@/lib/types";

export default function FeatureSection({ features }: { features: Feature[] }) {
  if (!features.length) return <p className="text-sm text-gray-500">No features listed.</p>;

  const grouped = features.reduce<Record<string, Feature[]>>((acc, f) => {
    (acc[f.section] ||= []).push(f);
    return acc;
  }, {});

  return (
    <div className="grid gap-4 md:grid-cols-2">
      {Object.entries(grouped).map(([section, items]) => (
        <div key={section} className="rounded-2xl bg-white p-5 ring-1 ring-gray-100">
          <h3 className="mb-3 text-xs font-bold uppercase tracking-wider text-brand-600">{section}</h3>
          <ul className="space-y-2.5">
            {items.map((f, i) => (
              <li key={i} className="flex gap-2 text-sm leading-relaxed text-gray-700">
                <span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-accent-400" aria-hidden />
                <span>
                  {f.title && <span className="font-semibold text-gray-900">{f.title}: </span>}
                  {f.description}
                </span>
              </li>
            ))}
          </ul>
        </div>
      ))}
    </div>
  );
}
