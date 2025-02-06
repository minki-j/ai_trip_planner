"use client";

import { useEffect, useRef } from "react";

import { useToast } from "@/components/ui/use-toast";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

import { updateTrip } from "./actions";

interface TripFormProps {
  user: {
    user_name: string;
    user_interests: string[];
    user_extra_info: string;
    trip_transportation_schedule: string[];
    trip_location: string;
    trip_duration: string;
    trip_budget: string;
    trip_theme: string;
    trip_fixed_schedules: string[];
  };
}

export function TripForm({ user }: TripFormProps) {
  const { toast } = useToast();
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
    }
  }, [user.user_extra_info]);

  async function clientAction(formData: FormData) {
    const success = await updateTrip(formData);
    if (success) {
      toast({
        title: "Success",
        description: "Your profile has been updated successfully.",
      });
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
          Location
        </Label>
        <Input
          type="text"
          id="trip_location"
          name="trip_location"
          defaultValue={user.trip_location ?? ""}
          className="block w-full rounded-md border border-gray-300 px-3 py-2 focus:border-blue-500 focus:ring-blue-500"
        />
      </div>

      <div className="space-y-2">
        <Label htmlFor="trip_duration" className="block text-sm font-medium">
          Duration
        </Label>
        <Input
          type="text"
          id="trip_duration"
          name="trip_duration"
          defaultValue={user.trip_duration ?? ""}
          placeholder="e.g., Feb 19 - March 1"
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
        <Select name="trip_theme" defaultValue={user.trip_theme ?? ""}>
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
        <Label htmlFor="trip_transportation_schedule" className="block text-sm font-medium">
          Transportation Schedule
        </Label>
        <Textarea
          id="trip_transportation_schedule"
          name="trip_transportation_schedule"
          defaultValue={user.trip_transportation_schedule?.join("\n") ?? ""}
          rows={4}
          placeholder="Enter transportation schedules (one per line)"
          className="block w-full rounded-md border border-gray-300 px-3 py-2 focus:border-blue-500 focus:ring-blue-500"
        />
      </div>

      <div className="space-y-2">
        <Label htmlFor="trip_fixed_schedules" className="block text-sm font-medium">
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
