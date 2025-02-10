import mongoose from "mongoose";

export interface User {
  id: string;
  googleId: string;
  user_name: string;
  user_interests: string[];
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
  trip_fixed_schedules: string[];
}

const UserSchema = new mongoose.Schema<User>({
  googleId: {
    type: String,
    required: true,
    unique: true,
  },
  user_name: {
    type: String,
    required: true,
  },
  user_interests: {
    type: [String],
    default: [],
  },
  user_extra_info: {
    type: String,
    default: "",
  },
  trip_arrival_date: {
    type: String,
    default: "",
  },
  trip_arrival_time: {
    type: String,
    default: "",
  },
  trip_arrival_terminal: {
    type: String,
    default: "",
  },
  trip_departure_date: {
    type: String,
    default: "",
  },
  trip_departure_time: {
    type: String,
    default: "",
  },
  trip_departure_terminal: {
    type: String,
    default: "",
  },
  trip_location: {
    type: String,
    default: "",
  },
  trip_accommodation_location: {
    type: String,
    default: "",
  },
  trip_budget: {
    type: String,
    default: "",
  },
  trip_theme: {
    type: String,
    default: "",
  },
  trip_fixed_schedules: {
    type: [String],
    default: [],
  },
});

export default mongoose.models.User || mongoose.model("User", UserSchema);
