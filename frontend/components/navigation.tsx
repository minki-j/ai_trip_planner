"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Button } from "@/components/ui/button";
import { PenLine, Brain, User, Clock, Sun, Moon } from "lucide-react";
import { useSession, signIn, signOut } from "next-auth/react";
import { useTheme } from "next-themes";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";

export function Navigation() {
  const pathname = usePathname();
  const { data: session } = useSession();
  const { setTheme, theme } = useTheme();

  const links = [
    { href: "/schedule", label: "Schedule", icon: Clock, requiresAuth: true },
  ];

  return (
    <nav className="border-b">
      <div className="container mx-auto px-4 py-4">
        <div className="flex w-full items-center justify-between space-x-8">
          <div className="flex items-center space-x-8">
            <Link href="/" className="text-xl font-bold">
              <span className="md:hidden">Tour Assistant</span>
              <span className="hidden md:inline text-xl">Tour Assistant</span>
            </Link>
            <div className="flex items-center space-x-4">
              {links.map(({ href, label, icon: Icon, requiresAuth }) =>
                requiresAuth && !session ? (
                  <TooltipProvider key={href}>
                    <Tooltip delayDuration={100}>
                      <TooltipTrigger asChild>
                        <span className="flex items-center space-x-2 opacity-50 hover:opacity-10 cursor-pointer">
                          <Icon className="hidden md:block h-4 w-4" />
                          <span>{label}</span>
                        </span>
                      </TooltipTrigger>
                      <TooltipContent>
                        <p>Please sign in first</p>
                      </TooltipContent>
                    </Tooltip>
                  </TooltipProvider>
                ) : (
                  <Link
                    key={href}
                    href={href}
                    className={`flex items-center space-x-2 ${
                      pathname === href
                        ? "text-primary font-medium"
                        : "text-muted-foreground"
                    }`}
                  >
                    <Icon className="hidden md:block h-4 w-4" />
                    <span>{label}</span>
                  </Link>
                )
              )}
            </div>
          </div>
          <div className="flex items-center space-x-4">
            {/* <Button
              variant="outline"
              size="icon"
              onClick={() => setTheme(theme === "light" ? "dark" : "light")}
            >
              <Sun className="h-[1.2rem] w-[1.2rem] rotate-0 scale-100 transition-all dark:-rotate-90 dark:scale-0" />
              <Moon className="absolute h-[1.2rem] w-[1.2rem] rotate-90 scale-0 transition-all dark:rotate-0 dark:scale-100" />
              <span className="sr-only">Toggle theme</span>
            </Button> */}
            {session && session.user?.name !== "Temporary User" ? (
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button
                    variant="ghost"
                    className="relative h-10 w-10 rounded-full p-0"
                  >
                    {session.user?.image ? (
                      <img
                        src={session.user.image}
                        alt="Profile"
                        className="h-full w-full rounded-full object-cover"
                      />
                    ) : (
                      <div className="h-full w-full rounded-full bg-gray-300" />
                    )}
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end">
                  <DropdownMenuItem asChild>
                    <Link href="/profile" className="cursor-pointer">
                      Profile
                    </Link>
                  </DropdownMenuItem>
                  <DropdownMenuItem
                    onClick={() => signOut()}
                    className="cursor-pointer"
                  >
                    Sign Out
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            ) : (
              <Button onClick={() => signIn("google")}>Sign In</Button>
            )}
          </div>
        </div>
      </div>
    </nav>
  );
}
