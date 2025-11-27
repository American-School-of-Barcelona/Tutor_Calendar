# Development Plan: Tutomatics Calendar Booking System

## Project Overview

**Purpose:**
1. Beginning of year: Slot booking system where multiple students compete for the same time slots
2. Throughout the year: Regular booking system where tutors manage availability and students book lessons

**Technology Stack:**
- Backend: Flask (Python)
- Database: SQLite
- Frontend: HTML, CSS, JavaScript
- Authentication: Session-based with password hashing

---

## Phase 1: Foundation & Setup
Goal: Set up the base structure, database, and authentication framework.

### Section 1.1: Project Structure & SQLite Database Setup
- Install Flask-SQLAlchemy and Flask-Migrate
- Create SQLite database
- Set up database connection in Flask
- Create database models (User, Booking, Availability, Notification)
- Create database initialization script
- Test database connection

### Section 1.2: Basic Authentication System
- Install bcrypt for password hashing
- User model with roles (admin/student)
- Password hashing functions
- Login/logout routes
- Session management
- Basic login page (HTML only)

### Section 1.3: Styling - Login Page (Tutomatics Theme)
- Light beige/off-white background
- Dark gray text
- Rounded navigation-style buttons
- Clean, minimalist design
- Basic animations/transitions

---

## Phase 2: Admin Features
Goal: Build all admin functionality.

### Section 2.1: Admin Login & Dashboard
- Admin login route
- Admin dashboard page
- Route protection (admin-only)
- Basic navigation structure

### Section 2.2: Styling - Admin Dashboard (Tutomatics Theme)
- Dashboard layout with light beige background
- Navigation tabs (light beige, dark gray text, rounded)
- Consistent Tutomatics theme
- Admin theme colors

### Section 2.3: User Approval System
- Student registration route
- Pending users queue page
- Approve/deny functionality
- Update user status in database
- Display pending registrations

### Section 2.4: Styling - User Approval Page (Tutomatics Theme)
- Queue list design
- Approve/deny button styling (rounded, theme colors)
- Status indicators
- Consistent with overall theme

### Section 2.5: Admin Calendar - Availability Management
- Calendar view for admin
- Mark times as unavailable
- Repeat options (daily/weekly/until date/forever)
- Save availability to database
- Display unavailable times on calendar

### Section 2.6: Styling - Admin Calendar (Tutomatics Theme)
- Calendar grid styling
- Unavailable time highlighting
- Repeat option UI (rounded buttons, theme colors)
- Selection effects
- Light beige background, dark gray text

### Section 2.7: Booking Request Management
- Display pending student booking requests
- Accept/deny booking requests
- Update booking status
- Show accepted bookings on calendar
- Notification system (basic)

### Section 2.8: Styling - Request Management Page (Tutomatics Theme)
- Request list design
- Accept/deny buttons (theme styling)
- Status badges
- Consistent navigation

---

## Phase 3: Student Features
Goal: Build all student functionality.

### Section 3.1: Student Registration & Login
- Student signup route
- Email field validation
- Store pending registrations (awaiting admin approval)
- Student login route
- Basic signup/login pages
- Placeholder for email verification (structure ready, implementation later)

### Section 3.2: Styling - Student Login/Signup (Tutomatics Theme)
- Signup form design (light beige background)
- Login form design
- Form validation styling
- Success/error messages
- Rounded buttons, dark gray text

### Section 3.3: Student Calendar View
- Display available time slots
- Show admin-marked unavailable times
- Show already booked slots
- Click to book functionality
- Submit booking request to admin
- Visual distinction between available/unavailable/booked

### Section 3.4: Styling - Student Calendar (Tutomatics Theme)
- Calendar grid styling
- Available/unavailable/booked color coding
- Booking selection effects
- Hover states
- Theme-consistent design

### Section 3.5: Past Lessons Tab
- Query user's past bookings
- Display lesson history
- Filter/sort options (date, status)
- Basic lesson details

### Section 3.6: Styling - Past Lessons Page (Tutomatics Theme)
- Lesson history list/card design
- Date formatting
- Status indicators
- Consistent navigation and theme

---

## Phase 4: Integration & Polish
Goal: Connect all pieces and refine the experience.

### Section 4.1: Calendar Integration
- Sync admin availability with student view
- Show accepted bookings on both calendars
- Real-time updates (or refresh mechanism)
- Ensure data consistency

### Section 4.2: Notification System (Basic)
- Store notifications in database
- Display notification count
- Mark as read functionality
- Basic notification display
- (Email notifications - Phase 5 or later)

### Section 4.3: Final UI Polish (Tutomatics Theme)
- Consistent color scheme throughout (light beige, dark gray)
- Smooth transitions
- Responsive design basics
- Loading states
- Error handling UI
- Rounded buttons and navigation tabs everywhere
- Professional, clean aesthetic

---

## Phase 5: Beginning of Year Slot Booking (Future)
Goal: Add the competitive slot booking feature.

### Section 5.1: Slot Contest System
- Mark slots as "contested"
- Show contest count per slot
- Allow multiple pending requests per slot
- Admin selects winner
- Visual indicators for contested slots

### Section 5.2: Styling - Contest View (Tutomatics Theme)
- Visual indicators for contested slots
- Contest count display
- Special styling for high-contest slots
- Theme-consistent design

---

## Development Order

1. Phase 1: Foundation (database, authentication)
2. Phase 2: Admin features (dashboard, approvals, calendar, requests)
3. Phase 3: Student features (registration, calendar, lessons)
4. Phase 4: Integration & polish
5. Phase 5: Beginning of year feature (future)

---

## Notes

- Email verification: Placeholder structure ready, implementation later
- Database: SQLite (suitable for ~30 concurrent users)
- Design: Clean, minimalist, professional with Tutomatics branding
- Scalability: Structure allows for future enhancements