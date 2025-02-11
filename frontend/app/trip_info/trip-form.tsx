"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter, usePathname } from "next/navigation";
import { redirect } from "next/navigation";

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
import { ScheduleItem, ScheduleItemType } from "@/models/Schedule";

export function TripForm({ user }: { user: User }) {
  const { toast } = useToast();
  const router = useRouter();
  const pathname = usePathname();
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);

  const [fixedSchedules, setFixedSchedules] = useState<ScheduleItem[]>(
    user.trip_fixed_schedules
  );
  const newSchedulePlaceholder = {
    id: 999, // start from 9999 and go down
    type: ScheduleItemType.EVENT,
    time: { start_time: new Date(), end_time: null },
    location: "",
    title: "",
    description: null,
    suggestion: null,
  };
  const [newSchedule, setNewSchedule] = useState<ScheduleItem>(
    newSchedulePlaceholder
  );
  const [showNewFixedScheduleForm, setShowNewFixedScheduleForm] =
    useState(false);

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

  async function submitForm(formData: FormData) {
    setHasUnsavedChanges(false);
    const formDataObject = Object.fromEntries(formData.entries());

    formDataObject["trip_arrival_date"] = arrivalDate || "";
    formDataObject["trip_departure_date"] = departureDate || "";

    console.log("formDataObject: ", formDataObject);

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
      action={submitForm}
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
          defaultValue={user.user_interests ?? ""}
          placeholder="e.g. History, Pizza, Jazz, Architecture"
          required
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
          placeholder="e.g. New York City"
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
          defaultValue={user.trip_budget ?? ""}
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
        <Select
          name="trip_theme"
          defaultValue={user.trip_theme ?? ""}
          required
        >
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
        />
        <Input
          type="time"
          id="trip_arrival_time"
          name="trip_arrival_time"
          required
          defaultValue={user.trip_arrival_time ?? ""}
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
        />
        <Input
          type="time"
          id="trip_departure_time"
          name="trip_departure_time"
          required
          defaultValue={user.trip_departure_time ?? ""}
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
          htmlFor="trip_accommodation_location"
          className="block text-sm font-medium"
        >
          Accommodation Location
        </Label>
        <Input
          id="trip_accommodation_location"
          name="trip_accommodation_location"
          required
          defaultValue={user.trip_accommodation_location ?? ""}
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
          defaultValue={user.trip_start_of_day_at ?? ""}
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
          defaultValue={user.trip_end_of_day_at ?? ""}
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
          {fixedSchedules?.length > 0 && (
            <div className="space-y-2">
              {fixedSchedules.map((schedule, index) => (
                <div
                  key={index}
                  className="flex flex-col gap-2 border p-4 rounded-md"
                >
                  <div className="flex justify-between items-center">
                    <span className="font-medium">{schedule.title}</span>
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
                        hiddenInput.value = JSON.stringify(newSchedules);
                        setFixedSchedules(newSchedules);
                      }}
                    >
                      ✕
                    </Button>
                  </div>
                  <div className="text-sm text-muted-foreground grid grid-cols-2 gap-2">
                    <div>
                      <span className="font-medium">Type:</span> {schedule.type}
                    </div>
                    <div>
                      <span className="font-medium">Location:</span>{" "}
                      {schedule.location}
                    </div>
                    <div className="col-span-2">
                      <span className="font-medium">Time:</span>{" "}
                      {new Date(schedule.time.start_time).toLocaleString()}
                      {schedule.time.end_time && (
                        <>
                          {" "}
                          - {new Date(schedule.time.end_time).toLocaleString()}
                        </>
                      )}
                    </div>
                    {schedule.description && (
                      <div className="col-span-2">
                        <span className="font-medium">Description:</span>{" "}
                        {schedule.description}
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
          {showNewFixedScheduleForm ? (
            <div className="space-y-2 border p-4 rounded-md bg-gray-50">
              <div className="grid grid-cols-2 gap-2">
                <div className="space-y-2">
                  <Label htmlFor="schedule_type">Type</Label>
                  <select
                    id="schedule_type"
                    className="w-full p-2 border rounded-md"
                    value={newSchedule.type}
                    onChange={(e) =>
                      setNewSchedule((prev) => ({
                        ...prev,
                        type: e.target.value as ScheduleItemType,
                      }))
                    }
                  >
                    {Object.values(ScheduleItemType).map((type) => (
                      <option key={type} value={type}>
                        {type.replace(/_/g, " ").toLowerCase()}
                      </option>
                    ))}
                  </select>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="schedule_location">Location</Label>
                  <Input
                    id="schedule_location"
                    value={newSchedule.location}
                    onChange={(e) =>
                      setNewSchedule((prev) => ({
                        ...prev,
                        location: e.target.value,
                      }))
                    }
                    placeholder="Enter location"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="schedule_start_time">Start Time</Label>
                  <Input
                    id="schedule_start_time"
                    type="datetime-local"
                    value={
                      newSchedule.time.start_time instanceof Date
                        ? newSchedule.time.start_time.getFullYear() +
                          "-" +
                          String(
                            newSchedule.time.start_time.getMonth() + 1
                          ).padStart(2, "0") +
                          "-" +
                          String(
                            newSchedule.time.start_time.getDate()
                          ).padStart(2, "0") +
                          "T" +
                          String(
                            newSchedule.time.start_time.getHours()
                          ).padStart(2, "0") +
                          ":" +
                          String(
                            newSchedule.time.start_time.getMinutes()
                          ).padStart(2, "0")
                        : ""
                    }
                    onChange={(e) =>
                      setNewSchedule((prev) => ({
                        ...prev,
                        time: {
                          ...prev.time,
                          start_time: new Date(e.target.value),
                        },
                      }))
                    }
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="schedule_end_time">End Time</Label>
                  <Input
                    id="schedule_end_time"
                    type="datetime-local"
                    value={
                      newSchedule.time.end_time instanceof Date
                        ? newSchedule.time.end_time.getFullYear() +
                          "-" +
                          String(
                            newSchedule.time.end_time.getMonth() + 1
                          ).padStart(2, "0") +
                          "-" +
                          String(newSchedule.time.end_time.getDate()).padStart(
                            2,
                            "0"
                          ) +
                          "T" +
                          String(newSchedule.time.end_time.getHours()).padStart(
                            2,
                            "0"
                          ) +
                          ":" +
                          String(
                            newSchedule.time.end_time.getMinutes()
                          ).padStart(2, "0")
                        : ""
                    }
                    onChange={(e) =>
                      setNewSchedule((prev) => ({
                        ...prev,
                        time: {
                          ...prev.time,
                          end_time: new Date(e.target.value),
                        },
                      }))
                    }
                  />
                </div>
                <div className="col-span-2 space-y-2">
                  <Label htmlFor="schedule_title">Title</Label>
                  <Input
                    id="schedule_title"
                    value={newSchedule.title}
                    onChange={(e) =>
                      setNewSchedule((prev) => ({
                        ...prev,
                        title: e.target.value,
                      }))
                    }
                    placeholder="Enter title"
                  />
                </div>
                <div className="col-span-2 space-y-2">
                  <Label htmlFor="schedule_description">
                    Description (Optional)
                  </Label>
                  <textarea
                    id="schedule_description"
                    className="w-full p-2 border rounded-md"
                    value={newSchedule.description || ""}
                    onChange={(e) =>
                      setNewSchedule((prev) => ({
                        ...prev,
                        description: e.target.value || null,
                      }))
                    }
                    placeholder="Enter description"
                    rows={3}
                  />
                </div>
              </div>
              <Button
                type="button"
                variant="default"
                className="w-full"
                onClick={() => {
                  if (
                    newSchedule.title &&
                    newSchedule.location &&
                    newSchedule.time.start_time
                  ) {
                    const schedule = {
                      ...newSchedule,
                      id: newSchedule.id - (fixedSchedules?.length || 0), // adjust id
                    };
                    const newSchedules = [...(fixedSchedules || []), schedule];
                    const hiddenInput = document.getElementById(
                      "trip_fixed_schedules"
                    ) as HTMLInputElement;
                    hiddenInput.value = JSON.stringify(newSchedules);
                    setFixedSchedules(newSchedules);
                    setNewSchedule(newSchedulePlaceholder);
                    setShowNewFixedScheduleForm(false);
                  }
                }}
              >
                Add
              </Button>
            </div>
          ) : (
            <Button
              type="button"
              variant="outline"
              className="w-full text-muted-foreground"
              onClick={() => setShowNewFixedScheduleForm(true)}
            >
              + Add
            </Button>
          )}
          <input
            type="hidden"
            id="trip_fixed_schedules"
            name="trip_fixed_schedules"
            value={JSON.stringify(fixedSchedules)}
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
          placeholder="e.g. I have a penut allergy"
          rows={1}
          onChange={(e) => {
            e.target.style.height = "auto";
            e.target.style.height = `${e.target.scrollHeight}px`;
          }}
          className="mb-4 max-h-[300px] text-md resize-none leading-relaxed"
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
