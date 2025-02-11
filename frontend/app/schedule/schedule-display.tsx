import { useState } from "react";
import {
  ScheduleItem,
  ScheduleItemType,
  ScheduleItemTime,
} from "@/models/Schedule";
import {
  ChevronLeft,
  ChevronRight,
  MapPin,
  Clock,
  Plane,
  Bus,
  Footprints,
  Calendar,
  Building,
  Route,
  Landmark,
  UtensilsCrossed,
  HelpCircle,
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

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
        icon: Calendar,
      },
      [ScheduleItemType.MUSEUM_GALLERY]: {
        bg: "bg-red-50",
        border: "border-red-200",
        icon: Building,
      },
      [ScheduleItemType.STREETS]: {
        bg: "bg-red-50",
        border: "border-red-200",
        icon: Route,
      },
      [ScheduleItemType.HISTORICAL_SITE]: {
        bg: "bg-red-50",
        border: "border-red-200",
        icon: Landmark,
      },
      [ScheduleItemType.MEAL]: {
        bg: "bg-yellow-50",
        border: "border-yellow-200",
        icon: UtensilsCrossed,
      },
      [ScheduleItemType.OTHER]: {
        bg: "bg-gray-50",
        border: "border-gray-200",
        icon: HelpCircle,
      },
    };
    return styles[type] || styles[ScheduleItemType.OTHER];
  };

  return (
    <div className="max-w-4xl mx-auto px-4">
      {/* Date Navigation */}
      <motion.div
        className="flex items-center justify-between mb-8 bg-white sticky top-0 py-4 z-10"
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
      >
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
        <h2 className="text-xl font-bold text-gray-900">
          {currentDate.toLocaleDateString("en-US", {
            weekday: "long",
            year: "numeric",
            month: "long",
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
      </motion.div>

      {/* Schedule Timeline */}
      <div className="relative border-l-2 border-gray-200 ml-2">
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
                const styling = getScheduleStyling(schedule.type);
                const Icon = styling.icon;

                return (
                  <motion.div
                    key={schedule.id}
                    className="mb-8 ml-6"
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
                      <div className="flex items-start gap-4">
                        <div className="p-2 rounded-full bg-white/50">
                          <Icon className="h-6 w-6" />
                        </div>
                        <div className="flex-1">
                          <h3 className="text-lg font-semibold text-gray-900 mb-2">
                            {schedule.title}
                          </h3>
                          <div className="flex items-center mb-3 text-gray-600">
                            <MapPin className="h-4 w-4 mr-1 flex-shrink-0" />
                            <p className="text-sm">{schedule.location}</p>
                          </div>
                          {schedule.description && (
                            <p className="text-sm text-gray-700 mb-2 leading-relaxed">
                              {schedule.description}
                            </p>
                          )}
                          {schedule.suggestion && (
                            <p className="text-sm text-gray-600 leading-relaxed">
                              {schedule.suggestion}
                            </p>
                          )}
                        </div>
                      </div>
                    </div>
                  </motion.div>
                );
              })}
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}
