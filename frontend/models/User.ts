import mongoose from "mongoose";

export interface User {
  id: string;
  googleId: string;
  user_name: string;
  user_interests: string[];
  user_extra_info: string;
  trip_transportation_schedule: string[];
  trip_location: string;
  trip_duration: string;
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
  trip_transportation_schedule: {
    type: [String],
    default: [],
  },
  trip_location: {
    type: String,
    default: "",
  },
  trip_duration: {
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
