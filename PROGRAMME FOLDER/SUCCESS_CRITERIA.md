# Hotel Management System - Success Criteria

## 1. Authentication & Authorization

### 1.1 User Registration
**Success Criteria:**
- ✓ User cannot register with an existing email address (database constraint enforced)
- ✓ Password must be hashed before storing in database (using Werkzeug security)
- ✓ Username is auto-generated from email prefix and must be unique
- ✓ User must select a valid role during registration (validated against roles table)
- ✓ New users are set to active status by default (`is_active=True`)

### 1.2 User Login
**Success Criteria:**
- ✓ User cannot login with incorrect email/password combination
- ✓ Inactive users (`is_active=False`) cannot login even with correct credentials
- ✓ Successful login updates `last_login` timestamp in database
- ✓ User session persists based on "Remember Me" checkbox state
- ✓ Logged-in users are redirected away from login page

### 1.3 Role-Based Access Control
**Success Criteria:**
- ✓ HR Manager role can only access `/dashboard/hr` route
- ✓ General Manager role can only access `/dashboard/manager` route
- ✓ Front Desk Agent role can only access `/dashboard/frontdesk` route
- ✓ Unauthorized role access redirects to appropriate dashboard
- ✓ Each route validates user role before rendering page

## 2. HR Management Module

### 2.1 Staff Management (HR Manager Only)
**Success Criteria:**
- ✓ Only HR Manager role can add, edit, or delete staff members
- ✓ Cannot create staff with duplicate email address (database constraint)
- ✓ Username is auto-generated from email and ensured to be unique
- ✓ Password is hashed before storing in database
- ✓ Cannot delete own user account (`user_id != current_user.id` validation)
- ✓ Can change staff role assignments (updates `role_id` in database)
- ✓ Can activate/deactivate users (updates `is_active` field)
- ✓ All database operations are wrapped in try-catch with rollback on error

### 2.2 Staff Data Validation
**Success Criteria:**
- ✓ Email format must be valid
- ✓ All required fields (first_name, last_name, email, phone, password) must be provided
- ✓ Role must be selected from existing roles in database
- ✓ Changes to staff records are immediately reflected in database

## 3. Manager Duty Management Module

### 3.1 Duty Status Management (General Manager Only)
**Success Criteria:**
- ✓ Only General Manager can toggle duty status of Front Desk Agents
- ✓ Duty status toggles `is_on_duty` boolean field in database
- ✓ Duty status change is immediately reflected across all sessions
- ✓ Front Desk Agents can view but not change their own duty status

### 3.2 Shift Schedule Management (General Manager Only)
**Success Criteria:**
- ✓ Only General Manager can assign, view, and delete shifts
- ✓ Schedule records include date, start time, end time, and assigned_by reference
- ✓ Shift deletion removes record from database
- ✓ Schedules are stored with proper date/time data types
- ✓ `assigned_by` field tracks which manager created the schedule

### 3.3 Duty-Based Access Control
**Success Criteria:**
- ✓ Front Desk Agents cannot check-in guests when `is_on_duty=False`
- ✓ Front Desk Agents cannot check-out guests when `is_on_duty=False`
- ✓ Front Desk Agents cannot edit reservations when `is_on_duty=False`
- ✓ Front Desk Agents cannot cancel reservations when `is_on_duty=False`
- ✓ Front Desk Agents cannot add guests when `is_on_duty=False`
- ✓ Front Desk Agents cannot edit guests when `is_on_duty=False`
- ✓ Front Desk Agents cannot add guest notes when `is_on_duty=False`
- ✓ Manager and HR roles bypass duty status checks (`can_edit()` always returns True)

## 4. Guest Management Module

### 4.1 Guest Creation & Editing
**Success Criteria:**
- ✓ Cannot create guest with duplicate email (database unique constraint)
- ✓ Guest records store ID proof type and number
- ✓ Guest creation timestamp (`created_at`) is automatically set
- ✓ Email is optional for walk-in guests (nullable field)
- ✓ Phone number is mandatory (nullable=False constraint)
- ✓ Changes require user to be on duty (if Front Desk Agent)

