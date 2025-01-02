import React from 'react';

function CalendarPage() {
  // FullCalendar or react-big-calendar etc. can be integrated
  // for MVP, just a placeholder:
  return (
    <div className="container mt-4">
      <h2>배당 캘린더</h2>
      <div className="alert alert-info">
        달력이 표시될 영역 (FullCalendar component 등)
      </div>
    </div>
  );
}

export default CalendarPage;