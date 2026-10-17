"""Domain constants shared by models, services and routes."""

ROLE_USER = 'user'
ROLE_ADMIN = 'admin'

TYPE_EQUIPMENT = 'Equipment'
TYPE_PROFESSIONAL = 'Professional'

STATUS_PENDING = 'Pending'
STATUS_APPROVED = 'Approved'
STATUS_REJECTED = 'Rejected'
STATUS_CANCELLED = 'Cancelled'
STATUS_BORROWED = 'Borrowed'
STATUS_RETURNED = 'Returned'

# Statuses that block the dates of a resource (compare in lower case).
BLOCKING_STATUSES = ('pending', 'approved', 'booked', 'borrowed')
