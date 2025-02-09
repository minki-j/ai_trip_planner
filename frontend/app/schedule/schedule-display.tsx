import { TimeSlot, ScheduleItem, ScheduleItemType } from "@/models/Schedule";
import { ChevronLeft, ChevronRight } from 'lucide-react';

interface ScheduleDisplayProps {
  activities: ScheduleItem[];
}

export default function ScheduleDisplay({ activities }: ScheduleDisplayProps) {
  // Helper function to format time
  const formatTime = (date: Date) => {
    return date.toLocaleTimeString('en-US', { 
      hour: '2-digit', 
      minute: '2-digit',
      hour12: true 
    });
  };

  // Helper function to get activity background color based on type
  const getActivityColor = (type: ScheduleItemType) => {
    const colors = {
      [ScheduleItemType.TERMINAL]: 'bg-blue-100',
      [ScheduleItemType.TRANSPORT]: 'bg-yellow-100',
      [ScheduleItemType.WALK]: 'bg-green-100',
      [ScheduleItemType.EVENT]: 'bg-purple-100',
      [ScheduleItemType.MUSEUM_GALLERY]: 'bg-pink-100',
      [ScheduleItemType.STREETS]: 'bg-orange-100',
      [ScheduleItemType.HISTORICAL_SITE]: 'bg-red-100',
      [ScheduleItemType.OTHER]: 'bg-gray-100',
      [ScheduleItemType.REMOVE]: 'bg-gray-100',
    };
    return colors[type] || 'bg-gray-100';
  };

  return (
    <div className="max-w-4xl mx-auto p-4">
      {/* Date Navigation */}
      <div className="flex items-center justify-between mb-6">
        <button className="p-2 rounded-full hover:bg-gray-100">
          <ChevronLeft className="h-6 w-6" />
        </button>
        <h2 className="text-xl font-semibold">
          {new Date().toLocaleDateString("en-US", {
            weekday: "long",
            year: "numeric",
            month: "long",
            day: "numeric",
          })}
        </h2>
        <button className="p-2 rounded-full hover:bg-gray-100">
          <ChevronRight className="h-6 w-6" />
        </button>
      </div>

      {/* Schedule Timeline */}
      <div className="relative border-l-2 border-gray-200 ml-4">
        {activities.map((activity) => (
          <div key={activity.id} className="mb-8 ml-6">
            {/* Time Indicator */}
            <div className="flex items-center">
              <div className="absolute -left-1.5 mt-1.5">
                <div className="h-3 w-3 rounded-full bg-gray-400" />
              </div>
              <time className="mb-1 text-sm font-normal leading-none text-gray-500">
                {formatTime(new Date(activity.time.start_time))} -{" "}
                {formatTime(new Date(activity.time.end_time))}
              </time>
            </div>

            {/* Activity Card */}
            <div
              className={`p-4 rounded-lg ${getActivityColor(
                activity.type
              )} mt-2`}
            >
              <h3 className="text-lg font-semibold text-gray-900 mb-1">
                {activity.title}
              </h3>
              <p className="mb-2 text-sm text-gray-600">{activity.location}</p>
              <p className="text-sm text-gray-700">{activity.description}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