### 4.2 Guest Statistics Tracking
**Success Criteria:**
- ✓ `total_stays` increments on checkout
- ✓ `total_spent` accumulates reservation amounts on checkout
- ✓ `last_visit` updates to checkout date on checkout
- ✓ Statistics are updated atomically during checkout transaction

### 4.3 Guest Notes with Approval Workflow
**Success Criteria:**
- ✓ Notes created by Front Desk Agents require approval (`is_approved=False`)
- ✓ Notes created by General Managers are auto-approved (`is_approved=True`)
- ✓ Auto-approved notes have `approved_by` and `approval_date` set immediately
- ✓ `created_by` field tracks which user created the note
- ✓ Notes are associated with guest via `guest_id` foreign key
- ✓ Cannot add notes when off duty (Front Desk Agents)

## 5. Reservation Management Module

### 5.1 Reservation Lifecycle
**Success Criteria:**
- ✓ New reservations start with status='confirmed'
- ✓ Check-in changes status to 'checked_in' and sets `actual_check_in` timestamp
- ✓ Cannot check-in a reservation that is not in 'confirmed' status
- ✓ Check-out changes status to 'checked_out' and sets `actual_check_out` timestamp
- ✓ Cannot check-out a reservation that is not in 'checked_in' status
- ✓ Cancellation changes status to 'cancelled'
- ✓ Cannot cancel reservations with status='checked_out'
- ✓ Cannot edit reservations with status='checked_out' or 'cancelled'

### 5.2 Room Availability Validation
**Success Criteria:**
- ✓ Cannot book same room for overlapping date ranges
- ✓ Availability check excludes current reservation when editing
- ✓ Check validates: check_in <= existing check_in < check_out
- ✓ Check validates: check_in < existing check_out <= check_out
- ✓ Check validates: check_in >= existing check_in AND check_out <= existing check_out
- ✓ Only considers reservations with status 'confirmed' or 'checked_in' in availability check

### 5.3 Reservation Pricing Calculation
**Success Criteria:**
- ✓ Total amount = base_price × number_of_nights
- ✓ Number of nights = (check_out_date - check_in_date).days
- ✓ Total recalculates when dates are edited
- ✓ `room_rate` stores the base price at time of booking
- ✓ `total_amount` stores final calculated price

### 5.4 Public Guest Booking
**Success Criteria:**
- ✓ Guests can book without login (public route)
- ✓ Existing guest is found by email if provided
- ✓ New guest record created if email doesn't exist
- ✓ System finds first available room in selected category
- ✓ Booking fails if no rooms available for selected dates
- ✓ Unique `reservation_code` generated for each booking (10 characters)
- ✓ Transaction commits only if all operations succeed

### 5.5 Duty-Based Reservation Actions
**Success Criteria:**
- ✓ All reservation actions (check-in, check-out, edit, cancel) validate duty status
- ✓ Front Desk Agents must have `is_on_duty=True` to perform actions
- ✓ Database changes are rejected if duty status check fails
- ✓ User is redirected with error message if not on duty

## 6. Room Management Module

### 6.1 Room Status Tracking
**Success Criteria:**
- ✓ Room is 'occupied' if has reservation with status='checked_in' for today
- ✓ Room is 'arriving' if has reservation with check_in_date=today and status='confirmed'
- ✓ Room is 'departing' if has reservation with check_out_date=today and status='checked_in'
- ✓ Room is 'available' if none of above conditions match
- ✓ Status calculation considers only current date, not historical data

### 6.2 Room Category Configuration
**Success Criteria:**
- ✓ Each room belongs to exactly one category (`category_id` foreign key)
- ✓ Categories define max_adults and max_children constraints
- ✓ Categories define base_price used for calculations
- ✓ Room number must be unique (database constraint)

## 7. Reports Module

### 7.1 Occupancy Report
**Success Criteria:**
- ✓ Total rooms count includes all rooms in database
- ✓ Occupied count = reservations where check_in <= selected_date < check_out AND status IN ('confirmed', 'checked_in')
- ✓ Occupancy percentage = (occupied / total) × 100
- ✓ Category breakdown groups by room category
- ✓ Breakdown shows total rooms and occupied rooms per category

