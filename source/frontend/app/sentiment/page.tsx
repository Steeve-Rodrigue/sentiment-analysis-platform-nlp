import { Source_Serif_4 } from "next/font/google";
import Link from "next/link";
import { ListTree, Radio, Star, ArrowLeft } from "lucide-react";

import { stixTwoText } from "@/components/ui/Tonecard";
import { SentimentForm } from "@/components/sentiment-form";
import { AspectForm } from "@/components/aspect-form";
import { LiveSentimentChart } from "@/components/live-sentiment-chart";
import { LiveAspectBubbles } from "@/components/live-aspect-bubbles";
import { BackendGate } from "@/components/backend-gate";

const sourceSerif = Source_Serif_4({
  subsets: ["latin"],
  weight: ["400", "500", "600"],
});

export default function SentimentPage() {
  return (
    <main className="flex flex-col">
      <section className="relative flex flex-col items-center justify-center gap-3 overflow-hidden bg-gradient-to-b from-[#0D08AF]/50 via-white to-slate-50 px-7 pb-4 pt-5 sm:py-20">
        <div className="pointer-events-none absolute -top-16 -left-16 size-64 rounded-full bg-[#3a67ed]/15 blur-3xl" />
        <div className="pointer-events-none absolute -right-10 -bottom-20 size-72 rounded-full bg-[#1040b9]/10 blur-3xl" />
        <h1
          className={`${sourceSerif.className} relative max-w-xl text-center text-3xl font-medium tracking-tight text-black pt-5  sm:text-6xl`}
        >
          Let&apos;s Try <span className="text-[blue]">it</span> now
        </h1>
        <p className="relative max-w-md text-center text-[12px]  text-muted-foreground sm:text-base">
          Tape a review below and see it analyzed. No setup
          required.
        </p>
      </section>

      <div className="container mx-auto flex flex-col gap-16 px-7 py-12 sm:px-10 lg:px-40">
        <BackendGate>
          <section className="flex flex-col gap-4">
            <div className="flex flex-col gap-2">
              <span
                className={`${stixTwoText.className} inline-flex w-fit items-center gap-2 rounded-full bg-gradient-to-r from-[#1040b9] to-[#3a67ed] px-4 py-1.5 text-sm text-white shadow-sm sm:text-base`}
              >
                <Star className="size-3.5 sm:size-4" />
                Read the overall tone
              </span>
              <p className="text-muted-foreground text-[11px] sm:text-[14px]">
                Tape a customer review. The model reads it whole and gives you
                one verdict : Positive or Negative
              </p>
            </div>
            <SentimentForm />
          </section>

          <section className="flex flex-col gap-4">
            <div className="flex flex-col gap-2">
              <span
                className={`${stixTwoText.className} inline-flex w-fit items-center gap-2 rounded-full bg-gradient-to-r from-[#1040b9] to-[#3a67ed] px-4 py-1.5 text-sm text-white shadow-sm sm:text-base`}
              >
                <ListTree className="size-3.5 sm:size-4" />
                Break it down by aspect
              </span>
              <p className="text-muted-foreground text-[11px] sm:text-[14px]">
                A review often praises one thing and criticizes another. We
                automatically detect the topics it touches
                 and analyse  each one on its own.
              </p>
            </div>
            <AspectForm />
          </section>

          <section className="flex flex-col gap-4">
            <div className="flex flex-col gap-2">
              <span
                className={`${stixTwoText.className} inline-flex w-fit items-center gap-2 rounded-full bg-gradient-to-r from-[#0f2386] to-[#3a67ed] px-4 py-1.5 text-sm text-white shadow-sm sm:text-base`}
              >
                <Radio className="size-3.5 sm:size-4" />
                Watch it happen live
              </span>
              <p className="text-muted-foreground text-[11px] sm:text-[14px]">
                Reviews arrive continuously and are scored the moment they
                land: the overall sentiment trend line updates below, and
                each aspect it touches on lands in the bubble chart, sized
                by how often it comes up.
              </p>
            </div>
            <LiveSentimentChart />
            <LiveAspectBubbles />
          </section>
        </BackendGate>
        <Link
              href="/"
              className="inline-flex items-center gap-2  px-8 text-base font-medium text-blue-500 transition-colors "
            >
              <ArrowLeft className="size-6" />Landing Page

        </Link>

      </div>
    </main>
  );
}
