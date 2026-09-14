import * as React from "react"
import Image from "next/image"
import { Kadwa } from "next/font/google"
import { type LucideIcon } from "lucide-react"
import { cn } from "cn"
import { Card, CardHeader, CardTitle, CardContent } from "./card"

export const kadwa = Kadwa({ subsets: ["latin"], weight: ["400", "700"] })

export type ToneCardStat = {
  icon: LucideIcon
  label: string
}

export type ToneCardTag = {
  icon: LucideIcon
  label: string
  className?: string
}

function Tag({ icon: Icon, label, className }: ToneCardTag) {
  return (
    <div className={cn("flex items-center gap-1 text-xs sm:text-sm sm:pl-11 sm:py-6", className)}>
      <Icon className="size-5" />
      {label}
    </div>
  )
}

function StatPill({ icon: Icon, label }: ToneCardStat) {
  return (
    <div className="flex flex-1 items-center justify-center gap-1 rounded-lg bg-[#f2f0f0] p-2 text-xs text-[#503535]">
      <Icon className="size-4" />
      {label}
    </div>
  )
}

export type ToneCardProps = {
  className?: string
  /** Photo shown in the card header. Takes precedence over headerIcon/headerGradient. */
  headerImage?: string
  /** Background classes for the header when no headerImage is given. */
  headerGradient?: string
  /** Icon shown centered in the header when no headerImage is given. */
  headerIcon?: LucideIcon
  title: string
  /** Main content area, specific to each feature (a quote, a list, a live indicator, ...). */
  body: React.ReactNode
  tag?: ToneCardTag
  stats: [ToneCardStat, ToneCardStat]
}

export function ToneCard({
  className,
  headerImage,
  headerGradient,
  headerIcon: HeaderIcon,
  title,
  body,
  tag,
  stats,
}: ToneCardProps) {
  return (
    <Card
      className={cn(
        "h-full gap-0 rounded-[24px] py-0 ring-0 shadow-[0_8px_16px_0_rgba(140,16,16,0.1)]",
        className
      )}
    >
      <div
        className={cn(
          "relative flex h-[38px] w-full h-[60px] shrink-0 items-center justify-center sm:h-[68px]",
          headerGradient
        )}
      >
        {headerImage ? (
          <Image src={headerImage} alt="" fill className="object-cover" />
        ) : (
          HeaderIcon && <HeaderIcon className="size-5 text-white sm:size-8" />
        )}
      </div>
      <CardHeader className="grid-rows-[auto_1fr] gap-5 px-6 pt-6 sm:px-4 flex-1">
        <CardTitle
          className={cn(kadwa.className, "text-[1.4rem] text-[#260000] text-center")}
        >
          {title}
        </CardTitle>
        <div className="flex h-full flex-col justify-between gap-2 px-6 sm:px-14">
          {body}
          {tag && <Tag {...tag} />}
        </div>
      </CardHeader>
      <CardContent className="flex gap-3 px-8 pt-5 pb-5 ">
        <StatPill {...stats[0]} />
        <StatPill {...stats[1]} />
      </CardContent>
    </Card>
  )
}

export default ToneCard
