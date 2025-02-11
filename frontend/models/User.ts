import { ScheduleItem, ScheduleItemType, ScheduleItemTime } from "./Schedule";

export interface User {
  id: string;
  googleId: string;
  user_name: string;
  user_interests: string;
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
  trip_accommodation_location: string;

  trip_budget: string;
  trip_theme: string;
  trip_fixed_schedules: ScheduleItem[];
}

