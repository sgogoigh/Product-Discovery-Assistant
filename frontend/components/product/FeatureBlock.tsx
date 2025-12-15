import type { Feature } from "@/lib/types";

export default function FeatureBlock({
  feature,
}: {
  feature: Feature;
}) {
  return (
    <div className="border rounded p-3">
      {feature.title && (
        <p className="font-medium">{feature.title}</p>
      )}
      <p className="text-sm text-gray-700">
        {feature.description}
      </p>
    </div>
  );
}