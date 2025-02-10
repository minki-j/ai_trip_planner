"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter, usePathname } from "next/navigation";
import { redirect } from "next/navigation";

import { format } from "date-fns";

import { useToast } from "@/components/ui/use-toast";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { DatePicker } from "@/components/ui/date-picker";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

import { updateTrip } from "./actions";

import { User } from "@/models/User";

export function TripForm({ user }: { user: User }) {
  const { toast } = useToast();
  const router = useRouter();
  const pathname = usePathname();
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);

  const [fixedSchedules, setFixedSchedules] = useState<string[]>(
    user.trip_fixed_schedules || []
  );
  const [arrivalDate, setArrivalDate] = useState<string | undefined>(
    user.trip_arrival_date || undefined
  );
  const [departureDate, setDepartureDate] = useState<string | undefined>(
    user.trip_departure_date || undefined
  );

  const additional_info_textareaRef = useRef<HTMLTextAreaElement>(null);
  useEffect(() => {
    if (additional_info_textareaRef.current) {
      additional_info_textareaRef.current.style.height = "auto";
      additional_info_textareaRef.current.style.height = `${additional_info_textareaRef.current.scrollHeight}px`;
    }
  }, [user.user_extra_info]);

  async function clientAction(formData: FormData) {
    setHasUnsavedChanges(false);
    const formDataObject = Object.fromEntries(formData.entries());

    formDataObject["trip_arrival_date"] = arrivalDate || "";
    formDataObject["trip_departure_date"] = departureDate || "";

    const success = await updateTrip(formDataObject);

    if (success) {
      toast({
        title: "Success",
        description: "Your profile has been updated successfully.",
      });
      // redirect("/schedule");
    } else {
      toast({
        title: "Error",
        description: "Your profile could not be updated.",
        variant: "destructive",
      });
    }
  }

  useEffect(() => {
    const handleBeforeUnload = (e: BeforeUnloadEvent) => {
      if (hasUnsavedChanges) {
        e.preventDefault();
        e.returnValue = "";
      }
    };

    window.addEventListener("beforeunload", handleBeforeUnload);

    return () => {
      window.removeEventListener("beforeunload", handleBeforeUnload);
    };
  }, [hasUnsavedChanges]);

  useEffect(() => {
    const handleClick = (e: MouseEvent) => {
      const target = e.target as HTMLElement;
      const anchor = target.closest("a");

      if (!anchor) return;

      const href = anchor.getAttribute("href");
      if (href && href !== pathname) {
        if (hasUnsavedChanges) {
          e.preventDefault();
          e.stopPropagation();

          const confirmed = window.confirm(
            "You have unsaved changes. Are you sure you want to leave?"
          );

          if (confirmed) {
            router.push(href);
          }
        }
      }
    };

    document.addEventListener("click", handleClick, true);
    return () => document.removeEventListener("click", handleClick, true);
  }, [hasUnsavedChanges, pathname, router]);

  const handleInputChange = () => {
    setHasUnsavedChanges(true);
  };

  return (
    <form
      action={clientAction}
      className="space-y-6"
      onChange={handleInputChange}
    >
      <div className="space-y-2">
        <Label htmlFor="user_name" className="block text-sm font-medium">
          Name
        </Label>
        <Input
          type="text"
          id="user_name"
          name="user_name"
          defaultValue={user.user_name ?? ""}
          required
          className="block w-full rounded-md border border-gray-300 px-3 py-2 focus:border-blue-500 focus:ring-blue-500"
        />
      </div>

      <div className="space-y-2">
        <Label htmlFor="user_interests" className="block text-sm font-medium">
          Interests
        </Label>
        <Input
          type="text"
          id="user_interests"
          name="user_interests"
          defaultValue={user.user_interests?.join(", ") ?? ""}
          placeholder="Enter interests separated by commas"
          className="block w-full rounded-md border border-gray-300 px-3 py-2 focus:border-blue-500 focus:ring-blue-500"
        />
      </div>

      <div className="space-y-2">
        <Label htmlFor="trip_location" className="block text-sm font-medium">
          Where are you visiting?
        </Label>
        <Input
          type="text"
          id="trip_location"
          name="trip_location"
          defaultValue={user.trip_location ?? ""}
          required
          className="block w-full rounded-md border border-gray-300 px-3 py-2 focus:border-blue-500 focus:ring-blue-500"
        />
      </div>

      <div className="space-y-2">
        <Label htmlFor="trip_budget" className="block text-sm font-medium">
          Budget
        </Label>
        <Select
          name="trip_budget"
          defaultValue={user.trip_budget ?? "moderate"}
          required
        >
          <SelectTrigger className="w-full">
            <SelectValue placeholder="Select a trip budget" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="budget friendly">Budget-Friendly</SelectItem>
            <SelectItem value="moderate">Moderate</SelectItem>
            <SelectItem value="luxury">Luxury</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <div className="space-y-2">
        <Label htmlFor="trip_theme" className="block text-sm font-medium">
          Theme
        </Label>
        <Select name="trip_theme" defaultValue={user.trip_theme ?? ""} required>
          <SelectTrigger className="w-full">
            <SelectValue placeholder="Select a trip theme" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="Cultural & Heritage">
              Cultural & Heritage
            </SelectItem>
            <SelectItem value="Adventure & Outdoor">
              Adventure & Outdoor
            </SelectItem>
            <SelectItem value="Relaxation & Wellness">
              Relaxation & Wellness
            </SelectItem>
            <SelectItem value="Culinary & Food">Culinary & Food</SelectItem>
            <SelectItem value="Urban Exploration">Urban Exploration</SelectItem>
            <SelectItem value="Nature & Wildlife">Nature & Wildlife</SelectItem>
            <SelectItem value="Luxury & Premium">Luxury & Premium</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <div className="space-y-2">
        <Label
          htmlFor="trip_arrival_info"
          className="block text-sm font-medium"
        >
          Arrival Time
        </Label>
        <DatePicker
          value={arrivalDate}
          onChange={(date) => setArrivalDate(date)}
          name="trip_arrival_date"
        />
        <Input
          type="time"
          id="trip_arrival_time"
          name="trip_arrival_time"
          required
          defaultValue={user.trip_arrival_time ?? "09:00"}
          className="block w-full rounded-md border border-gray-300 px-3 py-2 focus:border-blue-500 focus:ring-blue-500"
        />
      </div>

      <div className="space-y-2">
        <Label
          htmlFor="trip_arrival_terminal"
          className="block text-sm font-medium"
        >
          Arrival Terminal
        </Label>
        <Input
          id="trip_arrival_terminal"
          name="trip_arrival_terminal"
          required
          defaultValue={user.trip_arrival_terminal ?? ""}
          placeholder="e.g. Laguardia Airport"
          className="block w-full rounded-md border border-gray-300 px-3 py-2 focus:border-blue-500 focus:ring-blue-500"
        />
      </div>

      <div className="space-y-2">
        <Label
          htmlFor="trip_departure_info"
          className="block text-sm font-medium"
        >
          Departure Time
        </Label>
        <DatePicker
          value={departureDate}
          onChange={(date) => setDepartureDate(date)}
          name="trip_departure_date"
        />
        <Input
          type="time"
          id="trip_departure_time"
          name="trip_departure_time"
          required
          defaultValue={user.trip_departure_time ?? "09:00"}
          className="block w-full rounded-md border border-gray-300 px-3 py-2 focus:border-blue-500 focus:ring-blue-500"
        />
      </div>

      <div className="space-y-2">
        <Label
          htmlFor="trip_departure_terminal"
          className="block text-sm font-medium"
        >
          Departure Terminal
        </Label>
        <Input
          id="trip_departure_terminal"
          name="trip_departure_terminal"
          required
          defaultValue={user.trip_departure_terminal ?? ""}
          placeholder="e.g. Laguardia Airport, Feb 22th 9:35 PM"
          className="block w-full rounded-md border border-gray-300 px-3 py-2 focus:border-blue-500 focus:ring-blue-500"
        />
      </div>

      <div className="space-y-2">
        <Label
          htmlFor="trip_accomodation_location"
          className="block text-sm font-medium"
        >
          Accomodation Location
        </Label>
        <Input
          id="trip_accomodation_location"
          name="trip_accomodation_location"
          required
          defaultValue={user.trip_accomodation_location ?? ""}
          placeholder="e.g. 2658 Broadway"
          className="block w-full rounded-md border border-gray-300 px-3 py-2 focus:border-blue-500 focus:ring-blue-500"
        />
      </div>

      <div className="space-y-2">
        <Label
          htmlFor="trip_start_of_day_at"
          className="block text-sm font-medium"
        >
          Start of Day
        </Label>
        <Input
          type="time"
          id="trip_start_of_day_at"
          name="trip_start_of_day_at"
          required
          defaultValue={user.trip_start_of_day_at ?? "09:00"}
          className="block w-full rounded-md border border-gray-300 px-3 py-2 focus:border-blue-500 focus:ring-blue-500"
        />
      </div>

      <div className="space-y-2">
        <Label
          htmlFor="trip_end_of_day_at"
          className="block text-sm font-medium"
        >
          End of Day
        </Label>
        <Input
          type="time"
          id="trip_end_of_day_at"
          name="trip_end_of_day_at"
          required
          defaultValue={user.trip_end_of_day_at ?? "21:00"}
          className="block w-full rounded-md border border-gray-300 px-3 py-2 focus:border-blue-500 focus:ring-blue-500"
        />
      </div>

      <div className="space-y-2">
        <Label
          htmlFor="trip_fixed_schedules"
          className="block text-sm font-medium"
        >
          Fixed Schedules
        </Label>
        <div className="space-y-2">
          <div className="space-y-2">
            {fixedSchedules.map((schedule, index) => (
              <div
                key={index}
                className="flex items-center gap-2 border p-2 rounded-md"
              >
                <span className="flex-1 text-sm">{schedule}</span>
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  onClick={() => {
                    const newSchedules = fixedSchedules.filter(
                      (_, i) => i !== index
                    );
                    const hiddenInput = document.getElementById(
                      "trip_fixed_schedules"
                    ) as HTMLInputElement;
                    hiddenInput.value = newSchedules.join("\n");
                    setFixedSchedules((prev) => prev.concat(newSchedules));
                  }}
                >
                  ✕
                </Button>
              </div>
            ))}
          </div>
          <div className="flex gap-2">
            <Input
              id="schedule_input"
              placeholder="e.g. Feb/22 7AM-12PM, Meeting with client"
              className="flex-1"
            />
            <Button
              type="button"
              variant="secondary"
              onClick={() => {
                const input = document.getElementById(
                  "schedule_input"
                ) as HTMLInputElement;
                const hiddenInput = document.getElementById(
                  "trip_fixed_schedules"
                ) as HTMLInputElement;
                if (input.value.trim()) {
                  const currentSchedules =
                    hiddenInput?.value.split("\n").filter(Boolean) || [];
                  const newSchedules = [
                    ...currentSchedules,
                    input.value.trim(),
                  ];
                  hiddenInput.value = newSchedules.join("\n");
                  input.value = "";
                  setFixedSchedules((prev) => prev.concat(newSchedules));
                }
              }}
            >
              Add
            </Button>
          </div>
          <input
            type="hidden"
            id="trip_fixed_schedules"
            name="trip_fixed_schedules"
            value={user.trip_fixed_schedules?.join("\n") ?? ""}
          />
        </div>
      </div>

      <div className="space-y-2">
        <Label htmlFor="user_extra_info" className="block text-sm font-medium">
          Additional Information
        </Label>
        <Textarea
          ref={additional_info_textareaRef}
          id="user_extra_info"
          name="user_extra_info"
          defaultValue={user.user_extra_info ?? ""}
          rows={4}
          placeholder="Any additional information about your trip preferences..."
          onChange={(e) => {
            e.target.style.height = "auto";
            e.target.style.height = `${e.target.scrollHeight}px`;
          }}
          className="mb-4 min-h-[100px] max-h-[300px] text-md resize-none leading-relaxed"
        />
      </div>

      <div className="w-full">
        <Button type="submit" className="w-full">
          Save Changes
        </Button>
      </div>
    </form>
  );
}
