import type { Feature } from "@/lib/types";
import FeatureBlock from "./FeatureBlock";

export default function FeatureSection({
  features,
}: {
  features: Feature[];
}) {
  if (!features.length) {
    return (
      <p className="text-gray-500">
        No features listed.
      </p>
    );
  }

  // Group by section
  const grouped = features.reduce<Record<string, Feature[]>>(
    (acc, feature) => {
      acc[feature.section] ||= [];
      acc[feature.section].push(feature);
      return acc;
    },
    {}
  );

  return (
    <div className="space-y-6">
      {Object.entries(grouped).map(([section, items]) => (
        <div key={section}>
          <h3 className="font-semibold mb-2">{section}</h3>
          <div className="space-y-2">
            {items.map((f, i) => (
              <FeatureBlock key={i} feature={f} />
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}