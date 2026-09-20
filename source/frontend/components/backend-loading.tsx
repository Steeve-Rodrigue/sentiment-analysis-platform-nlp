import { Loader2 } from "lucide-react";

import { stixTwoText } from "@/components/ui/Tonecard";

export function BackendLoading() {
  return (
    <div className="flex flex-col items-center gap-3 rounded-[24px] bg-[#f2f0f0] px-6 py-16 text-center">
      <Loader2 className="size-8 animate-spin text-[#1040b9]" />
      <p className={`${stixTwoText.className} text-[#260000]`}>
        Waking up the model server
      </p>
      <p className="max-w-sm text-sm text-muted-foreground">
        This backend runs on a free tier that sleeps when idle -- the
        first request can take up to a minute to spin it back up.
      </p>
    </div>
  );
}
