# Spotify Recommender - Complete Project Breakdown

This document provides a comprehensive overview of everything created in this project, explaining what each component does and how they work together.

## 📁 Project Structure

```
spotify_recommender/
├── spotify_recommender/          # Django project root
│   ├── recommender/              # Main app directory
│   │   ├── models.py            # Database models (tables)
│   │   ├── views.py             # View functions (request handlers)
│   │   ├── urls.py              # URL routing configuration
│   │   ├── admin.py             # Django admin interface setup
│   │   ├── templates/           # HTML templates
│   │   │   └── recommender/
│   │   │       ├── base.html           # Base template (navbar, footer)
│   │   │       ├── home.html            # Landing page
│   │   │       ├── dashboard.html       # Main dashboard
│   │   │       ├── recommendations.html # Recommendations page
│   │   │       ├── listening_history.html # History page
│   │   │       └── error.html          # Error page
│   │   └── static/              # Static files (CSS, images)
│   │       └── css/
│   │           └── style.css    # All styling
│   ├── spotify_recommender/     # Project settings
│   │   ├── settings.py          # Django configuration
│   │   └── urls.py              # Main URL configuration
│   ├── requirements.txt         # Python dependencies
│   └── manage.py               # Django management script
└── README.md                   # Setup instructions
```

---

## 🗄️ Database Models (models.py)

### Purpose
Defines the database structure - what data we store and how it's organized.

### Models Created

#### 1. **SpotifyToken**
**Purpose**: Stores OAuth authentication tokens for each user.

**Why it exists**: 
- Spotify access tokens expire after 1 hour
- We need to store tokens to make API calls on behalf of users
- Refresh tokens allow us to get new access tokens automatically

**Key Fields**:
- `access_token`: Used to authenticate API calls
- `refresh_token`: Used to get new access tokens
- `expires_at`: When token expires (used to auto-refresh)

**Relationships**: One-to-one with Django User (one token per user)

---

#### 2. **SpotifyProfile**
**Purpose**: Stores user's Spotify profile information.

**Why it exists**:
- Avoids making API calls every time we need user's name/picture
- Stores profile data locally for quick access
- Displays user info on dashboard

**Key Fields**:
- `spotify_id`: Unique Spotify user ID
- `display_name`: User's Spotify name
- `profile_image_url`: Profile picture URL

**Relationships**: One-to-one with Django User

---

#### 3. **Track**
**Purpose**: Stores information about individual tracks (songs).

**Why it exists**:
- Multiple users can listen to the same track
- Prevents duplicate data (store track info once, reference it)
- Central repository of all tracks we've seen

**Key Fields**:
- `spotify_id`: Unique Spotify track ID
- `name`, `artist`, `album`: Basic track info
- `album_cover_url`: Image URL
- `preview_url`: 30-second preview audio
- `external_url`: Link to open in Spotify app

**Relationships**: Referenced by ListeningHistory and Recommendation

---

#### 4. **ListeningHistory**
**Purpose**: Stores individual listening events (when a user played a track).

**Why it exists**:
- Tracks user's listening patterns
- Used to analyze music taste
- Basis for generating recommendations

**Key Fields**:
- `user`: Which user played the track
- `track`: Which track was played
- `played_at`: When it was played (timestamp)

**Relationships**: Many-to-one with User, many-to-one with Track

**Special Features**:
- `unique_together`: Prevents duplicate entries (same user/track/time)
- `ordering`: Orders by most recent plays first

---

#### 5. **Recommendation**
**Purpose**: Stores generated music recommendations for users.

**Why it exists**:
- Saves recommendations so users can view them later
- Links users to tracks we think they'll like
- Stores confidence score and reason

**Key Fields**:
- `user`: Who the recommendation is for
- `track`: Track being recommended
- `score`: Confidence score (0.0 to 1.0)
- `reason`: Why we think they'll like it

**Relationships**: Many-to-one with User, many-to-one with Track

**Special Features**:
- `unique_together`: One recommendation per user/track pair
- `ordering`: Orders by highest score first

---

## 🎯 View Functions (views.py)

### Purpose
Handle HTTP requests and return responses. Each function corresponds to a URL route.

### Helper Functions

#### `get_spotify_oauth()`
**Purpose**: Creates SpotifyOAuth object for authentication.

**When it's used**: 
- When initiating login
- When exchanging authorization code for token
- When refreshing expired tokens

