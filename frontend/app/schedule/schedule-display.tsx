import { useState } from "react";
import { TimeSlot, ScheduleItem, ScheduleItemType } from "@/models/Schedule";
import { ChevronLeft, ChevronRight, MapPin } from "lucide-react";

interface ScheduleDisplayProps {
  schedules: ScheduleItem[];
}

// Helper function to check if two dates are the same day
const isSameDay = (date1: Date, date2: Date) => {
  return (
    date1.getFullYear() === date2.getFullYear() &&
    date1.getMonth() === date2.getMonth() &&
    date1.getDate() === date2.getDate()
  );
};

export default function ScheduleDisplay({ schedules }: ScheduleDisplayProps) {
  // Calculate earliest and latest dates from schedules
  const dateRange = schedules.reduce(
    (acc, activity) => {
      const startDate = new Date(activity.time.start_time);
      return {
        earliest: startDate < acc.earliest ? startDate : acc.earliest,
        latest: startDate > acc.latest ? startDate : acc.latest,
      };
    },
    {
      earliest: new Date(
        Math.max(
          ...schedules.map((a) => new Date(a.time.start_time).getTime())
        )
      ),
      latest: new Date(
        Math.min(
          ...schedules.map((a) => new Date(a.time.start_time).getTime())
        )
      ),
    }
  );

  // Initialize current date to the earliest date if available
  const [currentDate, setCurrentDate] = useState(dateRange.earliest);

  // Navigation handlers
  const handlePreviousDay = () => {
    setCurrentDate((prev) => {
      const newDate = new Date(prev);
      newDate.setDate(prev.getDate() - 1);
      return isSameDay(newDate, dateRange.earliest) ||
        newDate > dateRange.earliest
        ? newDate
        : prev;
    });
  };

  const handleNextDay = () => {
    setCurrentDate((prev) => {
      const newDate = new Date(prev);
      newDate.setDate(prev.getDate() + 1);
      return isSameDay(newDate, dateRange.latest) || newDate < dateRange.latest
        ? newDate
        : prev;
    });
  };

  // Check if navigation buttons should be disabled
  const isPreviousDisabled = isSameDay(currentDate, dateRange.earliest);
  const isNextDisabled = isSameDay(currentDate, dateRange.latest);

  // Filter schedules for current date
  const currentDateSchedules = schedules.filter((schedule) =>
    isSameDay(new Date(schedule.time.start_time), currentDate)
  );

  // Helper function to format time
  const formatTime = (date: Date) => {
    return date.toLocaleTimeString("en-US", {
      hour: "2-digit",
      minute: "2-digit",
      hour12: true,
    });
  };

  // Helper function to get schedule background color based on type
  const getScheduleColor = (type: ScheduleItemType) => {
    const colors = {
      [ScheduleItemType.TERMINAL]: "bg-blue-100",
      [ScheduleItemType.TRANSPORT]: "bg-yellow-100",
      [ScheduleItemType.WALK]: "bg-green-100",
      [ScheduleItemType.EVENT]: "bg-purple-100",
      [ScheduleItemType.MUSEUM_GALLERY]: "bg-pink-100",
      [ScheduleItemType.STREETS]: "bg-orange-100",
      [ScheduleItemType.HISTORICAL_SITE]: "bg-red-100",
      [ScheduleItemType.OTHER]: "bg-gray-100",
      [ScheduleItemType.REMOVE]: "bg-gray-100",
    };
    return colors[type] || "bg-gray-100";
  };

  return (
    <div className="max-w-4xl mx-auto">
      {/* Date Navigation */}
      <div className="flex items-center justify-between mb-6">
        <button
          onClick={handlePreviousDay}
          className={`p-2 rounded-full transition-colors ${
            !isPreviousDisabled
              ? "hover:bg-gray-100"
              : "opacity-20 cursor-not-allowed"
          }`}
          aria-label="Previous day"
          disabled={isPreviousDisabled}
        >
          <ChevronLeft className="h-6 w-6" />
        </button>
        <h2 className="text-md font-semibold">
          {currentDate.toLocaleDateString("en-US", {
            weekday: "short",
            year: "numeric",
            month: "long",
            day: "numeric",
          })}
        </h2>
        <button
          onClick={handleNextDay}
          className={`p-2 rounded-full transition-colors ${
            !isNextDisabled
              ? "hover:bg-gray-100"
              : "opacity-20 cursor-not-allowed"
          }`}
          aria-label="Next day"
          disabled={isNextDisabled}
        >
          <ChevronRight className="h-6 w-6" />
        </button>
      </div>

      {/* Schedule Timeline */}
      <div className="relative border-l-2 border-gray-200 ml-2">
        {currentDateSchedules.length === 0 ? (
          <div className="ml-6 py-4 text-gray-500">
            No schedules for this date
          </div>
        ) : (
          currentDateSchedules.map((schedule) => (
            <div key={schedule.id} className="mb-8 ml-6">
              {/* Time Indicator */}
              <div className="flex items-center">
                <div className="absolute -left-1.5 mt-1.5">
                  <div className="h-3 w-3 rounded-full bg-gray-400" />
                </div>
                <time className="mb-1 text-sm font-normal leading-none text-gray-500">
                  {formatTime(new Date(schedule.time.start_time))}
                  {schedule.time.end_time ? (
                    <> - {formatTime(new Date(schedule.time.end_time))}</>
                  ) : null}
                </time>
              </div>

              {/* Schedule Card */}
              <div
                className={`p-4 rounded-lg ${getScheduleColor(
                  schedule.type
                )} mt-2`}
              >
                <h3 className="text-md font-semibold text-gray-900 mb-1">
                  {schedule.title}
                </h3>
                <div className="flex items-center mb-2">
                  <MapPin className="h-4 w-4 text-gray-500 mr-1" />
                  <p className="text-sm text-gray-500">{schedule.location}</p>
                </div>
                <p className="text-sm text-gray-700">{schedule.description}</p>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
