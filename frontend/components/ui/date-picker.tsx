"use client";

import * as React from "react";
import { format } from "date-fns";
import { CalendarIcon } from "lucide-react";

import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Calendar } from "@/components/ui/calendar";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";

interface DatePickerProps {
  value?: string;
  onChange?: (date: string | undefined) => void;
}

export function DatePicker({ value, onChange }: DatePickerProps) {
  let date_value: Date | undefined;
  if (value) {
    const numeric_value: number[] = [];
    value?.split("-").forEach((num) => numeric_value.push(Number(num)));
    date_value = new Date(
      numeric_value[0],
      numeric_value[1] - 1,
      numeric_value[2]
    );
  }

  return (
    <Popover>
      <PopoverTrigger asChild>
        <Button
          variant={"outline"}
          className={cn(
            "w-full justify-between text-left font-normal",
            !value && "text-muted-foreground"
          )}
        >
          {value || <span>Pick a date</span>}
          <CalendarIcon className="h-3.5 w-3.5" />
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-auto p-0" align="start">
        <Calendar
          mode="single"
          selected={value ? date_value : undefined}
          onSelect={(date) => {
            onChange?.(date ? date.toISOString().split("T")[0] : undefined);
          }}
          initialFocus
        />
      </PopoverContent>
    </Popover>
  );
}
