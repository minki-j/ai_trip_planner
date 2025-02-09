"use client";

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
  CardFooter,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { updateSchedule } from "./actions";
import { useState } from "react";
import { TimeSlot, ScheduleItem } from "@/models/Schedule";

interface ScheduleFormProps {
  initialActivities: ScheduleItem[];
}

export default function ScheduleForm({ initialActivities }: ScheduleFormProps) {

  const [activities, setActivities] = useState(initialActivities);
  const [modifiedIndices, setModifiedIndices] = useState<Set<number>>(
    new Set()
  );

  const handleActivityChange = (
    index: number,
    field: keyof ScheduleItem | "time.start_time" | "time.end_time",
    value: string
  ) => {
    const newActivities = [...activities];
    const activity = { ...newActivities[index] };

    // Handle nested fields (e.g., 'time.start_time')
    if (field.includes(".")) {
      const [parent, child] = field.split(".") as [
        keyof ScheduleItem,
        keyof TimeSlot
      ];
      if (parent === "time") {
        activity.time = {
          ...activity.time,
          [child]: new Date(parseInt(value)),
        };
      }
    } else {
      // For non-nested fields, we know field is a direct key of ScheduleItem
      (activity as any)[field] = value;
    }

    newActivities[index] = activity;
    setActivities(newActivities);
    setModifiedIndices(new Set(modifiedIndices).add(index));
  };

  const handleConfirm = async (index: number) => {
    const updatedActivity = activities[index];
    await updateSchedule({
      list_of_activities: activities.map((a, i) =>
        i === index ? updatedActivity : a
      ),
    });
    setModifiedIndices(
      new Set(Array.from(modifiedIndices).filter((i) => i !== index))
    );
  };

  return (
    <div className="space-y-6">
      {activities?.map((activity, index) => (
        <Card key={index} className="w-full">
          <CardContent>
            <div className="grid gap-4">
              <div className="space-y-2">
                <Label htmlFor={`title-${index}`}>Title</Label>
                <Input
                  type="text"
                  id={`title-${index}`}
                  defaultValue={activity.title}
                  onChange={(e) =>
                    handleActivityChange(index, "title", e.target.value)
                  }
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label htmlFor={`start-time-${index}`}>Start Time</Label>
                  <Input
                    type="datetime-local"
                    id={`start-time-${index}`}
                    defaultValue={
                      activity.time.start_time instanceof Date
                        ? activity.time.start_time.toISOString().slice(0, 16)
                        : new Date(activity.time.start_time)
                            .toISOString()
                            .slice(0, 16)
                    }
                    value={
                      activity.time.start_time instanceof Date
                        ? activity.time.start_time.toISOString().slice(0, 16)
                        : new Date(activity.time.start_time)
                            .toISOString()
                            .slice(0, 16)
                    }
                    onChange={(e) =>
                      handleActivityChange(
                        index,
                        "time.start_time",
                        new Date(e.target.value).getTime().toString()
                      )
                    }
                  />
                </div>
                {activity.time.end_time && (
                  <div>
                    <Label htmlFor={`end-time-${index}`}>End Time</Label>
                    <Input
                      type="datetime-local"
                      id={`end-time-${index}`}
                      defaultValue={
                        activity.time.end_time instanceof Date
                          ? activity.time.end_time.toISOString().slice(0, 16)
                          : new Date(activity.time.end_time)
                              .toISOString()
                              .slice(0, 16)
                      }
                      value={
                        activity.time.end_time instanceof Date
                          ? activity.time.end_time.toISOString().slice(0, 16)
                          : new Date(activity.time.end_time)
                              .toISOString()
                              .slice(0, 16)
                      }
                      onChange={(e) =>
                        handleActivityChange(
                          index,
                          "time.end_time",
                          new Date(e.target.value).getTime().toString()
                        )
                      }
                    />
                  </div>
                )}
              </div>
              {activity.location && (
                <div>
                  <Label htmlFor={`location-${index}`}>Location</Label>
                  <Input
                    id={`location-${index}`}
                    defaultValue={activity.location}
                    value={activity.location}
                    onChange={(e) =>
                      handleActivityChange(index, "location", e.target.value)
                    }
                  />
                </div>
              )}
              {activity.description && (
                <div>
                  <Label htmlFor={`description-${index}`}>Description</Label>
                  <Input
                    id={`description-${index}`}
                    defaultValue={activity.description}
                    value={activity.description}
                    onChange={(e) =>
                      handleActivityChange(index, "description", e.target.value)
                    }
                  />
                </div>
              )}
            </div>
          </CardContent>
          <CardFooter className="flex justify-end">
            {modifiedIndices.has(index) && (
              <Button
                onClick={() => handleConfirm(index)}
                className="bg-primary  w-full text-white hover:bg-primary/90"
              >
                Confirm Changes
              </Button>
            )}
          </CardFooter>
        </Card>
      )) || null}
    </div>
  );
}
