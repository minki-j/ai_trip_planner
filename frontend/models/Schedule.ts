export enum ScheduleItemType {
  TERMINAL = "terminal",
  TRANSPORT = "transport",
  WALK = "walk",
  EVENT = "event",
  MUSEUM_GALLERY = "museum_gallery",
  STREETS = "streets",
  HISTORICAL_SITE = "historical_site",
  REMOVE = "remove",
  OTHER = "other",
}

export interface TimeSlot {
  start_time: Date;
  end_time: Date;
}

export interface ScheduleItem {
  id: number;
  type: ScheduleItemType;
  time: TimeSlot;
  location: string;
  title: string;
  description: string;
}