**Returns**: Configured SpotifyOAuth object

---

#### `get_user_spotify_client(user)`
**Purpose**: Gets authenticated Spotify API client for a user.

**When it's used**: 
- Before making any Spotify API calls
- Checks if token is expired and refreshes if needed

**Returns**: `spotipy.Spotify` client ready for API calls, or `None` if user not authenticated

**Key Logic**:
1. Gets stored token from database
2. Checks if expired (current time >= expiration time)
3. If expired, refreshes using refresh token
4. Returns authenticated client

---

### Public Views (No login required)

#### `home(request)`
**Purpose**: Landing page - first page users see.

**URL**: `/`

**What it does**:
- Displays welcome message
- Shows feature highlights
- Displays "Connect with Spotify" button

**Returns**: Rendered `home.html` template

---

#### `spotify_login(request)`
**Purpose**: Initiates Spotify OAuth login flow.

**URL**: `/login/`

**What it does**:
1. Creates OAuth object
2. Gets authorization URL from Spotify
3. Redirects user to Spotify login page

**Returns**: Redirect to Spotify authorization page

**Flow**: User clicks button → redirected to Spotify → authorizes → callback with code

---

#### `spotify_callback(request)`
**Purpose**: Handles callback from Spotify after user authorization.

**URL**: `/callback/`

**What it does** (CRITICAL FUNCTION):
1. Gets authorization code from URL parameters
2. Exchanges code for access token (calls Spotify API)
3. Gets user's profile from Spotify
4. Creates/updates Django User
5. Stores authentication tokens in `SpotifyToken`
6. Stores profile info in `SpotifyProfile`
7. Logs user into Django session
8. Redirects to dashboard

**Returns**: Redirect to dashboard on success, error page on failure

**Key Logic**:
- Uses `get_or_create()` to avoid duplicate users
- Uses `update_or_create()` to update tokens if user already exists
- Creates user with Spotify ID as username

---

### Protected Views (Login required)

#### `dashboard(request)`
**Purpose**: Main dashboard - shows profile and action buttons.

**URL**: `/dashboard/`

**Requires**: User must be logged in (`@login_required`)

**What it does**:
- Gets user's Spotify profile
- Displays profile info (name, picture)
- Shows buttons for:
  - Fetch listening history
  - Generate recommendations
  - View history
  - View recommendations

**Returns**: Rendered `dashboard.html` template

---

#### `fetch_listening_history(request)`
**Purpose**: Fetches user's recent listening history from Spotify and stores it.

**URL**: `/fetch-history/`

**Requires**: 
- User must be logged in
- Must be POST request (`@require_http_methods(["POST"])`)

**What it does**:
1. Gets authenticated Spotify client
2. Calls `current_user_recently_played()` API (last 50 tracks)
3. For each track:
   - Creates `Track` record if it doesn't exist
   - Creates `ListeningHistory` entry
4. Returns JSON response with counts

**Returns**: JSON response with success status and counts

**Called via**: AJAX from dashboard page (JavaScript fetch)

**Key Logic**:
- Uses `get_or_create()` to prevent duplicate tracks
- Parses timestamp from Spotify format
- Makes timestamp timezone-aware

---

#### `generate_recommendations(request)`
**Purpose**: Generates personalized music recommendations.

**URL**: `/generate-recommendations/`

**Requires**: User must be logged in

**What it does** (CORE RECOMMENDATION ALGORITHM):
1. Gets user's top tracks (most played, last 6 months)
2. Gets audio features for top 5 tracks (danceability, energy, valence, tempo)
3. Calculates average audio features (what type of music user likes)
4. Calls Spotify's recommendation API with:
   - Top tracks as "seed" (basis for recommendations)
   - Average features as "target" (match this style)
5. Clears old recommendations
6. Stores new recommendations in database
7. Redirects to recommendations page

**Returns**: Redirect to recommendations page

**Recommendation Algorithm**:
- Uses user's top tracks to identify their music taste
- Analyzes audio features to understand what they like
- Asks Spotify to find similar tracks with matching features
- Stores 20 recommendations with default score of 0.8

---

#### `recommendations_view(request)`
**Purpose**: Displays all recommendations for the user.

**URL**: `/recommendations/`

**Requires**: User must be logged in

**What it does**:
- Gets all recommendations for logged-in user
- Orders by score (highest first)
- Passes to template for display

