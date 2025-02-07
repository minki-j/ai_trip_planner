"use client";

import { useEffect, useRef, useState } from "react";
import { redirect } from "next/navigation";

import { useToast } from "@/components/ui/use-toast";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Input } from "@/components/ui/input";
import { DateRangePicker } from "@/components/ui/date-range-picker";
import { format } from "date-fns";
import { DateRange } from "react-day-picker";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,

} from "@/components/ui/select";
import { DatePicker } from "@/components/ui/date-picker";
import { updateTrip } from "./actions";

interface TripFormProps {
  user: {
    user_name: string;
    user_interests: string[];
    user_extra_info: string;
    
    trip_arrival_date: string;
    trip_arrival_time: string;
    trip_arrival_terminal: string;
    
    trip_departure_date: string;
    trip_departure_time: string;
    trip_departure_terminal: string;
    
    trip_start_of_day_at: string;
    trip_end_of_day_at: string;
    
    trip_location: string;
    trip_accomodation_location: string;

    trip_budget: string;
    trip_theme: string;
    trip_fixed_schedules: string[];
  };
}

export function TripForm({ user }: TripFormProps) {
  const [arrivalDate, setArrivalDate] = useState<Date>();
  const [departureDate, setDepartureDate] = useState<Date>();
  
  const { toast } = useToast();
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
    }
  }, [user.user_extra_info]);

  async function clientAction(formData: FormData) {
    const formDataObject = Object.fromEntries(formData.entries());
    formDataObject["trip_arrival_date"] = arrivalDate ? format(arrivalDate, "yyyy-MM-dd") : "";
    formDataObject["trip_departure_date"] = departureDate ? format(departureDate, "yyyy-MM-dd") : "";
    const success = await updateTrip(formDataObject);
    if (success) {
      toast({
        title: "Success",
        description: "Your profile has been updated successfully.",
      });
      redirect("/schedule");
    } else {
      toast({
        title: "Error",
        description: "Your profile could not be updated.",
        variant: "destructive",
      });
    }
  }

  return (
    <form action={clientAction} className="space-y-6">
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
        <Input
          type="text"
          id="trip_budget"
          name="trip_budget"
          defaultValue={user.trip_budget ?? ""}
          placeholder="Enter your budget"
          className="block w-full rounded-md border border-gray-300 px-3 py-2 focus:border-blue-500 focus:ring-blue-500"
        />
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
            <SelectItem value="cultural">Cultural & Heritage</SelectItem>
            <SelectItem value="adventure">Adventure & Outdoor</SelectItem>
            <SelectItem value="relaxation">Relaxation & Wellness</SelectItem>
            <SelectItem value="culinary">Culinary & Food</SelectItem>
            <SelectItem value="urban">Urban Exploration</SelectItem>
            <SelectItem value="nature">Nature & Wildlife</SelectItem>
            <SelectItem value="luxury">Luxury & Premium</SelectItem>
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
          placeholder="e.g. 2658 Broadway"
          className="block w-full rounded-md border border-gray-300 px-3 py-2 focus:border-blue-500 focus:ring-blue-500"
        />
      </div>

      <div className="space-y-2">
        <Label
          htmlFor="trip_start_of_day"
          className="block text-sm font-medium"
        >
          Start of Day
        </Label>
        <Input
          type="time"
          id="trip_start_of_day"
          name="trip_start_of_day"
          required
          defaultValue={user.trip_start_of_day ?? "09:00"}
          className="block w-full rounded-md border border-gray-300 px-3 py-2 focus:border-blue-500 focus:ring-blue-500"
        />
      </div>

      <div className="space-y-2">
        <Label htmlFor="trip_end_of_day" className="block text-sm font-medium">
          End of Day
        </Label>
        <Input
          type="time"
          id="trip_end_of_day"
          name="trip_end_of_day"
          required
          defaultValue={user.trip_end_of_day ?? "21:00"}
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
        <Textarea
          id="trip_fixed_schedules"
          name="trip_fixed_schedules"
          defaultValue={user.trip_fixed_schedules?.join("\n") ?? ""}
          rows={4}
          placeholder="Enter fixed schedules (one per line)"
          className="block w-full rounded-md border border-gray-300 px-3 py-2 focus:border-blue-500 focus:ring-blue-500"
        />
      </div>

      <div className="space-y-2">
        <Label htmlFor="user_extra_info" className="block text-sm font-medium">
          Additional Information
        </Label>
        <Textarea
          ref={textareaRef}
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
