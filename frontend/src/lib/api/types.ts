// Tipe response backend. Kontrak lengkap: integration-docs/*.md

export type TripStatus = "published" | "ongoing" | "completed" | "cancelled";
export type RideRequestStatus = "pending" | "accepted" | "rejected";
export type RatingRoleContext = "driver_to_passenger" | "passenger_to_driver";

export type LatLng = { lat: number; lng: number };

export type Trip = {
  trip_id: string;
  driver_id: string;
  vehicle_id: string;
  origin: LatLng;
  destination: LatLng;
  departure_time: string;
  available_seats: number;
  status: TripStatus;
  estimated_total_cost: number;
  cost_per_seat: number;
};

export type DriverInfo = {
  user_id: string;
  name: string;
  profile_photo: string | null;
  avg_rating_driver: number;
  total_ratings_driver: number;
};

export type VehicleInfo = {
  vehicle_id: string;
  type: string;
  brand: string;
  model: string;
  plate_number: string;
  capacity: number;
};

export type TripDetail = Trip & { driver: DriverInfo; vehicle: VehicleInfo };

export type JoinedTrip = Trip & { member_status: "active" | "cancelled" };

export type RecommendedTrip = {
  trip: Trip;
  origin_distance_km: number;
  destination_distance_km: number;
  time_diff_minutes: number;
  score: number;
};

export type TripMember = {
  user_id: string;
  name: string;
  profile_photo: string | null;
  role: "driver" | "passenger";
  trip_member_id: string | null;
  status: string;
};

export type RideRequest = {
  request_id: string;
  trip_id: string;
  requester_id: string;
  pickup: string;
  status: RideRequestStatus;
  created_at: string;
};

export type RideRequestWithRequester = RideRequest & {
  requester: {
    user_id: string;
    name: string;
    profile_photo: string | null;
    avg_rating: number;
    total_ratings: number;
  };
};

export type Message = {
  message_id: string;
  trip_id: string;
  sender_id: string;
  sender_name: string;
  content: string;
  sent_at: string;
};

export type Rating = {
  rating_id: string;
  trip_id: string;
  rater_id: string;
  rated_user_id: string;
  role_context: RatingRoleContext;
  score: number;
};
