export enum ScheduleItemType {
  TERMINAL = "terminal",
  TRANSPORT = "transport",
  WALK = "walk",
  EVENT = "event",
  MUSEUM_GALLERY = "museum_gallery",
  STREETS = "streets",
  HISTORICAL_SITE = "historical_site",
  MEAL = "meal",
  OTHER = "other",
}

export interface ScheduleItemTime {
  start_time: Date;
  end_time: Date | null;
}

export interface ScheduleItem {
  id: number;
  type: ScheduleItemType;
  time: ScheduleItemTime;
  location: string;
  title: string;
  description: string | null;
  suggestion: string | null;
}