### 7.2 Revenue Report
**Success Criteria:**
- ✓ Revenue includes only reservations with status IN ('checked_in', 'checked_out')
- ✓ Revenue filtered by check_in_date within date range
- ✓ ADR (Average Daily Rate) = total_revenue / total_bookings
- ✓ RevPAR = total_revenue / (total_rooms × days_in_period)
- ✓ Category revenue aggregates by room category
- ✓ Date range is inclusive of start and end dates

### 7.3 Arrivals/Departures Report
**Success Criteria:**
- ✓ Arrivals show reservations with check_in_date = selected_date
- ✓ Departures show reservations with check_out_date = selected_date
- ✓ Only includes reservations with status IN ('confirmed', 'checked_in')
- ✓ Reports join guest and room data for complete information

### 7.4 Report Access Control
**Success Criteria:**
- ✓ Reports accessible by General Manager role
- ✓ Reports accessible by Front Desk Agent role
- ✓ Reports not accessible by HR Manager role
- ✓ Unauthorized access redirects to appropriate dashboard

## 8. Data Integrity & Database Constraints

### 8.1 Unique Constraints
**Success Criteria:**
- ✓ User.username must be unique (database constraint)
- ✓ User.email must be unique (database constraint)
- ✓ Guest.email must be unique if provided (database constraint)
- ✓ Room.room_number must be unique (database constraint)
- ✓ Reservation.reservation_code must be unique (database constraint)
- ✓ Role.name must be unique (database constraint)

### 8.2 Foreign Key Relationships
**Success Criteria:**
- ✓ User.role_id references valid Role.id
- ✓ Reservation.guest_id references valid Guest.id
- ✓ Reservation.room_id references valid Room.id
- ✓ Room.category_id references valid RoomCategory.id
- ✓ GuestNote.guest_id references valid Guest.id
- ✓ GuestNote.created_by references valid User.id
- ✓ Schedule.user_id references valid User.id
- ✓ Schedule.assigned_by references valid User.id

### 8.3 Nullable Field Validation
**Success Criteria:**
- ✓ User.username, email, password_hash, first_name, last_name, role_id are NOT NULL
- ✓ Guest.first_name, last_name, phone are NOT NULL
- ✓ Guest.email is NULLABLE (for walk-ins)
- ✓ Reservation.guest_id, room_id, check_in_date, check_out_date, room_rate, total_amount are NOT NULL
- ✓ All timestamps default to current UTC time when not provided

### 8.4 Transaction Safety
**Success Criteria:**
- ✓ All multi-step operations use database transactions
- ✓ Errors trigger rollback to prevent partial updates
- ✓ Database commit only occurs if all validations pass
- ✓ Error messages are shown to user on transaction failure

## 9. Security & Password Management

### 9.1 Password Handling
**Success Criteria:**
- ✓ Passwords are never stored in plain text
- ✓ Passwords are hashed using Werkzeug's generate_password_hash
- ✓ Password verification uses check_password_hash (constant-time comparison)
- ✓ Password hash length supports 255 characters

### 9.2 Session Management
**Success Criteria:**
- ✓ Unauthenticated users redirected to login page with next parameter
- ✓ Login required decorator protects all dashboard routes
- ✓ User session invalidated on logout
- ✓ Session persists across requests when "Remember Me" is checked

## 10. Business Logic Validation

### 10.1 Reservation Business Rules
**Success Criteria:**
- ✓ Check-out date must be after check-in date
- ✓ Number of guests must not exceed room category limits
- ✓ Cannot modify completed reservations
- ✓ Cannot check-in before check-in date
- ✓ Guest statistics only update on successful checkout

### 10.2 Staff Management Business Rules
**Success Criteria:**
- ✓ Cannot delete own user account
- ✓ Inactive users cannot login
- ✓ Front Desk Agents can only edit when on duty
- ✓ Managers and HR bypass duty restrictions

### 10.3 Database Initialization
**Success Criteria:**
- ✓ Roles are created on first run if none exist
- ✓ Default admin user created if no users exist
- ✓ Room categories created if none exist
- ✓ Sample rooms created if none exist
- ✓ Initialization is idempotent (safe to run multiple times)
