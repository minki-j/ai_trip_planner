export function Spinner() {
  return (
    <div className="animate-[pulse_2s_ease-in-out_infinite] space-y-3">
      <div className="h-4 bg-gray-500 hover:bg-gray-700 rounded w-3/4"></div>
      <div className="h-4 bg-gray-500 hover:bg-gray-700 rounded"></div>
      <div className="h-4 bg-gray-500 hover:bg-gray-700 rounded w-5/6"></div>
    </div>
  );
}
