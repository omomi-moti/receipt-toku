import * as React from "react"
import { Slot } from "@radix-ui/react-slot"
import { cva, type VariantProps } from "class-variance-authority"
import { cn } from "@/lib/utils"

const buttonVariants = cva(
  "inline-flex items-center justify-center whitespace-nowrap rounded-full text-sm font-medium transition-all duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:pointer-events-none disabled:opacity-50 backdrop-blur-md",
  {
    variants: {
      variant: {
        default: "bg-gradient-to-r from-purple-500/80 to-blue-500/80 border border-white/20 text-white hover:from-purple-600/90 hover:to-blue-600/90 shadow-lg",
        destructive: "bg-gradient-to-r from-red-500/70 to-red-600/70 border border-red-400/30 text-white hover:from-red-600/80 hover:to-red-700/80 shadow-lg",
        outline: "bg-gradient-to-r from-purple-500/30 to-blue-500/30 border border-purple-400/30 text-white hover:from-purple-500/50 hover:to-blue-500/50 shadow-md",
        secondary: "bg-gradient-to-r from-purple-500/40 to-blue-500/40 border border-white/20 text-white hover:from-purple-500/60 hover:to-blue-500/60 shadow-md",
        ghost: "hover:bg-white/10 text-foreground",
        link: "text-primary underline-offset-4 hover:underline",
      },
      size: {
        default: "h-10 px-5 py-2",
        sm: "h-9 px-4",
        lg: "h-12 px-8",
        icon: "h-10 w-10",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
)

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, ...props }, ref) => {
    const Comp = asChild ? Slot : "button"
    return (
      <Comp
        className={cn(buttonVariants({ variant, size, className }))}
        ref={ref}
        {...props}
      />
    )
  }
)
Button.displayName = "Button"

export { Button, buttonVariants }
