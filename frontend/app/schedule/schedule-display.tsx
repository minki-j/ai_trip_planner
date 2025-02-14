import { useState } from "react";
import {
  ScheduleItem,
  ScheduleItemType,
  ScheduleItemTime,
} from "@/models/Schedule";
import {
  ChevronLeft,
  ChevronRight,
  Clock,
  Plane,
  Bus,
  Map,
  Footprints,
  Calendar,
  Ticket,
  Landmark,
  Utensils,
  Heart,
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { Button } from "@/components/ui/button";
import { Edit } from "lucide-react";

interface ScheduleDisplayProps {
  schedules: ScheduleItem[];
  startGeneration: () => void;
  setIsEditMode: React.Dispatch<React.SetStateAction<boolean>>;
}

// Helper function to check if two dates are the same day
const isSameDay = (date1: Date, date2: Date) => {
  return (
    date1.getFullYear() === date2.getFullYear() &&
    date1.getMonth() === date2.getMonth() &&
    date1.getDate() === date2.getDate()
  );
};

export default function ScheduleDisplay({
  schedules,
  startGeneration,
  setIsEditMode,
}: ScheduleDisplayProps) {
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
        Math.max(...schedules.map((a) => new Date(a.time.start_time).getTime()))
      ),
      latest: new Date(
        Math.min(...schedules.map((a) => new Date(a.time.start_time).getTime()))
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

  // Filter schedules for current date and sort by start time
  const currentDateSchedules = schedules
    .filter((schedule) =>
      isSameDay(new Date(schedule.time.start_time), currentDate)
    )
    .sort(
      (a, b) =>
        new Date(a.time.start_time).getTime() -
        new Date(b.time.start_time).getTime()
    );

  // Helper function to format time
  const formatTime = (date: Date) => {
    return date.toLocaleTimeString("en-US", {
      hour: "2-digit",
      minute: "2-digit",
      hour12: true,
    });
  };

  // Helper function to get schedule styling based on type
  const getScheduleStyling = (type: ScheduleItemType) => {
    const styles = {
      [ScheduleItemType.TERMINAL]: {
        bg: "bg-blue-50",
        border: "border-blue-200",
        icon: Plane,
      },
      [ScheduleItemType.TRANSPORT]: {
        bg: "bg-green-50",
        border: "border-green-200",
        icon: Bus,
      },
      [ScheduleItemType.WALK]: {
        bg: "bg-green-50",
        border: "border-green-200",
        icon: Footprints,
      },
      [ScheduleItemType.EVENT]: {
        bg: "bg-red-50",
        border: "border-red-200",
        icon: Ticket,
      },
      [ScheduleItemType.MUSEUM_GALLERY]: {
        bg: "bg-red-50",
        border: "border-red-200",
        icon: Landmark,
      },
      [ScheduleItemType.STREETS]: {
        bg: "bg-red-50",
        border: "border-red-200",
        icon: Footprints,
      },
      [ScheduleItemType.HISTORICAL_SITE]: {
        bg: "bg-red-50",
        border: "border-red-200",
        icon: Landmark,
      },
      [ScheduleItemType.MEAL]: {
        bg: "bg-yellow-50",
        border: "border-yellow-200",
        icon: Utensils,
      },
      [ScheduleItemType.OTHER]: {
        bg: "bg-gray-50",
        border: "border-gray-200",
        icon: Heart,
      },
    };
    return styles[type] || styles[ScheduleItemType.OTHER];
  };

  return (
    <div>
      {/* Schedule Timeline */}
      <div className="relative border-l-2 border-gray-200 ml-3 mr-2 pt-3 mb-[70px] z-9">
        <AnimatePresence mode="wait">
          {currentDateSchedules.length === 0 ? (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="ml-6 py-8 text-gray-500 flex flex-col items-center"
            >
              <Calendar className="h-12 w-12 text-gray-400 mb-2" />
              <p>No schedules for this date</p>
            </motion.div>
          ) : (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
            >
              {currentDateSchedules.map((schedule, index) => {
                const styling = getScheduleStyling(schedule.activity_type);
                const Icon = styling.icon;

                return (
                  <motion.div
                    key={schedule.id + Math.random()}
                    className="mb-8 ml-4"
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: index * 0.1 }}
                  >
                    {/* Time Indicator */}
                    <div className="flex items-center group">
                      <div className="absolute -left-2 mt-1.5">
                        <div className="h-4 w-4 rounded-full bg-white border-2 border-gray-300 group-hover:border-gray-400 transition-colors duration-200" />
                      </div>
                      <time className="mb-1 text-sm font-medium text-gray-600 flex items-center">
                        <Clock className="h-4 w-4 mr-1" />
                        {formatTime(new Date(schedule.time.start_time))}
                        {schedule.time.end_time && (
                          <>
                            <span className="mx-2">-</span>
                            {formatTime(new Date(schedule.time.end_time))}
                          </>
                        )}
                      </time>
                    </div>

                    {/* Schedule Card */}
                    <div
                      className={`p-6 rounded-lg ${styling.bg} border ${styling.border} mt-2 transition-all duration-200 hover:shadow-md`}
                      role="article"
                      aria-label={`Schedule: ${schedule.title}`}
                    >
                      <div className="flex flex-col gap-2">
                        <div className="flex items-center justify-between gap-3">
                          <h3 className="text-md sm:text-lg font-semibold text-gray-900">
                            {schedule.title}
                          </h3>
                          <Icon className="h-6 w-6" />
                        </div>
                        <a
                          href={
                            schedule.location.includes(" to ")
                              ? `https://www.google.com/maps/dir/?api=1&origin=${encodeURIComponent(
                                  schedule.location.split(" to ")[0]
                                )}&destination=${encodeURIComponent(
                                  schedule.location.split(" to ")[1]
                                )}`
                              : `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(
                                  schedule.location
                                )}`
                          }
                          target="_blank"
                          rel="noopener noreferrer"
                          className="flex items-center justify-start mb-3 hover:underline hover:text-blue-800 transition-colors"
                        >
                          <img
                            src="/Google Maps Icon 2020.svg"
                            alt="Google Maps"
                            className="h-4 w-4 mr-2 flex-shrink-0"
                          />
                          <p className="text-[12px] sm:text-sm b-0 p-0">
                            {schedule.location}
                          </p>
                        </a>
                        {schedule.description && (
                          <p className="text-xs sm:text-sm text-gray-700 mb-0 sm:mb-2 leading-relaxed">
                            {schedule.description}
                          </p>
                        )}
                        {schedule.suggestion && (
                          <p className="text-xs sm:text-sm text-gray-600 mb-0leading-relaxed">
                            {schedule.suggestion}
                          </p>
                        )}
                      </div>
                    </div>
                  </motion.div>
                );
              })}
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Date Navigation */}
      <div className="py-2 bg-white w-full max-w-3xl mx-auto fixed bottom-0 shadow-[0_-10px_20px_-1px_rgba(0,0,0,0.05)] rounded-xl z-[999]">
        <motion.div
          className="flex items-center justify-between"
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3 }}
        >
          <div className="flex gap-4">
            <Button
              onClick={() => setIsEditMode((prev) => !prev)}
              size="lg"
              className="absolute bottom-3 left-3 rounded-full w-8 h-8 shadow-sm hover:bg-primary hover:text-primary-foreground hover:shadow-xl transition-shadow duration-200 flex items-center justify-center p-0 bg-white text-secondary-foreground border"
              title="Toggle Edit Mode"
            >
              <Edit className="h-4 w-4" />
            </Button>
            <Button
              onClick={() => {
                if (
                  window.confirm(
                    "Are you sure you want to regenerate a new schedule?"
                  )
                ) {
                  startGeneration();
                }
              }}
              variant={"outline"}
              className="absolute bottom-3 left-14 text-xs h-8 py-0 px-2"
              title="Regenerate Schedule"
            >
              Regenerate
            </Button>
          </div>
          <div className="flex items-center justify-end space-x-4">
            <button
              onClick={handlePreviousDay}
              className={`p-2 rounded-full transition-all duration-200 ${
                !isPreviousDisabled
                  ? "hover:bg-gray-100 hover:scale-105 active:scale-95"
                  : "opacity-20 cursor-not-allowed"
              }`}
              aria-label="Previous day"
              disabled={isPreviousDisabled}
            >
              <ChevronLeft className="h-6 w-6" />
            </button>
            <h2 className="text-sm sm:text-xl font-bold text-gray-900">
              {currentDate.toLocaleDateString("en-US", {
                weekday: "short",
                month: "short",
                day: "numeric",
              })}
            </h2>
            <button
              onClick={handleNextDay}
              className={`p-2 rounded-full transition-all duration-200 ${
                !isNextDisabled
                  ? "hover:bg-gray-100 hover:scale-105 active:scale-95"
                  : "opacity-20 cursor-not-allowed"
              }`}
              aria-label="Next day"
              disabled={isNextDisabled}
            >
              <ChevronRight className="h-6 w-6" />
            </button>
          </div>
        </motion.div>
      </div>
    </div>
  );
}
