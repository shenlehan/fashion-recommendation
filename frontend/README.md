# Fashion Recommendation System - Frontend

React-based frontend for the Fashion Recommendation System.

## Features

1. **User Authentication** - Login and Register pages
2. **My Wardrobe** - View, upload, and manage clothing items
3. **Get Recommendations** - AI-powered outfit suggestions based on weather and wardrobe
4. **Customizable Recommendations** - Regenerate suggestions with user preferences

## Tech Stack

- **React 19** - UI framework
- **React Router** - Client-side routing
- **Axios** - HTTP client for API communication
- **Vite** - Build tool and dev server

## Getting Started

### Prerequisites

- Node.js 16+ installed
- Backend server running on `http://localhost:8000`

### Installation

```bash
npm install
```

### Development

```bash
npm run dev
```

The app will be available at `http://localhost:3000`

### Build for Production

```bash
npm run build
```

## Project Structure

```
src/
├── pages/           # Page components
│   ├── Login.jsx
│   ├── Register.jsx
│   ├── Wardrobe.jsx
│   ├── Recommendations.jsx
│   ├── Auth.css
│   ├── Wardrobe.css
│   └── Recommendations.css
├── services/        # API service layer
│   └── api.js
├── App.jsx          # Main app component with routing
├── App.css          # App-level styles
├── main.jsx         # Entry point
└── index.css        # Global styles
```

## API Integration

The frontend connects to the backend API at `http://localhost:8000/api/v1`. API calls are handled through the `services/api.js` module.

### Available API Functions

- `registerUser(userData)` - Register new user
- `loginUser(username, password)` - Login user
- `getUserProfile(userId)` - Get user profile
- `uploadClothingItem(userId, formData)` - Upload clothing image
- `getUserWardrobe(userId)` - Get user's wardrobe items
- `deleteClothingItem(itemId)` - Delete wardrobe item
- `getOutfitRecommendations(userId, preferences)` - Get outfit recommendations

## User Flow

1. **Register/Login** - Create account or login with existing credentials
2. **Add Items** - Upload clothing items with images to build your wardrobe
3. **View Wardrobe** - Browse all your clothing items with categories, colors, and seasons
4. **Get Recommendations** - Receive personalized outfit suggestions
5. **Customize** - Filter recommendations by occasion, style, and color preferences
6. **Regenerate** - Get new suggestions based on your feedback

## Features in Detail

### User Authentication
- Simple username/password authentication
- User data persisted in localStorage
- Protected routes (redirect to login if not authenticated)

### Wardrobe Management
- Upload clothing images
- Automatic image analysis (via backend ML model)
- View items in a responsive grid
- Delete unwanted items

### Recommendations
- Weather-aware suggestions based on user's city
- Outfit combinations from wardrobe items
- Missing item analysis
- Customizable filters:
  - Occasion (casual, business, formal, sport, party)
  - Style (classic, trendy, minimalist, bohemian, street)
  - Color preferences
- One-click regeneration

## Notes

- Authentication is basic (no JWT tokens yet)
- Images are served from backend at `http://localhost:8000/uploads/`
- User sessions persist via localStorage
- Responsive design works on mobile and desktop

## Future Enhancements

- [ ] JWT-based authentication
- [ ] Profile page to update user info
- [ ] Outfit favorites/save feature
- [ ] Social sharing of outfits
- [ ] Advanced filtering and search
- [ ] Outfit history/calendar
