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

interface Activity {
  activity_id: string;
  activity_name: string;
  activity_type: string;
  activity_start_time: string;
  activity_end_time: string;
  activity_location: string;
  activity_budget: string;
  activity_description: string;
}

interface ScheduleFormProps {
  initialActivities: Activity[];
}

export default function ScheduleForm({ initialActivities }: ScheduleFormProps) {
  const [activities, setActivities] = useState(initialActivities);
  const [modifiedIndices, setModifiedIndices] = useState<Set<number>>(
    new Set()
  );

  const handleActivityChange = (
    index: number,
    field: keyof Activity,
    value: string
  ) => {
    const newActivities = [...activities];
    newActivities[index] = {
      ...newActivities[index],
      [field]: value,
    };
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
          <CardHeader>
            <CardTitle>{activity.activity_name}</CardTitle>
            <CardDescription>{activity.activity_type}</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid gap-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label htmlFor={`start-time-${index}`}>Start Time</Label>
                  <Input
                    id={`start-time-${index}`}
                    defaultValue={activity.activity_start_time}
                    value={activity.activity_start_time}
                    onChange={(e) =>
                      handleActivityChange(
                        index,
                        "activity_start_time",
                        e.target.value
                      )
                    }
                  />
                </div>
                <div>
                  <Label htmlFor={`end-time-${index}`}>End Time</Label>
                  <Input
                    id={`end-time-${index}`}
                    defaultValue={activity.activity_end_time}
                    value={activity.activity_end_time}
                    onChange={(e) =>
                      handleActivityChange(
                        index,
                        "activity_end_time",
                        e.target.value
                      )
                    }
                  />
                </div>
              </div>
              <div>
                <Label htmlFor={`location-${index}`}>Location</Label>
                <Input
                  id={`location-${index}`}
                  defaultValue={activity.activity_location}
                  value={activity.activity_location}
                  onChange={(e) =>
                    handleActivityChange(
                      index,
                      "activity_location",
                      e.target.value
                    )
                  }
                />
              </div>
              <div>
                <Label htmlFor={`budget-${index}`}>Budget</Label>
                <Input
                  id={`budget-${index}`}
                  defaultValue={activity.activity_budget}
                  value={activity.activity_budget}
                  onChange={(e) =>
                    handleActivityChange(
                      index,
                      "activity_budget",
                      e.target.value
                    )
                  }
                />
              </div>
              <div>
                <Label htmlFor={`description-${index}`}>Description</Label>
                <Input
                  id={`description-${index}`}
                  defaultValue={activity.activity_description}
                  value={activity.activity_description}
                  onChange={(e) =>
                    handleActivityChange(
                      index,
                      "activity_description",
                      e.target.value
                    )
                  }
                />
              </div>
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
