"""
Default configuration values for the ArtificialU system.
"""

from typing import Dict, List

# Database defaults
DEFAULT_DB_URL = "postgresql://postgres:postgres@localhost:5432/artificial_u_dev"

# Audio defaults (temporary path for processing)
DEFAULT_TEMP_AUDIO_PATH = "temp_audio"

# Export defaults
DEFAULT_TEXT_EXPORT_PATH = "lecture_texts"

# Content generation defaults
DEFAULT_CONTENT_BACKEND = "anthropic"
DEFAULT_OLLAMA_MODEL = "phi4-mini"

# Storage defaults (MinIO/S3)
DEFAULT_STORAGE_TYPE = "minio"  # "minio" or "s3"
DEFAULT_STORAGE_ENDPOINT_URL = "http://minio:9000"  # For MinIO in Docker network
DEFAULT_STORAGE_PUBLIC_URL = "http://localhost:9000"  # For public access URLs
DEFAULT_STORAGE_ACCESS_KEY = "minioadmin"
DEFAULT_STORAGE_SECRET_KEY = "minioadmin"
DEFAULT_STORAGE_REGION = "us-east-1"
DEFAULT_STORAGE_AUDIO_BUCKET = "artificial-u-audio"
DEFAULT_STORAGE_LECTURES_BUCKET = "artificial-u-lectures"
DEFAULT_STORAGE_IMAGES_BUCKET = "artificial-u-images"

# Professor defaults
PROFESSOR_TITLES = [
    "Professor",
    "Associate Professor",
    "Assistant Professor",
    "Adjunct Professor",
]

PROFESSOR_LAST_NAMES = [
    "Smith",
    "Johnson",
    "Williams",
    "Brown",
    "Jones",
    "Miller",
    "Davis",
    "Wilson",
    "Taylor",
    "Clark",
    "Lee",
    "Garcia",
    "Martinez",
    "Rodriguez",
    "Lewis",
]

# Gender options
PROFESSOR_GENDERS = [
    "Male",
    "Female",
    "Non-binary",
]

# Accent options
PROFESSOR_ACCENTS = [
    "American (Neutral)",
    "American (Southern)",
    "American (Midwestern)",
    "American (New York)",
    "British (RP)",
    "British (Cockney)",
    "Scottish",
    "Irish",
    "Australian",
    "Indian",
    "French",
    "German",
    "Italian",
    "Russian",
    "Spanish",
    "Japanese",
    "Chinese",
    "Korean",
    "South African",
    "Nigerian",
    "Brazilian",
]

# Age range options
PROFESSOR_AGE_RANGES = [
    "30-40",
    "40-50",
    "50-60",
    "60-70",
    "70-80",
]

# Department and specialization defaults
DEPARTMENTS = [
    "Computer Science",
    "Physics",
    "Biology",
    "Mathematics",
    "History",
    "Psychology",
    "Chemistry",
    "Engineering",
    "Economics",
    "Philosophy",
]

DEPARTMENT_SPECIALIZATIONS: Dict[str, List[str]] = {
    "Computer Science": [
        "Machine Learning",
        "Software Engineering",
        "Cybersecurity",
        "Artificial Intelligence",
        "Data Science",
        "Computer Graphics",
    ],
    "Physics": [
        "Quantum Mechanics",
        "Astrophysics",
        "Particle Physics",
        "Theoretical Physics",
        "Nuclear Physics",
    ],
    "Biology": [
        "Molecular Biology",
        "Genetics",
        "Ecology",
        "Microbiology",
        "Evolutionary Biology",
    ],
    "Mathematics": [
        "Number Theory",
        "Applied Statistics",
        "Differential Equations",
        "Geometry",
        "Algebra",
    ],
    "History": [
        "Ancient Civilizations",
        "Modern History",
        "Political History",
        "Medieval History",
        "Cultural History",
    ],
    "Psychology": [
        "Cognitive Psychology",
        "Clinical Psychology",
        "Developmental Psychology",
        "Social Psychology",
        "Neuropsychology",
    ],
    "Chemistry": [
        "Organic Chemistry",
        "Inorganic Chemistry",
        "Physical Chemistry",
        "Biochemistry",
        "Analytical Chemistry",
    ],
    "Engineering": [
        "Mechanical Engineering",
        "Electrical Engineering",
        "Civil Engineering",
        "Chemical Engineering",
        "Aerospace Engineering",
    ],
    "Economics": [
        "Microeconomics",
        "Macroeconomics",
        "International Economics",
        "Behavioral Economics",
        "Econometrics",
    ],
    "Philosophy": [
        "Ethics",
        "Logic",
        "Metaphysics",
        "Epistemology",
        "Political Philosophy",
    ],
}

# Teaching style defaults
TEACHING_STYLES = [
    "Interactive",
    "Lecture-based",
    "Discussion-oriented",
    "Practical",
    "Research-focused",
    "Project-based",
    "Case study",
    "Flipped classroom",
]

# Personality defaults
PERSONALITIES = [
    "Enthusiastic",
    "Methodical",
    "Inspiring",
    "Analytical",
    "Patient",
    "Innovative",
    "Strict",
    "Supportive",
    "Intellectual",
    "Approachable",
]

# Course defaults
DEFAULT_COURSE_LEVEL = "Undergraduate"
DEFAULT_COURSE_WEEKS = 14
DEFAULT_LECTURES_PER_WEEK = 2
DEFAULT_LECTURE_WORD_COUNT = 2000

# Logging defaults
DEFAULT_LOG_LEVEL = "INFO"
