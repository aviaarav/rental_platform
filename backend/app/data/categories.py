"""Fixed option lists used by the listing forms."""

EQUIPMENT_CATEGORIES = [
    'Power Tools', 'Hand Tools', 'Ladders', 'Gardening', 'Construction',
    'Audio and Lighting', 'Camping and Travel', 'Kitchen and Catering',
    'Furniture and Event', 'Electronics', 'Vehicles and Cycles', 'Other',
]

SERVICE_CATEGORIES = [
    'Electrician', 'Plumber', 'Driver', 'Carpenter', 'Painter', 'Mechanic',
    'AC Technician', 'Mason', 'Gardener', 'Cook / Caterer', 'Photographer', 'Tutor', 'Other',
]

CONDITIONS = ['New', 'Good', 'Average']
PICKUP_METHODS = ["Owner's Home", 'Mutual Location', 'Delivery']
CHARGE_TYPES = ['Per Hour', 'Per Day']
AVAILABILITY_OPTIONS = ['Available', 'Unavailable']
# Booking request options
URGENCY_OPTIONS = ['Normal', 'Urgent', 'Emergency']
SERVICE_MODES = ['At My Location', "At Provider's Place", 'Online / Remote']

# Dropdowns on the booking request forms (free text is still accepted by the server)
EQUIPMENT_PURPOSES = ['Event / Function', 'Home repair work', 'Construction work', 'Agricultural work',
                      'Business use', 'Personal use', 'Other']
SERVICE_PURPOSES = ['Repair and maintenance', 'New installation', 'House wiring / Fan and light fitting',
                    'Inspection / Consultation', 'Emergency repair', 'Regular service', 'Other']
