import Image from "next/image";
import Link from "next/link";
import { Source_Serif_4 } from "next/font/google";
import {
  ArrowRight,
  Clock,
  Radio,
  Star,
  ThumbsDown,
  ThumbsUp,
} from "lucide-react";

import { cn } from "cn";
import ToneCard, { stixTwoText, type ToneCardProps } from "@/components/ui/Tonecard";

const sourceSerif = Source_Serif_4({
  subsets: ["latin"],
  weight: ["400", "500", "600"],
});

const FEATURES: Omit<ToneCardProps, "className">[] = [
  {
    title: "Read the overall tone",
    headerImage: "/phone.jpg",
    body: (
      <p className={cn(stixTwoText.className, "text-center text-3xs text-[#503535]")}>
        &ldquo;The new UI is incredibly intuitive and the performance is
        lightning fast. I&apos;ve never been happier with a software update.
        It&apos;s a total game-changer for my workflow.&rdquo;
      </p>
    ),
    tag: {
      icon: Star,
      label: "Positive Sentiment Detected",
      className: "text-[#1040b9]",
    },
    stats: [
      { icon: Star, label: "98% Positive" },
      { icon: Clock, label: "12ms" },
    ],
  },
  {
    title: "Break it down by aspect",
    headerImage: "/img2.jpg",
    body: (
      <div className="flex w-full flex-col gap-3">
        <p className={cn(stixTwoText.className, "text-center text-3xs text-[#503535]")}>
          &ldquo;Delivery took way longer than promised, but the customer
          service team was fantastic and the product quality itself is
          top.&rdquo;
        </p>
        <div className="grid grid-cols-1 gap-2 text-[11px] text-[#503535]">
          <li className="flex items-center justify-between gap-2 rounded-lg bg-[#f2f0f0] p-1 ">
            <span >Delivery</span>
            <span className="text-[#D14E38]">Negative</span>
          </li>
          <li className="flex items-center justify-between gap-2 rounded-lg bg-[#f2f0f0] p-1 w-full">
            <span>Customer Service</span>
            <span className="text-[#1F7A5C]">Positive</span>
          </li>
          <li className="flex items-center justify-between gap-2 rounded-lg bg-[#f2f0f0] p-1">
            <span>Product Quality</span>
            <span className="text-[#1F7A5C]">Positive</span>
          </li>
        </div>
      </div>
    ),
    stats: [
      { icon: ThumbsUp, label: "2 Positive" },
      { icon: ThumbsDown, label: "1 Negative" },
    ],
  },
  {
    title: "Watch it happen live",
    headerImage: "/img3.jpeg",
    body: (
      <div className="flex w-full flex-col gap-3">
        <p className={cn(stixTwoText.className, "text-center text-3xs text-[#503535]")}>
          Real reviews stream in continuously: the overall sentiment trend
          line updates over time, alongside a live, sentiment-colored
          bubble chart  one bubble per aspect, sized by how often it
          comes up.
        </p>
        <div className="flex flex-wrap items-center justify-center gap-x-3 gap-y-1.5">
          <span className="text-base font-semibold text-[#D14E38]">Delivery</span>
          <span className="text-xs font-medium text-[#1F7A5C]">Service</span>
          <span className="text-sm font-medium text-[#1F7A5C]">Quality</span>
          <span className="text-[10px] text-[#D14E38]">Price</span>
          <span className="text-xs font-medium text-[#1F7A5C]">Packaging</span>
          <span className="text-[10px] text-[#D14E38]">Refund</span>
        </div>
      </div>
    ),
    stats: [
      { icon: Radio, label: "Live" },
      { icon: Clock, label: "Updates frequently" },
    ],
  },
];

export default function LandingPage() {
  return (
    <main className="flex flex-col">
      <section className="relative overflow-hidden">
        <div className="pointer-events-none absolute inset-x-0 -top-32 flex justify-center">
          <div className="h-80 w-80 rounded-full bg-[blue]/15 blur-3xl sm:h-[28rem] sm:w-[28rem]" />
        </div>

        <div className="container relative mx-auto flex flex-col items-center gap-6 px-6 pt-28 pb-0 text-center sm:px-6 sm:pb-2 lg:px-1">


          <h1
            className={`${sourceSerif.className} max-w-2xl text-4xl font-medium tracking-tight  pt-4    px-1 sm:text-5xl  pt-15 lg:text-6xl`}
          >
            What your customers <span className="text-[blue] text-bold px-1">actually</span> mean
          </h1>
          <div className="flex items-center gap-4">
            <Link
              href="/sentiment"
              className="inline-flex items-center gap-2 rounded-xl bg-[#211BDF] px-6 py-3 text-base font-medium text-white transition-colors hover:bg-[#0f2386]/90"
            >
              Start
              <ArrowRight className="size-4" />
            </Link>
          </div>
          <p className="max-w-xl text-lg text-muted-foreground">
            An aspect-based sentiment analysis platform that
            reads reviews in english  the way a person would  as a whole, and
            piece by piece.
          </p>

        </div>
      </section>
      <section className="container mx-auto px-8 py-10 sm:px-[2%] lg:px-[2%]">
        <div className="grid gap-8 sm:grid-cols-2 lg:grid-cols-3">
          {FEATURES.map((feature) => (
            <ToneCard key={feature.title} {...feature} />
          ))}
        </div>
      </section>
    </main>
  );
}
