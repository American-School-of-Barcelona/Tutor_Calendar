# Booking System Business Rules

## Lesson Duration Rules
- **Minimum duration**: 2 hours (120 minutes)
- **Maximum duration**: 4 hours (240 minutes) - configurable
- **Duration increments**: 1 hour (60 minutes) steps
- Students can only book in 1-hour increments beyond the 2-hour minimum

## Pricing Rules
- **Base price**: 100€ for 2 hours
- **Additional cost**: 50€ per extra hour
- **Examples**:
  - 2 hours = 100€
  - 3 hours = 150€
  - 4 hours = 200€

## Booking Time Rules
- Bookings can only be made for **future time slots**
- Past time slots are automatically disabled and unclickable
- System uses live clock to determine past slots (updates every 60 seconds)

## Availability Rules
- Bookings must fall within tutor's availability blocks
- If tutor has no availability set, they are considered available all day (default)
- Bookings cannot overlap with:
  - Other **accepted** bookings
  - Tutor's unavailable time blocks (set by admin)

## Booking Status Flow
1. **pending**: Student submits booking request → waiting for admin approval
2. **accepted**: Admin approves → booking is confirmed, slot becomes unavailable
3. **denied**: Admin rejects → booking is cancelled, slot remains available
4. **cancelled**: Student cancels a pending booking → slot becomes available again

## Conflict Resolution
- If multiple pending bookings conflict for the same time slot:
  - Admin can only approve one
  - Other conflicting pending bookings should be automatically denied (or kept pending with warning)
  - System prevents double-booking of accepted slots

## Calendar Display Rules
- **15-minute time segments**: Calendar displays slots in 15-minute increments
- **Time range**: 8:00 AM to 10:00 PM (configurable)
- **Color coding**:
  - Available slots: Pastel green
  - Pending bookings: Pastel yellow
  - Accepted bookings: Pastel red/orange
  - Unavailable slots: Light gray
  - Past slots: Dimmed gray (unclickable)