**Returns**: Rendered `recommendations.html` template

**Optimization**: Uses `select_related('track')` to fetch track data in one query

---

#### `listening_history_view(request)`
**Purpose**: Displays user's listening history.

**URL**: `/history/`

**Requires**: User must be logged in

**What it does**:
- Gets last 100 listening history entries
- Orders by most recent first
- Passes to template for display

**Returns**: Rendered `listening_history.html` template

**Optimization**: Uses `select_related('track')` to fetch track data in one query

---

## 🔗 URL Routing (urls.py)

### Purpose
Maps URL paths to view functions. When user visits a URL, Django uses this to find which function to call.

### URL Patterns

| URL Path | View Function | Name | Purpose |
|----------|--------------|------|---------|
| `/` | `home` | `home` | Landing page |
| `/login/` | `spotify_login` | `spotify_login` | Start Spotify login |
| `/callback/` | `spotify_callback` | `spotify_callback` | Handle Spotify callback |
| `/dashboard/` | `dashboard` | `dashboard` | Main dashboard |
| `/fetch-history/` | `fetch_listening_history` | `fetch_history` | Fetch history (POST) |
| `/generate-recommendations/` | `generate_recommendations` | `generate_recommendations` | Generate recommendations |
| `/recommendations/` | `recommendations_view` | `recommendations` | View recommendations |
| `/history/` | `listening_history_view` | `listening_history` | View history |

### Namespacing
- `app_name = 'recommender'` creates a namespace
- URLs are referenced as `'recommender:dashboard'`, `'recommender:home'`, etc.
- Prevents conflicts with other apps

---

## 🎨 Templates (HTML Files)

### Purpose
Define the HTML structure and layout for each page.

### Template Files

#### `base.html`
**Purpose**: Base template with common elements (navbar, footer).

**What it contains**:
- Navigation bar with links
- Main content area
- Footer
- CSS and JavaScript includes

**How it's used**: Other templates extend this using `{% extends 'recommender/base.html' %}`

---

#### `home.html`
**Purpose**: Landing page with "Connect with Spotify" button.

**What it displays**:
- Welcome message
- Feature highlights (3 cards)
- "Connect with Spotify" button

**Key Elements**:
- Hero section with title
- Feature cards explaining the app
- Call-to-action button

---

#### `dashboard.html`
**Purpose**: Main dashboard after login.

**What it displays**:
- User's Spotify profile (name, picture)
- Action buttons:
  - Fetch History (AJAX call)
  - Generate Recommendations
  - View History link
  - View Recommendations link

**Key Features**:
- JavaScript for AJAX fetch history button
- Status messages for fetch operations
- Responsive card layout

---

#### `recommendations.html`
**Purpose**: Displays generated recommendations.

**What it displays**:
- Grid of recommendation cards
- Each card shows:
  - Album cover art
  - Track name, artist, album
  - Preview audio player (if available)
  - "Open in Spotify" button

**Key Features**:
- Responsive grid layout
- Empty state if no recommendations
- Audio preview players

---

#### `listening_history.html`
**Purpose**: Displays user's listening history.

**What it displays**:
- List of recently played tracks
- Each item shows:
  - Album cover art
  - Track name, artist, album
  - When it was played
  - "Open in Spotify" button

**Key Features**:
- Ordered by most recent first
- Shows last 100 entries
- Empty state if no history

---

#### `error.html`
**Purpose**: Displays error messages.

**What it displays**:
- Error icon
- Error message
- Link back to home

---

## 🎨 Styling (style.css)

### Purpose
Defines all visual styling for the application.

### Key Features

#### Color Scheme
- **Primary Color**: Spotify green (`#1DB954`)
- **Dark Background**: Dark theme (`#121212`, `#181818`)
- **Text Colors**: White, light gray, muted gray

#### Components Styled
- Navigation bar (sticky, dark theme)
- Buttons (primary, secondary, hover effects)
- Cards (glassmorphism effect with backdrop blur)
- Forms (status messages, loading states)
- Responsive design (mobile-friendly)

#### Design Patterns
- **Glassmorphism**: Translucent cards with backdrop blur
- **Gradient backgrounds**: Purple gradient on body
- **Hover effects**: Buttons lift and glow on hover
- **Responsive grid**: Adapts to screen size

---

