import { PulseBlock } from "@/components/dashboard/Skeletons";

export default function Loading() {
  return (
    <div className="mx-auto w-full max-w-[1400px] flex-1 px-4 py-6 sm:px-6">
      <div className="mb-6 flex items-start justify-between border-b border-border pb-6">
        <div>
          <PulseBlock className="mb-2 h-7 w-24" />
          <PulseBlock className="h-4 w-48" />
        </div>
        <PulseBlock className="h-9 w-32" />
      </div>
      <PulseBlock className="h-96 w-full" />
    </div>
  );
}
