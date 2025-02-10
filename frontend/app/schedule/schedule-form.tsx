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
  initialSchedules: ScheduleItem[];
}

export default function ScheduleForm({ initialSchedules }: ScheduleFormProps) {

  const [schedules, setSchedules] = useState(initialSchedules);
  const [modifiedIndices, setModifiedIndices] = useState<Set<number>>(
    new Set()
  );

  const handleActivityChange = (  
    index: number,
    field: keyof ScheduleItem | "time.start_time" | "time.end_time",
    value: string
  ) => {
    const newSchedules = [...schedules];
    const schedule = { ...newSchedules[index] };

    // Handle nested fields (e.g., 'time.start_time')
    if (field.includes(".")) {
      const [parent, child] = field.split(".") as [
        keyof ScheduleItem,
        keyof TimeSlot
      ];
      if (parent === "time") {
        schedule.time = {
          ...schedule.time,
          [child]: new Date(parseInt(value)),
        };
      }
    } else {
      // For non-nested fields, we know field is a direct key of ScheduleItem
      (schedule as any)[field] = value;
    }

    newSchedules[index] = schedule;
    setSchedules(newSchedules);
    setModifiedIndices(new Set(modifiedIndices).add(index));
  };

  const handleConfirm = async (index: number) => {
    const updatedSchedule = schedules[index];
    await updateSchedule({
      list_of_activities: schedules.map((a, i) =>
        i === index ? updatedSchedule : a
      ),
    });
    setModifiedIndices(
      new Set(Array.from(modifiedIndices).filter((i) => i !== index))
    );
  };

  return (
    <div className="space-y-6">
      {schedules?.map((schedule, index) => (
        <Card key={index} className="w-full">
          <CardContent>
            <div className="grid gap-4">
              <div className="space-y-2">
                <Label htmlFor={`title-${index}`}>Title</Label>
                <Input
                  type="text"
                  id={`title-${index}`}
                  defaultValue={schedule.title}
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
                      schedule.time.start_time instanceof Date
                        ? schedule.time.start_time.toISOString().slice(0, 16)
                        : new Date(schedule.time.start_time)
                            .toISOString()
                            .slice(0, 16)
                    }
                    value={
                      schedule.time.start_time instanceof Date
                        ? schedule.time.start_time.toISOString().slice(0, 16)
                        : new Date(schedule.time.start_time)
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
                {schedule.time.end_time && (
                  <div>
                    <Label htmlFor={`end-time-${index}`}>End Time</Label>
                    <Input
                      type="datetime-local"
                      id={`end-time-${index}`}
                      defaultValue={
                        schedule.time.end_time instanceof Date
                          ? schedule.time.end_time.toISOString().slice(0, 16)
                          : new Date(schedule.time.end_time)
                              .toISOString()
                              .slice(0, 16)
                      }
                      value={
                        schedule.time.end_time instanceof Date
                          ? schedule.time.end_time.toISOString().slice(0, 16)
                          : new Date(schedule.time.end_time)
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
              {schedule.location && (
                <div>
                  <Label htmlFor={`location-${index}`}>Location</Label>
                  <Input
                    id={`location-${index}`}
                    defaultValue={schedule.location}
                    value={schedule.location}
                    onChange={(e) =>
                      handleActivityChange(index, "location", e.target.value)
                    }
                  />
                </div>
              )}
              {schedule.description && (
                <div>
                  <Label htmlFor={`description-${index}`}>Description</Label>
                  <Input
                    id={`description-${index}`}
                    defaultValue={schedule.description}
                    value={schedule.description}
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