## ⚙️ Configuration Files

### settings.py
**Purpose**: Django project configuration.

**Key Settings Added**:
- `INSTALLED_APPS`: Added `'recommender'` app
- `TEMPLATES`: Added template directory path
- `STATICFILES_DIRS`: Added static files directory

**What This Does**:
- Registers the recommender app
- Tells Django where to find templates
- Tells Django where to find static files (CSS)

---

### admin.py
**Purpose**: Configures Django admin interface.

**What It Does**:
- Registers all models with admin interface
- Customizes list display (which columns shown)
- Adds filters and search functionality
- Adds date hierarchy navigation

**Access**: Visit `/admin/` after creating superuser

---

## 🔄 Application Flow

### Complete User Journey

1. **User visits home page** (`/`)
   - Sees landing page with features
   - Clicks "Connect with Spotify"

2. **User initiates login** (`/login/`)
   - Redirected to Spotify authorization page
   - User authorizes app

3. **Spotify redirects back** (`/callback/`)
   - Spotify sends authorization code
   - We exchange code for tokens
   - We create/update user account
   - We store tokens and profile
   - User logged into Django
   - Redirected to dashboard

4. **User on dashboard** (`/dashboard/`)
   - Sees profile info
   - Can fetch listening history
   - Can generate recommendations

5. **User fetches history** (`/fetch-history/`)
   - AJAX call to fetch history
   - Last 50 tracks fetched from Spotify
   - Stored in database
   - Status message displayed

6. **User generates recommendations** (`/generate-recommendations/`)
   - Algorithm analyzes top tracks
   - Generates 20 recommendations
   - Stored in database
   - Redirected to recommendations page

7. **User views recommendations** (`/recommendations/`)
   - Sees all generated recommendations
   - Can play previews
   - Can open in Spotify

---

## 🔑 Key Concepts

### OAuth Flow
**What it is**: Secure way to let users log in with Spotify without sharing passwords.

**How it works**:
1. User clicks "Connect with Spotify"
2. Redirected to Spotify login page
3. User authorizes app
4. Spotify redirects back with authorization code
5. We exchange code for access token
6. We use token to make API calls

### Token Management
**Access Tokens**: Expire after 1 hour, used for API calls.
**Refresh Tokens**: Don't expire, used to get new access tokens.

**Auto-refresh logic**:
- Before each API call, check if token expired
- If expired, use refresh token to get new access token
- Update stored token in database

### Recommendation Algorithm
**How it works**:
1. Get user's top tracks (most played)
2. Analyze audio features (danceability, energy, valence, tempo)
3. Calculate average features (what they like)
4. Ask Spotify to find similar tracks with matching features
5. Store recommendations with confidence scores

### Database Relationships
- **One-to-One**: User → SpotifyToken, User → SpotifyProfile
- **Many-to-One**: ListeningHistory → User, ListeningHistory → Track
- **Many-to-One**: Recommendation → User, Recommendation → Track

**Why this structure**:
- One user has one token and one profile
- One user has many listening history entries
- One track can be in many listening history entries
- One user has many recommendations

---

## 📦 Dependencies

### requirements.txt
Lists all Python packages needed:

- **Django 4.2.7**: Web framework
- **spotipy 2.23.0**: Spotify API library
- **requests 2.31.0**: HTTP library (used by spotipy)

---

## 🚀 How to Use This Information

### When Adding Features
1. **New model?** → Add to `models.py`, create migration
2. **New page?** → Add view to `views.py`, add URL to `urls.py`, create template
3. **New API call?** → Use `get_user_spotify_client()` helper function

### When Debugging
1. **Token errors?** → Check `SpotifyToken` model, `get_user_spotify_client()` function
2. **Recommendations not working?** → Check `generate_recommendations()` function
3. **History not fetching?** → Check `fetch_listening_history()` function

### When Understanding Flow
1. Start with `urls.py` to see all routes
2. Follow URL to `views.py` to see what happens
3. Check `models.py` to see what data is stored
4. Check templates to see what's displayed

---

## 📝 Summary

This project creates a complete web application that:
1. Authenticates users with Spotify OAuth
2. Fetches and stores listening history
3. Analyzes music preferences
4. Generates personalized recommendations
5. Displays everything in a beautiful UI

Each component has a specific purpose and works together to create the full experience. The code is heavily commented to help you understand what each part does and why it exists.



