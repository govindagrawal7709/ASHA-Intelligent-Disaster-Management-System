from django.contrib.auth.models import User
from django.db.models import Count, Q, Case, When, IntegerField
from math import radians, sin, cos, sqrt, atan2

ACTIVE_STATUSES = ['Assigned', 'En Route']

# Simple haversine distance in kilometers
def calculate_distance(lat1, lon1, lat2, lon2):
    if None in (lat1, lon1, lat2, lon2):
        return None
    R = 6371.0  # Earth radius in km
    dlat = radians(float(lat2) - float(lat1))
    dlon = radians(float(lon2) - float(lon1))
    a = sin(dlat / 2)**2 + cos(radians(float(lat1))) * cos(radians(float(lat2))) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return R * c


def choose_best_volunteer(relief_request, max_active_tasks: int = 1) -> User | None:
    """
    Choose best volunteer considering:
      - volunteer role
      - fewest active tasks
      - skill relevance
      - geographic proximity
    """
    base_qs = (
        User.objects.filter(
            is_active=True,
            is_staff=True,
        )
        .select_related('profile')
        .annotate(
            is_volunteer_role=Case(
                When(profile__role='volunteer', then=0),
                default=1,
                output_field=IntegerField(),
            ),
            active_tasks=Count(
                'assigned_tasks',
                filter=Q(assigned_tasks__status__in=ACTIVE_STATUSES),
            ),
        )
        .order_by('is_volunteer_role', 'active_tasks', 'id')
    )

    if not base_qs.exists():
        return None

    # Compute skill relevance & distance
    candidates = []
    for volunteer in base_qs:
        profile = getattr(volunteer, "profile", None)
        if not profile:
            continue

        # --- Skill matching ---
        skills_text = (profile.skills_bio or "").lower()
        request_type = relief_request.request_type.lower()
        skill_match = request_type in skills_text  # simple relevance flag

        # --- Distance calculation ---
        distance = None
        if profile.latitude and profile.longitude:
            distance = calculate_distance(
                relief_request.latitude,
                relief_request.longitude,
                profile.latitude,
                profile.longitude,
            )

        # Weighting logic
        candidates.append({
            "volunteer": volunteer,
            "skill_match": skill_match,
            "distance": distance if distance is not None else 99999,  # fallback
            "active_tasks": volunteer.active_tasks,
            "is_volunteer_role": volunteer.is_volunteer_role,
        })

    # --- Ranking ---
    # Sort by: (skill_match desc, is_volunteer_role asc, active_tasks asc, distance asc)
    candidates.sort(
        key=lambda x: (
            not x["skill_match"],  # False < True so invert
            x["is_volunteer_role"],
            x["active_tasks"],
            x["distance"],
        )
    )

    for c in candidates:
        if c["active_tasks"] < max_active_tasks:
            return c["volunteer"]

    return candidates[0]["volunteer"] if candidates else None
